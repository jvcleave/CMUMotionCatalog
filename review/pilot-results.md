# CMU action review pilot results

The pilot covers 40 take IDs and all 15 proposed primary categories. Keep
the category definitions for subject review. Reserve **Action Sequences** for
takes with distinct actions whose individual uses justify separate ranges.
The cleaning actions in `86_12` fit **Everyday Tasks** because they dominate
the take. The UUIDs for `83_01` and `122_01` differ, but their pinned BVH
SHA-256 digests and rendered movement match. Carry their shared description
onto both identities.

## Identical-evidence model comparison

GPT-6.1 Terra at medium reasoning and GPT-6 Luna each reviewed the same 58
ordered, time-stamped three-quarter contact sheets. Both initial passes were
blind to the original descriptions. Final adjudication used additional
rendered frames or views, root travel, and original descriptions when needed.
The first-pass frames included some clipped tall motions. The camera fix
removed the clipping in the four affected takes checked after the comparison.

| Metric | GPT-6.1 Terra | GPT-6 Luna |
| --- | ---: | ---: |
| Main visible movement captured | 35 / 40 | 30 / 40 |
| Primary category matched the adjudicated pilot | 27 / 40 | 24 / 40 |
| Specific actor-relative direction captured | 0 / 10 | 2 / 10 |
| Handedness named in two clear one-handed examples | 0 / 2 | 0 / 2 |
| Selected sequence or finish captured | 9 / 10 | 2 / 10 |
| Approximate elapsed model review | 9 min 20 s | 9 min 55 s |

Main movement scoring credits accurate visible mechanics even where an
original source description supplies the eventual category. The misses for
Terra were `143_17`, `13_34`, `143_28`, `83_01`, and `124_05`. The misses for
Luna were `02_04`, `83_47`, `86_10`, `143_17`, `13_34`, `143_28`, `83_19`,
`69_52`, `01_07`, and `124_05`.

The direction check used `02_01`, `02_02`, `02_03`, `16_17`, `16_20`,
`83_47`, `69_52`, `83_01`, `83_19`, and `122_01`. For a turn, the score
requires the specific direction change. For handedness, the examples were
the raised hand in `02_06` and the wiping arm in `86_12`. Sequence and finish
scoring used `02_01`, `02_02`, `02_04`, `83_47`, `27_08`, `86_10`, `86_12`,
`143_18`, `05_11`, and `124_05`. Terra missed the jump shot sequence. Luna
captured the low-to-high reaches and walking finish of `86_12` and the repeated
descent and rise in `143_18`.

| Take | Correction or additional evidence |
| --- | --- |
| `02_01`, `02_02`, `02_03` | The root path confirms forward travel. The side view shows both walks ending mid-stride. Luna called the jog in-place and had the steady walk settling to a stand. |
| `02_04`, `83_47` | Takeoff and landing appear in the renders. Luna described both as squats. |
| `16_17`, `16_20`, `69_52` | Root travel and the changing heading distinguish left and right turns and backward travel. |
| `13_34`, `01_07`, `124_05` | A wider vertical fit recovered the complete climbing and jumping poses. The ladder, playground setup, and basketball scenario come from the original CMU descriptions. |
| `83_01`, `122_01` | Separate original sheets both show the same wide diagonal step. Terra reported one sheet blank. |
| `86_10`, `86_12` | The overlapping windows show the jog in `86_10` and the low-to-high cleaning sequence in `86_12`. |

Terra recorded two requests for a second look, on the climb and the sheet
it reported as blank. Luna recorded no second-view requests. The adjudication
still needed root travel, the walk side view, and framing rerenders. Use
**Terra for the initial subject pass**. The gaps in Luna's jump recognition
and sequencing, combined with similar elapsed times, give little reason to
route straightforward takes to Luna in this pilot. Use root travel for
locomotion, source context for scenes with props, and denser frames or a
second view for quick or ambiguous movement.

## Time estimate

The three short-heavy batches averaged about 12 seconds per take for Terra
across 32 takes. Each contained some medium or long clips. The batch of
eight takes over 30 seconds averaged about 23 seconds per take. These are
batch elapsed estimates from the reviewers, including assessment and
writing. The pilot did not separately time a human review.

There were 2,157 takes at or below 30 seconds and 351 longer takes after
the pilot. Applying the observed Terra rates gives about 9.3 reviewer-hours
for one model pass, plus rendering, rerenders and adjudication. The
four original render runs took about 45, 141, 51 and 54 seconds of wall
time and partly overlapped. The first full subject checkpoints will help
refine the estimate.
