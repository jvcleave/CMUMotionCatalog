"""List pending take IDs and exact-BVH review references by subject."""

import argparse
from collections import defaultdict
import json

from validate import ROOT, index, read


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("subjects", nargs="*", help="Optional two- or three-digit subject IDs.")
    parser.add_argument("--ids", action="store_true", help="Print only pending take IDs, one per line.")
    args = parser.parse_args()

    source = index(read("catalog/source-catalog.json")["takes"], "trialID")
    original = index(read("catalog/catalog.json")["takes"], "takeID")
    rows = read("review/pilot-annotations.json")["takes"]
    for path in sorted((ROOT / "review/subjects").glob("*.json")):
        rows.extend(json.loads(path.read_bytes())["takes"])
    completed = index(rows, "takeID")
    subjects = {take_id.split("_")[0] for take_id in source}
    unknown = set(args.subjects) - subjects
    if unknown:
        parser.error(f"Unknown subjects: {', '.join(sorted(unknown))}.")

    by_digest = defaultdict(list)
    for take in rows:
        if take["reviewStatus"] == "described":
            by_digest[take["sourceSHA256"]].append(take)
    for take_id in sorted(source, key=lambda item: tuple(map(int, item.split("_")))):
        if args.subjects and take_id.split("_")[0] not in args.subjects:
            continue
        if take_id in completed and completed[take_id]["reviewStatus"] == "described":
            continue
        if args.ids:
            print(take_id)
            continue
        exact_bvh = [
            match for match in by_digest[source[take_id]["sha256"]]
            if match["takeID"] != take_id
        ]
        if exact_bvh:
            same_context = [
                match["takeID"] for match in exact_bvh
                if match["sourceDescription"] == original[take_id]["sourceDescription"]
            ]
            refs = same_context or [match["takeID"] for match in exact_bvh]
            suffix = "same source description" if same_context else "check source context"
            print(f"{take_id}\tSame BVH as {', '.join(refs)} ({suffix})")
        elif take_id in completed:
            print(f"{take_id}\t{completed[take_id]['reviewNote']}")
        else:
            print(take_id)


if __name__ == "__main__":
    main()
