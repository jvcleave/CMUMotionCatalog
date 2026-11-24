"""Validate the CMU pilot roster, draft categories, and take annotations."""

import argparse
from collections import Counter
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def read(relative):
    return json.loads((ROOT / relative).read_bytes())


def index(rows, key):
    result = {}
    for row in rows:
        identifier = row[key]
        if identifier in result:
            raise ValueError(f"Duplicate {key} {identifier}.")
        result[identifier] = row
    return result


def validate(require_complete, proposed_checkpoint=None, require_catalog_complete=False):
    source = index(read("catalog/source-catalog.json")["takes"], "trialID")
    display = index(read("catalog/catalog.json")["takes"], "takeID")
    batches = index(read("review/pilot.json")["batches"], "id")
    roster = index([take for batch in batches.values() for take in batch["takes"]], "takeID")
    index(roster.values(), "sourceUUID")
    if len(roster) != 40:
        raise ValueError(f"Expected 40 pilot takes, found {len(roster)}.")
    for take_id, take in roster.items():
        if take["sourceUUID"] != source[take_id]["id"] or take["sourceUUID"] != display[take_id]["sourceUUID"]:
            raise ValueError(f"Source UUID differs from the catalog for {take_id}.")
    vacation_subjects = [
        take_id.split("_")[0] for take_id in roster
        if (display[take_id]["sourceDescription"] or "").lower() == "alaskan vacation"
    ]
    if sorted(vacation_subjects) != [str(subject) for subject in range(27, 33)]:
        raise ValueError("Select one Alaskan vacation take per subject from 27 through 32.")

    category_data = read("review/categories.json")
    categories = index(category_data["categories"], "id")
    index(categories.values(), "name")
    for category in categories.values():
        if not category["name"].strip() or not category["definition"].strip():
            raise ValueError(f"Missing category name or definition for {category['id']}.")
    pilot = index(read("review/pilot-annotations.json")["takes"], "takeID")
    if not pilot.keys() <= roster.keys():
        raise ValueError("The pilot annotations must stay within the pilot roster.")
    subject_data = {
        path.stem: json.loads(path.read_bytes())
        for path in sorted((ROOT / "review/subjects").glob("*.json"))
    }
    if proposed_checkpoint is not None:
        subject_data[proposed_checkpoint["subject"]] = proposed_checkpoint
    checkpoints = []
    for subject, data in subject_data.items():
        if data["subject"] != subject or not data["takes"]:
            raise ValueError(f"Invalid subject checkpoint {subject}.json.")
        if any(take["takeID"].split("_")[0] != subject for take in data["takes"]):
            raise ValueError(f"A take appears in the wrong subject checkpoint {subject}.json.")
        checkpoints.extend(data["takes"])
    annotations = index([*pilot.values(), *checkpoints], "takeID")
    index(annotations.values(), "sourceUUID")
    timing_issues = index(read("review/source-timing-issues.json")["takes"], "takeID")
    for take_id, issue in timing_issues.items():
        frame = issue["firstDifferentFrame"]
        if (issue["sourceUUID"] != source[take_id]["id"]
                or type(frame) is not int or not 1 < frame <= source[take_id]["frameCount"]
                or frame != issue["leadingZeroChannelFrames"] + 1):
            raise ValueError(f"{take_id} has inconsistent source timing audit metadata.")
    flagged = set()
    for take_id, take in annotations.items():
        original = source[take_id]
        expected = {
            "sourceUUID": original["id"],
            "sourceDescription": display[take_id]["sourceDescription"],
            "sourceSHA256": original["sha256"],
            "frameCount": original["frameCount"],
            "frameInterval": original["frameInterval"],
        }
        for field, value in expected.items():
            if take[field] != value:
                raise ValueError(f"{take_id} has mismatched {field}.")
        if not take["title"].strip() or not take["actionDescription"].strip():
            raise ValueError(f"{take_id} is missing a title or action description.")
        if take["primaryCategory"] not in categories:
            raise ValueError(f"{take_id} has an unknown primary category.")
        usable_frame = take.get("firstUsableFrame", 1)
        if type(usable_frame) is not int or not 1 <= usable_frame <= original["frameCount"]:
            raise ValueError(f"{take_id} has an invalid first usable source frame.")
        if take_id in timing_issues and usable_frame != timing_issues[take_id]["firstDifferentFrame"]:
            raise ValueError(f"{take_id} is missing the audited first usable source frame.")
        if any(not tag.strip() for tag in take["searchTags"]) or len(set(take["searchTags"])) != len(take["searchTags"]):
            raise ValueError(f"{take_id} has empty or repeated tags.")
        status = take["reviewStatus"]
        if status == "needs-review" and take.get("reviewNote", "").strip():
            flagged.add(take_id)
        elif status != "described":
            raise ValueError(f"{take_id} needs a recognized status and a note for follow-up.")
        previous_end = 0
        for segment in take.get("segments", []):
            start, end = segment["startFrame"], segment["endFrame"]
            if (type(start) is not int or type(end) is not int
                    or not previous_end < start <= end <= original["frameCount"]
                    or not segment["title"].strip()):
                raise ValueError(f"{take_id} has an invalid or overlapping source-frame range.")
            previous_end = end

    pilot_counts = Counter(take["primaryCategory"] for take in pilot.values())
    missing_categories = set(categories) - pilot_counts.keys()
    if category_data["status"] == "pilot-reviewed":
        for category_id, category in categories.items():
            examples = category["exampleTakes"]
            if (category["pilotCount"] != pilot_counts[category_id] or not examples
                    or len(set(examples)) != len(examples)
                    or any(pilot.get(take_id, {}).get("primaryCategory") != category_id for take_id in examples)):
                raise ValueError(f"Incorrect pilot count or example takes for {category_id}.")
    pilot_flags = flagged.intersection(pilot)
    if require_complete and (roster.keys() != pilot.keys() or pilot_flags or missing_categories):
        raise ValueError("A complete pilot needs all takes reviewed and every category represented.")
    print(f"{len(pilot)}/{len(roster)} pilot takes annotated, {len(pilot_flags)} flagged, "
          f"{len(categories) - len(missing_categories)}/{len(categories)} categories represented.")
    if checkpoints:
        print(f"{len(annotations)}/{len(source)} catalog takes annotated, "
              f"{len(flagged)} flagged across pilot and subject checkpoints.")
    if require_catalog_complete and (annotations.keys() != source.keys() or flagged):
        raise ValueError(
            f"Catalog review has {len(source.keys() - annotations.keys())} pending takes "
            f"and {len(flagged)} flagged annotations."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--complete", action="store_true", help="Require pilot coverage and no flagged pilot takes.")
    parser.add_argument("--catalog-complete", action="store_true", help="Require coverage and no flags across the catalog.")
    args = parser.parse_args()
    validate(args.complete or args.catalog_complete, require_catalog_complete=args.catalog_complete)
