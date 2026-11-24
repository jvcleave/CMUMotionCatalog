"""Restore or verify the checked-in catalog from the versioned preview ZIPs."""

import argparse
from collections import defaultdict
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]


def restore(directory, output, check):
    index_data = (directory / "catalog.json").read_bytes()
    catalog = json.loads(index_data)
    by_pack = defaultdict(set)
    for take in catalog["takes"]:
        take_id = take["takeID"]
        if not re.fullmatch(r"[0-9]+_[0-9]+", take_id):
            raise ValueError(f"Invalid take ID {take_id!r}.")
        still = f"stills/{take_id}.png"
        animation = f"animations/{take_id}.png"
        if take["thumbnail"]["path"] != still or take["animation"]["path"] != animation:
            raise ValueError(f"Unexpected media path for {take_id}.")
        paths = by_pack[take["packID"]]
        if still in paths:
            raise ValueError(f"Duplicate take {take_id}.")
        paths.update((still, animation))

    packs = catalog["previewPacks"]
    if len(packs) != len(by_pack) or {pack["id"] for pack in packs} != by_pack.keys():
        raise ValueError("The preview packs and takes must cover the same groups.")
    for pack in packs:
        pack_id = pack["id"]
        if not re.fullmatch(r"cmu-bvh-[0-9]+-[0-9]+", pack_id):
            raise ValueError(f"Invalid preview group {pack_id!r}.")
        path = directory / f"{pack_id}-previews.zip"
        data = path.read_bytes()
        if len(data) != pack["byteCount"] or hashlib.sha256(data).hexdigest() != pack["sha256"]:
            raise ValueError(f"{path.name} differs from the catalog checksum.")

        with ZipFile(BytesIO(data)) as archive:
            paths = archive.namelist()
            expected = by_pack[pack_id]
            if len(paths) != len(expected) or set(paths) != expected or len(paths) != 2 * pack["takeCount"]:
                raise ValueError(f"{path.name} does not contain the expected preview files.")
            for member in paths:
                destination = output / pack_id / member
                image = archive.read(member)
                if check:
                    if destination.read_bytes() != image:
                        raise ValueError(f"Preview differs from the release archive at {destination}.")
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(image)

    destination = output / "catalog.json"
    if check:
        if destination.read_bytes() != index_data:
            raise ValueError("The catalog index differs from the release index.")
    else:
        destination.write_bytes(index_data)

    files = {path.relative_to(output).as_posix() for path in output.glob("cmu-bvh-*/*/*.png")}
    expected_files = {f"{pack_id}/{path}" for pack_id, paths in by_pack.items() for path in paths}
    if files != expected_files:
        raise ValueError("The local catalog contains missing or extra previews.")
    verb = "Verified" if check else "Restored"
    print(f"{verb} {len(files)} preview images for {len(catalog['takes'])} CMU takes.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release_directory", type=Path, help="Directory with catalog.json and preview ZIPs.")
    parser.add_argument("catalog_directory", type=Path, nargs="?", default=ROOT / "catalog")
    parser.add_argument("--check", action="store_true", help="Verify the local catalog without writing files.")
    args = parser.parse_args()
    restore(args.release_directory, args.catalog_directory, args.check)


if __name__ == "__main__":
    main()
