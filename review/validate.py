"""Validate the CMU pilot roster, draft categories, and take annotations."""

import argparse
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


def validate(require_complete):
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

    categories = index(read("review/categories.json")["categories"], "id")
    index(categories.values(), "name")
    for category in categories.values():
        if not category["name"].strip() or not category["definition"].strip():
            raise ValueError(f"Missing category name or definition for {category['id']}.")
    annotations = index(read("review/pilot-annotations.json")["takes"], "takeID")
    index(annotations.values(), "sourceUUID")
    needs_review = 0
    for take_id, take in annotations.items():
        if take_id not in roster:
            raise ValueError(f"Annotation {take_id} is outside the pilot.")
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
        if any(not tag.strip() for tag in take["searchTags"]) or len(set(take["searchTags"])) != len(take["searchTags"]):
            raise ValueError(f"{take_id} has empty or repeated tags.")
        status = take["reviewStatus"]
        if status == "needs-review" and take.get("reviewNote", "").strip():
            needs_review += 1
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

    missing_categories = set(categories) - {take["primaryCategory"] for take in annotations.values()}
    if require_complete and (roster.keys() != annotations.keys() or needs_review or missing_categories):
        raise ValueError("A complete pilot needs all takes reviewed and every category represented.")
    print(f"{len(annotations)}/{len(roster)} pilot takes annotated, {needs_review} flagged, "
          f"{len(categories) - len(missing_categories)}/{len(categories)} categories represented.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--complete", action="store_true", help="Require final coverage and no flagged takes.")
    args = parser.parse_args()
    validate(args.complete)
