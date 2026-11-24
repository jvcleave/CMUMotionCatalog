# Leading all-zero CMU frames

A full audit of the 2,548 pinned BVHs found ten takes whose captured timeline
starts with at least one frame with every motion channel set to zero. These
rows occur after the BVH calibration frame. The first differing frame can
move the root several meters and change the pose abruptly.

| Take | Leading zero frames | First differing captured frame | Source time | Horizontal root jump |
| --- | ---: | ---: | ---: | ---: |
| `07_12` | 1 | 2 | 0.0083 s | 2.2463 m |
| `09_10` | 4 | 5 | 0.0333 s | 1.6088 m |
| `104_01` | 55 | 56 | 0.4583 s | 2.3710 m |
| `104_18` | 113 | 114 | 0.9417 s | 2.3606 m |
| `104_21` | 5 | 6 | 0.0417 s | 1.6933 m |
| `104_38` | 4 | 5 | 0.0333 s | 1.6511 m |
| `138_54` | 74 | 75 | 0.6167 s | 2.8994 m |
| `20_10` | 13 | 14 | 0.1083 s | 1.1120 m |
| `28_01` | 48 | 49 | 0.4000 s | 0.0428 m |
| `79_77` | 79 | 80 | 0.6583 s | 0.2996 m |

Creator's CMU retargeter anchors horizontal root travel to captured frame 1
and skips the single documented calibration row. A change to that anchor
or to source-frame numbering would affect playback and could change trims
in saved Motion Clip Sessions.

Keep the pinned BVHs and their source timing. The recorded entries for
`07_12` and `09_10` describe the visible gait and flag the start. The other
eight are queued for subject review. Resolve how the usable start should be
presented before approving affected entries. A source-time range can expose
it while preserving the original timeline.

The private Creator tool `Tools/CMUMotionCatalog/audit_leading_frames.py`
reproduces this report from the checksum-verified BVHs.
