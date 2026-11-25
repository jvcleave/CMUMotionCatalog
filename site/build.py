"""Build the static catalog browser and copy its preview assets."""

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parent.parent


# This revision contains all the checksum-pinned source BVHs.
BVH_BASE = (
    "https://raw.githubusercontent.com/jvcleave/CMUMotionCatalog/"
    "91a0f97526c3e2e2baa0bc2fc78eb10dd912447e/catalog"
)
MOTION_FILTERS = {
    "partner-work": "Partner Work",
    "turns-in-place": "Turns in Place",
    "stylized-walks": "Stylized Walks",
}
PARTNER_TAGS = {"participant a", "participant b", "two people"}
PARTNER_ROLE = re.compile(r"\bparticipant [ab]\b")
IN_PLACE_TURN = re.compile(r"\b(?:turns? in place|turning in place|in-place turns?|pivot(?:s|ing)?)\b")
STYLIZED_WALK = re.compile(
    r"\b(?:limps?|limping|injured|tired|drunk(?:en)?|stagger(?:s|ing)?|"
    r"struts?|strutting|sneaks?|sneaking|march(?:es|ing)?|tiptoes?|tiptoeing|"
    r"elderly|stylized (?:walk|gait)|zombie)\b"
)


def motion_filters(take):
    tags = {tag.strip().lower() for tag in take["tags"]}
    title = take["title"].lower()
    filters = []
    if tags & PARTNER_TAGS or PARTNER_ROLE.search(title):
        filters.append("partner-work")
    if take["primaryCategory"] == "walking-turning":
        labels = (title, (take["sourceDescription"] or "").lower(), *tags)
        if any(IN_PLACE_TURN.search(label) for label in labels):
            filters.append("turns-in-place")
        if any(STYLIZED_WALK.search(label) for label in labels):
            filters.append("stylized-walks")
    return filters


def build(output):
    catalog_directory = ROOT / "catalog"
    catalog = json.loads((catalog_directory / "catalog.json").read_bytes())
    source = json.loads((catalog_directory / "source-catalog.json").read_bytes())
    calibration_frames = source["calibrationFrameCount"]

    output.mkdir(parents=True, exist_ok=True)
    site = ROOT / "site"
    assets = ("catalog.css", "catalog.js", "skeleton-viewer.js", "character-view.js", "model.glb")
    revision = sha256()
    for filename in assets:
        asset = (site / filename).read_bytes()
        revision.update(sha256(asset).digest())
        (output / filename).write_bytes(asset)
    html = (site / "index.html").read_text(encoding="utf-8")
    (output / "index.html").write_text(
        html.replace("ASSET_REVISION", revision.hexdigest()[:12])
        .replace("CATALOG_VERSION", catalog["catalogVersion"]),
        encoding="utf-8",
    )

    takes = []
    for take in catalog["takes"]:
        previews = {}
        for field in ("thumbnail", "animation"):
            relative = Path(take["packID"]) / take[field]["path"]
            destination = output / "media" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(catalog_directory / relative, destination)
            previews[field] = (Path("media") / relative).as_posix()
        takes.append({
            "id": take["takeID"],
            "title": take["title"],
            "description": take["actionDescription"],
            "original": take["sourceDescription"],
            "category": take["primaryCategory"],
            "secondaryCategories": take.get("secondaryCategories", []),
            "motionFilters": motion_filters(take),
            "tags": take["tags"],
            "duration": (take["frameCount"] - 1) * take["frameInterval"],
            "needsReview": take.get("reviewStatus") == "needs-review",
            "motion": {
                "url": f"{BVH_BASE}/{take['packID']}/{take['bvh']['path']}",
                "frameCount": take["frameCount"],
                "frameInterval": take["frameInterval"],
                "calibrationFrames": calibration_frames,
                "firstUsableFrame": take.get("firstUsableFrame", 1),
            },
            **previews,
        })

    counts = Counter(
        category for take in takes for category in (take["category"], *take["secondaryCategories"])
    )
    categories = [
        {**category, "count": counts[category["id"]]}
        for category in catalog["categories"]
    ]
    filter_counts = Counter(filter_id for take in takes for filter_id in take["motionFilters"])
    filters = [
        {"id": filter_id, "name": name, "count": filter_counts[filter_id]}
        for filter_id, name in MOTION_FILTERS.items()
    ]
    (output / "catalog.json").write_text(
        json.dumps({"categories": categories, "motionFilters": filters, "takes": takes}, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Destination for the static website")
    build(parser.parse_args().output)
