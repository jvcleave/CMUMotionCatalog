# Catalog

All 2,548 takes have a static PNG and a looping animated PNG in their subject
pack directory. The preview files in this directory total about 285 MiB.

| Walk Forward, 35_01 | Right-Hand Wave, 113_27 | Cartwheel, 121_02 |
| --- | --- | --- |
| [![Default Human walking forward](cmu-bvh-35-39/stills/35_01.png)](cmu-bvh-35-39/animations/35_01.png) | [![Default Human waving](cmu-bvh-113-128/stills/113_27.png)](cmu-bvh-113-128/animations/113_27.png) | [![Default Human performing a cartwheel](cmu-bvh-113-128/stills/121_02.png)](cmu-bvh-113-128/animations/121_02.png) |
| [Open animation](cmu-bvh-35-39/animations/35_01.png) | [Open animation](cmu-bvh-113-128/animations/113_27.png) | [Open animation](cmu-bvh-113-128/animations/121_02.png) |

## Data and files

- [catalog.json](catalog.json) lists every take. Search titles, categories,
  tags, original descriptions, or take IDs such as `35_01`. The IDs preserve
  the source zero padding. `sourceUUID` is the Creator source identity in the
  pinned original catalog.
- [source-catalog.json](source-catalog.json) is the pinned source index with
  archive and BVH paths, download URLs, source checksums, and timing.
- For local access, join `packID` and either `thumbnail.path` or
  `animation.path` relative to this directory. For example,
  `cmu-bvh-35-39/stills/35_01.png` is the still for `35_01`.
- The stills are 384 × 384 pixels and the animations are 256 × 256 pixels.
  Each animation uses up to 10 evenly spaced captured poses, including the
  first and last, with a fixed 150 ms per frame. Frame numbers start at one
  and skip the cgspeed calibration pose.
- `labelOrigin` identifies visually reviewed labels, normalized upstream
  descriptions, or broad motion labels derived from recorded travel and
  turning. `sourceDescription` preserves the upstream text where available.

For ZIP downloads, match a take's `packID` to the corresponding entry in
`previewPacks` for its URL, size, and SHA-256. Inside the ZIP, the paths
start at `stills/` and `animations/`. The [original BVH packs](https://github.com/jvcleave/MessCharacterCreatorApp/releases/tag/cmu-bvh-2010-v1)
contain the motion data and source playback timing.

## Contribute labels

Update the take's entry in [annotations.json](annotations.json) with a concise
title, an action category, and search tags. Use the stable take ID as the key.
Set `posterFrame` when a particular captured pose best shows the action.
The [regeneration tools](../tools/) rebuild the index and previews.
