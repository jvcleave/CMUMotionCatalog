"""Merge the completed action reviews into the offline catalog index."""

import argparse
import json

from validate import ROOT, read, validate


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def publish(version, check):
    categories, reviews = validate(require_complete=True, require_catalog_complete=True)
    catalog = read("catalog/catalog.json")
    existing_overrides = read("catalog/annotations.json")
    overrides = {}
    catalog["catalogVersion"] = version
    catalog["categories"] = [
        {key: category[key] for key in ("id", "name", "definition")}
        for category in categories.values()
    ]
    takes = catalog.pop("takes")
    for take in takes:
        take_id = take["takeID"]
        review = reviews[take_id]
        primary = review["primaryCategory"]
        label = {
            "title": review["title"],
            "category": categories[primary]["name"],
            "tags": list(dict.fromkeys(tag.strip() for tag in review["searchTags"])),
        }
        take.update(label, labelOrigin="reviewed", primaryCategory=primary,
                    actionDescription=review["actionDescription"])
        for field in ("secondaryCategories", "segments", "firstUsableFrame", "reviewNote"):
            if field in review:
                take[field] = review[field]
            else:
                take.pop(field, None)
        poster_frame = existing_overrides.get(take_id, {}).get("posterFrame")
        if poster_frame is not None:
            label["posterFrame"] = poster_frame
        overrides[take_id] = label

    # Keep each take on one line for readable diffs and a compact offline index.
    catalog_lines = [f"  {compact(key)}:{compact(value)}," for key, value in catalog.items()]
    take_lines = ",\n".join(f"    {compact(take)}" for take in takes)
    index_text = "\n".join(["{", *catalog_lines, '  "takes":[', take_lines, "  ]", "}\n"])
    override_lines = ",\n".join(f"  {compact(key)}:{compact(value)}" for key, value in overrides.items())
    override_text = "{\n" + override_lines + "\n}\n"
    for filename, content in (("catalog.json", index_text), ("annotations.json", override_text)):
        path = ROOT / "catalog" / filename
        data = content.encode("utf-8")
        if check:
            if path.read_bytes() != data:
                raise ValueError(f"{filename} differs from the published review metadata.")
        else:
            path.write_bytes(data)
    print(f"Catalog {version}: {len(takes)} takes, {len(categories)} categories, "
          f"{len(index_text.encode('utf-8')):,} index bytes.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="Catalog version, such as 1.1.0.")
    parser.add_argument("--check", action="store_true", help="Verify generated files without modifying them.")
    args = parser.parse_args()
    publish(args.version, args.check)
