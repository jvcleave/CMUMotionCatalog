"""Build the CMU label catalog and stage sparse, exact-frame BVHs for native rendering."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.request import urlopen
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = (
    "https://github.com/jvcleave/MessCharacterCreatorApp/releases/download/cmu-bvh-2010-v1/catalog.json"
)
SOURCE_SHA256 = "d3840484688ab07e18f29dd4c5633f38973cb370bce9421c93b951c7555ec4eb"
RELEASE_TAG = "v1.0.0"
PACK_URL = f"https://github.com/jvcleave/CMUMotionCatalog/releases/download/{RELEASE_TAG}/"

CATEGORY_RULES = (
    ("Calibration", r"\b(t.pose|calibration|range of motion)\b"),
    ("Dance", r"\b(dance|ballet|pirouette|salsa|waltz|arabesque|glissade|choreograph\w*)\b"),
    ("Climbing", r"\b(climb\w*|hang from|dangle|monkey bars)\b"),
    ("Acrobatics", r"\b(acrobat\w*|cartwheel\w*|somersault\w*|flip\w*|gymnast\w*)\b"),
    ("Sports", r"\b(basketball|soccer|swim\w*|breast stroke|hockey|golf|tennis|baseball|boxing|tread water|volleyball|football|rugby|sword\w*|punch\w*|fenc\w*|martial arts)\b"),
    ("Jumping", r"\b(jump\w*|hop\w*|leap\w*|skip\w*)\b"),
    ("Running", r"\b(run\w*|jog\w*|sprint\w*)\b"),
    ("Gestures", r"\b(gestur\w*|wave\w*|shrug\w*|bow\w*|high five|signal\w*|point\w*|story|conversation|curtsey|curtsy|laugh\w*|conduct\w*)\b"),
    ("Turning", r"\b(turn\w*|spin\w*|twirl\w*|pivot\w*)\b|^\d{2,3}$"),
    ("Walking", r"\b(walk\w*|stair\w*|side step\w*|sidestep\w*|march\w*|limp\w*|creep\w*|sneak\w*|stroll\w*|navigat\w*)\b"),
    ("Exercise", r"\b(stretch\w*|yoga|push[ -]?up\w*|sit[ -]?up\w*|exercis\w*)\b"),
    ("Everyday Actions", r"\b(sit\w*|stand\w*|bend\w*|reach\w*|pick\w*|get up|carry\w*|throw\w*|sweep\w*|wash\w*|wip\w*|mop\w*|open\w*|drink\w*|wait\w*|idle|lay down|lie down|crouch\w*|roll\w*|crawl\w*)\b"),
)

TAG_RULES = (
    ("forward", r"\bforwards?\b"),
    ("backward", r"\bbackwards?\b"),
    ("lateral", r"\b(sideways?|side step|sidestep|lateral)\b"),
    ("left", r"\bleft\b"),
    ("right", r"\bright\b"),
    ("in place", r"\b(in place|stationary)\b"),
    ("slow", r"\b(slow|slowly)\b"),
    ("quick", r"\b(fast|quick|quickly)\b"),
    ("repeated", r"\b(repeat\w*|multiple)\b"),
    ("stairs", r"\b(stairs?|staircase)\b"),
    ("uneven terrain", r"\buneven terrain\b"),
    ("figure eight", r"\bfigure (8|eight)\b"),
    ("treadmill", r"\btreadmill\b"),
)


def load_source(path):
    if path is None:
        with urlopen(SOURCE_URL, timeout=30) as response:
            raw = response.read()
    else:
        raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("Source catalog SHA-256 differs from the pinned release.")
    return json.loads(raw)


def sampled_frames(count):
    samples = min(10, count)
    if samples <= 1:
        return list(range(1, samples + 1))
    intervals = samples - 1
    return [1 + (index * (count - 1) + intervals // 2) // intervals for index in range(samples)]


def display_label(take_id, source_description, annotations):
    if take_id in annotations:
        return dict(annotations[take_id], labelOrigin="reviewed")
    text = " ".join((source_description or "").split())
    text = re.sub(r"([a-z])([A-Z0-9])", r"\1 \2", text)
    text = re.sub(r"([A-Z])([A-Z][a-z])", r"\1 \2", text)
    text = re.sub(r"[_/]", " ", text)
    text = " ".join(text.split()).strip(" -;,.")
    if text.lower() in {"", "unknown", "clean", "cleaned", "bad amc"} or text.lower() == f"{take_id.lower()} amc":
        return {
            "title": f"Unclassified Motion {take_id}",
            "category": "Unclassified",
            "tags": [],
            "labelOrigin": "unclassified",
        }

    search = text.lower()
    categories = [category for category, pattern in CATEGORY_RULES if re.search(pattern, search)]
    category = categories[0] if categories else "Other Motion"
    tags = [item.lower() for item in categories[1:]]
    tags.extend(tag for tag, pattern in TAG_RULES if re.search(pattern, search))
    if re.fullmatch(r"(90|180|270|360)", text):
        text = f"Turn {text}°"
    if len(text) > 72:
        reduced = text[:72].rsplit(" ", 1)[0].rstrip(" -,;:")
        text = (reduced or text[:72]) + "…"
    text = text[0].upper() + text[1:]
    return dict(title=text, category=category, tags=list(dict.fromkeys(tags)), labelOrigin="source-description")


def stage_take(archive, take, label, stage):
    take_id = take["trialID"]
    frame_count = take["frameCount"]
    raw = archive.read(take["path"])
    if len(raw) != take["byteCount"] or hashlib.sha256(raw).hexdigest() != take["sha256"]:
        raise ValueError(f"{take_id} differs from the published BVH.")
    hierarchy, motion = raw.split(b"MOTION", 1)
    frames_line, time_line, *poses = motion.strip().splitlines()
    if (int(frames_line.split(b":")[1]) != frame_count + 1
            or len(poses) != frame_count + 1
            or float(time_line.split(b":")[1]) != take["frameInterval"]):
        raise ValueError(f"{take_id} differs from the published BVH timing.")

    if label["labelOrigin"] == "unclassified":
        label.update(motion_profile(poses, take_id))

    animation = sampled_frames(frame_count)
    poster = label.get("posterFrame")
    if poster is None and label["category"] == "Jumping":
        # Use root height to find the apex on a dense grid of candidate samples.
        stride = max(1, frame_count // 120)
        poster = max(range(1, frame_count + 1, stride), key=lambda index: float(poses[index].split(None, 2)[1]))
    if poster is None:
        poster = (frame_count + 1) // 2
    if not 1 <= poster <= frame_count:
        raise ValueError(f"{take_id} selects a poster outside the captured poses.")
    kept = sorted(set(animation + [poster]))
    header = f"MOTION\nFrames: {len(kept) + 1}\nFrame Time: {take['frameInterval']}\n".encode("ascii")
    sparse = hierarchy + header + b"\n".join(poses[index] for index in [0] + kept) + b"\n"
    (stage / f"{take_id}.bvh").write_bytes(sparse)
    return dict(takeID=take_id, capturedFrames=kept, posterFrame=poster, animationFrames=animation)


def motion_profile(poses, take_id):
    # The archive includes takes labeled only "clean" or "unknown". Report
    # visible root travel and turning in these cases without guessing the action.
    count = len(poses) - 1
    points = [tuple(map(float, poses[i].split(None, 5)[:5])) for i in range(1, count + 1, max(1, count // 120))]
    first_x, _, first_z, _, previous_yaw = points[0]
    leg_height = max(1, abs(float(poses[0].split(None, 2)[1])))
    travel = max(math.hypot(point[0] - first_x, point[2] - first_z) for point in points)
    total_yaw = 0
    max_yaw = 0
    for _, _, _, _, yaw in points:
        total_yaw += (yaw - previous_yaw + 180) % 360 - 180
        max_yaw = max(max_yaw, abs(total_yaw))
        previous_yaw = yaw
    travels = travel >= 1.3 * leg_height
    turns = max_yaw >= 65
    title = "Traveling Motion" if travels else "Motion in Place"
    tags = ["traveling" if travels else "in place"]
    if turns:
        title += " with Turns"
        tags.append("turns")
    return dict(title=f"{title} {take_id}", tags=tags, labelOrigin="motion-profile")


def build(source, archives, stage):
    annotations = json.loads((ROOT / "annotations.json").read_bytes())
    take_ids = {take["trialID"] for take in source["takes"]}
    if not annotations.keys() <= take_ids:
        raise ValueError("An annotation names a take missing from the published index.")
    staged = []
    catalog = []
    media_packs = []
    stage.mkdir(parents=True, exist_ok=True)
    for pack in source["packs"]:
        pack_id = pack["id"]
        asset = f"{pack_id}-previews.zip"
        media_packs.append(dict(id=pack_id, url=PACK_URL + asset, takeCount=pack["takeCount"]))
        with ZipFile(archives / pack["filename"]) as archive:
            index = archive.read("cmu-mocap-index-text.txt").decode("utf-8-sig")
            descriptions = dict(re.findall(r"^([0-9]+_[0-9]+)[ \t]+([^\r\n]+)", index, re.M))
            for take in source["takes"]:
                if take["packID"] != pack_id:
                    continue
                take_id = take["trialID"]
                description = descriptions.get(take_id, "").strip() or None
                label = display_label(take_id, description, annotations)
                render = stage_take(archive, take, label, stage)
                staged.append(render)
                label.pop("posterFrame", None)
                catalog.append(dict(
                    takeID=take_id,
                    sourceUUID=take["id"],
                    subject=take_id.split("_")[0],
                    packID=pack_id,
                    **label,
                    sourceDescription=description,
                    frameCount=take["frameCount"],
                    frameInterval=take["frameInterval"],
                    thumbnail=dict(path=f"stills/{take_id}.png", frame=render["posterFrame"]),
                    animation=dict(path=f"animations/{take_id}.png", frames=render["animationFrames"]),
                ))
    by_id = lambda take: tuple(map(int, take["takeID"].split("_")))
    catalog.sort(key=by_id)
    staged.sort(key=by_id)
    preview = dict(
        schemaVersion=1,
        catalogVersion=RELEASE_TAG.removeprefix("v"),
        source=dict(
            revision=source["revision"],
            catalogURL=SOURCE_URL,
            catalogSHA256=SOURCE_SHA256,
            dataset=source["dataset"],
            datasetURL="https://mocap.cs.cmu.edu/",
            conversionURL=source["sourceURL"],
            acknowledgment=source["acknowledgment"],
        ),
        media=dict(renderer="MessCharacterCreator Default Human", thumbnailSize=384, animationSize=256, animationFrameDelayMS=150),
        previewPacks=media_packs,
        takes=catalog,
    )
    return preview, staged


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", type=Path, help="Directory with the original CMU ZIPs.")
    parser.add_argument("stage", type=Path, help="Temporary output for sparse BVHs and render.json.")
    parser.add_argument("--source-catalog", type=Path, help="Local copy of the pinned public index.")
    args = parser.parse_args()
    catalog, staged = build(load_source(args.source_catalog), args.archives, args.stage)
    write_json(args.stage / "render.json", staged)
    write_json(args.stage / "catalog.json", catalog)
    print(f"Staged {len(staged)} verified CMU takes.")


if __name__ == "__main__":
    main()
