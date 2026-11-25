"""Build the static catalog browser and copy its preview assets."""

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "review"))
from validate import index, read, validate


def build(output):
    validate(require_complete=True)
    reviews = read("review/pilot-annotations.json")["takes"]
    for checkpoint in sorted((ROOT / "review/subjects").glob("*.json")):
        reviews.extend(read(checkpoint.relative_to(ROOT))["takes"])
    by_id = index(reviews, "takeID")
    catalog = read("catalog/catalog.json")["takes"]
    if by_id.keys() != {take["takeID"] for take in catalog}:
        raise ValueError("The Pages catalog requires an annotation for every take.")

    output.mkdir(parents=True, exist_ok=True)
    for filename in ("index.html", "catalog.css", "catalog.js"):
        shutil.copyfile(ROOT / "site" / filename, output / filename)

    takes = []
    for take in catalog:
        review = by_id[take["takeID"]]
        previews = {}
        for field in ("thumbnail", "animation"):
            relative = Path(take["packID"]) / take[field]["path"]
            destination = output / "media" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / "catalog" / relative, destination)
            previews[field] = (Path("media") / relative).as_posix()
        takes.append({
            "id": take["takeID"],
            "title": review["title"],
            "description": review["actionDescription"],
            "original": review["sourceDescription"],
            "category": review["primaryCategory"],
            "tags": review.get("searchTags", []),
            "duration": (review["frameCount"] - 1) * review["frameInterval"],
            "needsReview": review["reviewStatus"] == "needs-review",
            **previews,
        })

    counts = Counter(take["category"] for take in takes)
    categories = [
        {key: category[key] for key in ("id", "name", "definition")}
        | {"count": counts[category["id"]]}
        for category in read("review/categories.json")["categories"]
    ]
    (output / "catalog.json").write_text(
        json.dumps({"categories": categories, "takes": takes}, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Destination for the static website")
    build(parser.parse_args().output)
