"""Record a checked subject batch with source identity from the catalog."""

import argparse
import json
import os
from pathlib import Path
import re
import tempfile

from validate import ROOT, index, read, validate


REVIEW_FIELDS = ("title", "actionDescription", "primaryCategory", "searchTags")


def checkpoint(subject, draft):
    source = index(read("catalog/source-catalog.json")["takes"], "trialID")
    display = index(read("catalog/catalog.json")["takes"], "takeID")
    rows = index(draft["takes"], "takeID")
    if not rows:
        raise ValueError("Expected at least one take.")
    path = ROOT / "review" / "subjects" / f"{subject}.json"
    previous = json.loads(path.read_bytes())["takes"] if path.is_file() else []
    takes = index(previous, "takeID")
    for take_id, row in rows.items():
        original = source[take_id]
        take = dict(
            takeID=take_id,
            sourceUUID=original["id"],
            sourceDescription=display[take_id]["sourceDescription"],
            sourceSHA256=original["sha256"],
            frameCount=original["frameCount"],
            frameInterval=original["frameInterval"],
        )
        for field in REVIEW_FIELDS:
            take[field] = row[field]
        take["reviewStatus"] = row.get("reviewStatus", "described")
        for field in ("reviewNote", "firstUsableFrame", "segments", "secondaryCategories"):
            if field in row:
                take[field] = row[field]
        takes[take_id] = take

    data = dict(schemaVersion=1, subject=subject, takes=[takes[take_id] for take_id in sorted(takes)])
    validate(require_complete=True, proposed_checkpoint=data)
    path.parent.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        try:
            output.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
            output.close()
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
    print(f"Checkpointed {len(rows)} takes in {path.relative_to(ROOT)}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("subject")
    parser.add_argument("draft", type=Path, help="JSON object with a takes array of reviewed fields.")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]{2,3}", args.subject):
        parser.error("Use the catalog's two- or three-digit subject ID.")
    checkpoint(args.subject, json.loads(args.draft.read_bytes()))
