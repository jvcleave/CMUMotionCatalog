"""Package native Default Human stills and APNGs by CMU subject group."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
from zipfile import ZIP_STORED, ZipFile, ZipInfo
from zlib import crc32

from build_catalog import load_source, sampled_frames, write_json


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def chunks(data):
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("Expected a PNG signature.")
    offset = len(PNG_SIGNATURE)
    while offset + 12 <= len(data):
        length, kind = struct.unpack_from(">I4s", data, offset)
        end = offset + 8 + length
        if end + 4 > len(data):
            raise ValueError(f"Incomplete PNG chunk {kind!r}.")
        value = data[offset + 8:end]
        digest = struct.unpack_from(">I", data, end)[0]
        if crc32(kind + value) != digest:
            raise ValueError(f"Invalid PNG checksum for {kind!r}.")
        yield kind, value
        offset = end + 4
        if kind == b"IEND" and offset == len(data):
            return
    raise ValueError("Missing PNG end chunk.")


def chunk(kind, value):
    return struct.pack(">I4s", len(value), kind) + value + struct.pack(">I", crc32(kind + value))


def animation_png(inputs, size, delay):
    """Reuse the native PNG scanlines and retain even identical sampled poses."""
    first = list(chunks(inputs[0]))
    width, height, bits, color_type, _, _, _ = struct.unpack(">IIBBBBB", first[0][1])
    if (width, height) != (size, size) or bits != 8 or color_type not in {2, 6}:
        raise ValueError("The APNG inputs must share the native RGB or RGBA format.")

    output = bytearray(PNG_SIGNATURE)
    output += chunk(*first[0])
    for kind, value in first[1:]:
        if kind == b"IDAT":
            break
        if kind in {b"cHRM", b"cICP", b"gAMA", b"iCCP", b"pHYs", b"sBIT", b"sRGB"}:
            output += chunk(kind, value)
    output += chunk(b"acTL", struct.pack(">II", len(inputs), 0))
    sequence = 0
    for index, frame in enumerate(inputs):
        decoded = first if index == 0 else list(chunks(frame))
        if decoded[0] != first[0]:
            raise ValueError("An APNG frame has inconsistent image parameters.")
        output += chunk(b"fcTL", struct.pack(">IIIIIHHBB", sequence, width, height, 0, 0, delay, 1000, 0, 0))
        sequence += 1
        for kind, value in decoded:
            if kind != b"IDAT":
                continue
            if index == 0:
                output += chunk(kind, value)
            else:
                output += chunk(b"fdAT", struct.pack(">I", sequence) + value)
                sequence += 1
    output += chunk(b"IEND", b"")
    return bytes(output)


def validate_catalog(catalog, source):
    published = {take["trialID"]: take for take in source["takes"]}
    actual_ids = [take["takeID"] for take in catalog["takes"]]
    if len(actual_ids) != len(published) or set(actual_ids) != published.keys():
        raise ValueError("The labeled catalog and source catalog must cover the same take IDs.")
    group_counts = Counter()
    for take in catalog["takes"]:
        take_id = take["takeID"]
        original = published[take_id]
        if (
            take["sourceUUID"] != original["id"]
            or take["packID"] != original["packID"]
            or take["frameCount"] != original["frameCount"]
            or take["frameInterval"] != original["frameInterval"]
        ):
            raise ValueError(f"Source identity or timing mismatch for {take_id}.")
        original_name = " ".join(f"CMU {take_id} {take['sourceDescription'] or ''}".split())[:80].rstrip()
        if original_name != original["name"]:
            raise ValueError(f"Source description mismatch for {take_id}.")
        if not take["title"].strip() or not take["category"]:
            raise ValueError(f"Missing label for {take_id}.")
        still, animation = take["thumbnail"], take["animation"]
        if (
            not 1 <= still["frame"] <= original["frameCount"]
            or animation["frames"] != sampled_frames(original["frameCount"])
            or still["path"] != f"stills/{take_id}.png"
            or animation["path"] != f"animations/{take_id}.png"
        ):
            raise ValueError(f"Preview sampling or path mismatch for {take_id}.")
        group_counts[take["packID"]] += 1
    if group_counts != {pack["id"]: pack["takeCount"] for pack in catalog["previewPacks"]}:
        raise ValueError("The archive sizes do not cover the published take groups.")


def archive_member(archive, path, data):
    entry = ZipInfo(path)
    entry.create_system = 3
    entry.external_attr = 0o100644 << 16
    archive.writestr(entry, data, compress_type=ZIP_STORED)


def make_pack(pack, takes, media, render, output):
    path = output / pack["url"].rsplit("/", 1)[-1]
    temporary = path.with_suffix(".tmp")
    with ZipFile(temporary, "w") as archive:
        for take in takes:
            directory = render / take["takeID"]
            still = (directory / "still.png").read_bytes()
            first = list(chunks(still))[0]
            if first[0] != b"IHDR" or struct.unpack_from(">II", first[1]) != (media["thumbnailSize"],) * 2:
                raise ValueError(f"Unexpected still dimensions for {take['takeID']}.")
            inputs = [
                (directory / f"frame-{index}.png").read_bytes()
                for index in range(len(take["animation"]["frames"]))
            ]
            encoded = animation_png(inputs, media["animationSize"], media["animationFrameDelayMS"])
            archive_member(archive, take["thumbnail"]["path"], still)
            archive_member(archive, take["animation"]["path"], encoded)
    temporary.replace(path)
    return dict(pack, byteCount=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("staged_catalog", type=Path)
    parser.add_argument("render_directory", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--source-catalog", type=Path, help="Local copy of the pinned public index.")
    args = parser.parse_args()

    source = load_source(args.source_catalog)
    catalog = json.loads(args.staged_catalog.read_bytes())
    validate_catalog(catalog, source)
    output = args.output_directory
    output.mkdir(parents=True, exist_ok=True)
    catalog["media"]["defaultHumanAssetPackSHA256"] = (args.render_directory / "asset-pack.txt").read_text().strip()
    for index, pack in enumerate(catalog["previewPacks"]):
        takes = [take for take in catalog["takes"] if take["packID"] == pack["id"]]
        catalog["previewPacks"][index] = packed = make_pack(pack, takes, catalog["media"], args.render_directory, output)
        print(f"{packed['id']}  {len(takes)} takes  {packed['byteCount'] / 1024**2:.1f} MiB", flush=True)
    write_json(output / "catalog.json", catalog)
    print(f"Packaged {len(catalog['takes'])} stills and APNGs.")


if __name__ == "__main__":
    main()
