# Regeneration tools

## Restore or verify published previews

Python 3.9 or later is enough to restore or verify the catalog from the
published preview ZIPs. The commands below use the GitHub CLI to download
the assets into a temporary directory.

```sh
WORK=$(mktemp -d)
gh release download v1.0.0 --repo jvcleave/CMUMotionCatalog --dir "$WORK"
python3 tools/restore_catalog.py "$WORK" --check
```

Run the same command without `--check` to extract the index and previews
into `catalog/`. Supply a second directory argument to restore to a
different location. The tool checks each ZIP's size, SHA-256, and file list
against the index.

## Regenerate from the original motion

Use the [original CMU BVH ZIPs](https://github.com/jvcleave/MessCharacterCreatorApp/releases/tag/cmu-bvh-2010-v1),
Python 3.9 or later, and macOS with a Metal-capable GPU. For rendering, you
also need a MessCharacterCreator checkout with its Default Human assets
prepared and its macOS Debug app built. The checked-in Swift batch program
links against that build through Creator's `Tools/Reference/run-app-check.sh`.

Run from the root of this repository. Set the paths to your original
archives, Creator checkout, and Creator's Xcode DerivedData directory.

```sh
WORK=$(mktemp -d)
CMU_ARCHIVES=/path/to/original-cmu-zips
CREATOR_CHECKOUT=/path/to/MessCharacterCreator
CREATOR_DERIVED_DATA=/path/to/Creator/DerivedData/Xcode

python3 tools/build_catalog.py "$CMU_ARCHIVES" "$WORK/staged" --tag v1.0.0
bash tools/render_previews.sh \
  "$CREATOR_CHECKOUT" "$CREATOR_DERIVED_DATA" "$WORK/staged" "$WORK/rendered"
python3 tools/package_previews.py \
  "$WORK/staged/catalog.json" "$WORK/rendered" "$WORK/release"
python3 tools/restore_catalog.py "$WORK/release" "$WORK/catalog"
```

- `build_catalog.py` joins the checked-in annotations to the checked-in source
  index, verifies all BVHs, and stages only the captured poses needed for
  rendering. It keeps the calibration pose in each staged BVH.
- `render_previews.sh` calls the Swift batch program, which uses Creator's
  Default Human renderer. It writes the still and the sampled frames for
  each take. Set `CMU_PREVIEW_WORKERS` to tune rendering concurrency. The
  render output must be a new directory.
- `package_previews.py` encodes the animated PNGs and builds the preview ZIPs
  plus their checksum-bearing JSON index. `restore_catalog.py` turns those
  ZIPs back into the catalog directory layout.

Use a fresh `--tag` value when preparing a new release so the output JSON
points to the new ZIP URLs. Review the generated files in `$WORK/catalog`
before copying them into the checkout's `catalog/` directory.
