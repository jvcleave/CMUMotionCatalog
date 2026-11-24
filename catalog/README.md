# Catalog

All 2,548 takes include an original BVH, a static PNG, and a looping animated
PNG in their subject pack directory. The complete catalog takes up about
3.3 GiB after extraction.

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
- For local access, join `packID` and the file's `bvh.path`,
  `thumbnail.path`, or `animation.path` relative to this directory. For
  example, [the BVH for take 35_01](cmu-bvh-35-39/bvh/35/35_01.bvh) is at
  `cmu-bvh-35-39/bvh/35/35_01.bvh`. Each BVH entry records the size and
  SHA-256 of the original file.
- The stills are 384 × 384 pixels and the animations are 256 × 256 pixels.
  Each animation uses up to 10 evenly spaced captured poses, including the
  first and last, with a fixed 150 ms per frame. Frame numbers start at one
  and skip the cgspeed calibration pose.
- `labelOrigin` identifies visually reviewed labels, normalized upstream
  descriptions, or broad motion labels derived from recorded travel and
  turning. `sourceDescription` preserves the upstream text where available.

The [complete catalog ZIP](https://github.com/jvcleave/CMUMotionCatalog/releases/download/v1.0.1/cmu-motion-catalog-v1.0.1.zip)
uses this same directory layout. The `previewPacks` entries refer to the
earlier [v1.0.0 preview-only release](https://github.com/jvcleave/CMUMotionCatalog/releases/tag/v1.0.0).

## Contribute labels

Update the take's entry in [annotations.json](annotations.json) with a concise
title, an action category, and search tags. Use the stable take ID as the key.
Set `posterFrame` when a particular captured pose best shows the action.

## Credits and source terms

The data used in this project was obtained from mocap.cs.cmu.edu. The database
was created with funding from NSF EIA-0196217.

The source captures come from the [CMU Graphics Lab Motion Capture Database](https://mocap.cs.cmu.edu/).
The MotionBuilder-friendly BVH conversion is by Bruce Hahne. See the
[CMU data terms](https://mocap.cs.cmu.edu/), the
[cgspeed conversion notes](https://sites.google.com/a/cgspeed.com/cgspeed/motion-capture/the-motionbuilder-friendly-bvh-conversion-release-of-cmus-motion-capture-database/readme-file-for-the-bvh-conversion-release),
and the [pinned source archive release](https://github.com/jvcleave/MessCharacterCreatorApp/releases/tag/cmu-bvh-2010-v1).
