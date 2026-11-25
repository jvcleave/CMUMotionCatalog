# CMU Motion Catalog

Search and preview all 2,548 takes in the cgspeed 2010 MotionBuilder-friendly
BVH conversion of the CMU Graphics Lab Motion Capture Database. Each take
includes the original BVH, a reviewed title and action description, and still
and animated previews on MessCharacterCreator's Default Human. The catalog
groups motions into 16 categories.

## Catalog

[Download the complete catalog ZIP](https://github.com/jvcleave/CMUMotionCatalog/releases/download/v1.1.0/cmu-motion-catalog-v1.1.0.zip).
The ZIP extracts to a `catalog/` folder with all original BVHs, both previews
for every take, and the JSON metadata. The SHA-256 is in the [release notes](https://github.com/jvcleave/CMUMotionCatalog/releases/tag/v1.1.0).

[Browse the catalog](catalog/) to find individual files or suggest a label
correction.

## Credits and source terms

The data used in this project was obtained from mocap.cs.cmu.edu. The database
was created with funding from NSF EIA-0196217.

The source captures come from the [CMU Graphics Lab Motion Capture Database](https://mocap.cs.cmu.edu/).
The MotionBuilder-friendly BVH conversion is by Bruce Hahne.
See the [CMU data terms](https://mocap.cs.cmu.edu/) and
[cgspeed conversion notes](https://sites.google.com/a/cgspeed.com/cgspeed/motion-capture/the-motionbuilder-friendly-bvh-conversion-release-of-cmus-motion-capture-database/readme-file-for-the-bvh-conversion-release).

## Catalog browser

The GitHub Pages browser uses the published catalog index and its still and
animated previews. Use **Motion filter** to find Partner Work,
Turns in Place, or Stylized Walks across categories. Category totals count the
takes returned by that filter, including any take listed in two categories.
Type or select a **Tag** to narrow the results alongside the other filters.
Choose **3D Preview** on a card or in the take details to start playback. You
can orbit the animated character, switch to the source skeleton, or scrub the
motion. The viewer fetches the original BVH on demand from a pinned GitHub
revision.
The site artifact includes preview images and search metadata. The full BVH
download remains available through Releases.

For a local preview, build into a temporary directory and serve it over HTTP.

```sh
PAGES_PREVIEW="$(mktemp -d)"
PYTHONDONTWRITEBYTECODE=1 python3 site/build.py "$PAGES_PREVIEW"
python3 -m http.server 8000 --bind 127.0.0.1 --directory "$PAGES_PREVIEW"
```

Open `http://127.0.0.1:8000/`. To publish, set the repository’s Pages source to
**GitHub Actions**. The Pages workflow deploys from `main`.
