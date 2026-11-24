# CMU motion review and action categories

Review all 2,548 CMU BVH takes and give each a short title, an action
description, and one primary category. Keep the original CMU description and
use the existing take ID and source UUID to join the review to the catalog.
The finished category list should help someone find a usable motion in
Creator without knowing which subject performed it.

The v1.0.1 catalog contains about 9 hours and 52 minutes of recorded motion.
The median take lasts 7.3 seconds, and 360 takes exceed 30 seconds. The
catalog assigns 881 takes to **Other Motion** or **Unclassified**. Start with
a representative set, including previously reviewed takes, so the same
action and category rules apply across the collection. [Public catalog](https://github.com/jvcleave/CMUMotionCatalog/tree/v1.0.1/catalog)

## Review the recorded motion

1. **Prepare the review material.** Extend the private catalog tools to render
   continuous playback on the Default Human from the pinned BVH files. Show
   the take ID, source time, and a consistent three-quarter camera. Use a
   side view or a floor view of the root path when direction, ground contact,
   or the start and finish need a closer look. Keep the review renders in
   local build storage. The 10-frame previews serve the browsing catalog.
   [Existing catalog tools](https://github.com/jvcleave/MessCharacterCreator/blob/main/Tools/CMUMotionCatalog/README.md).
2. **Pilot 40 takes.** Include one **Alaskan vacation** take from each of
   subjects 27–32, close variants of familiar actions, clips with generic
   labels, a two-frame take, and several long mixed-action takes. Include
   enough clear examples to test each proposed category. Review the first
   batch together with its descriptions and category assignments. Settle
   the writing style, split or merge categories where the examples justify
   it, and measure review time for short and long takes separately.
3. **Review by subject and take.** Keep related trials together so differences
   in pace, direction, stance, or finish are easy to compare. Split long
   takes into consecutive review windows with overlapping boundaries.
   Check fast or ambiguous actions at slower speed or frame by frame.
   Checkpoint each batch by stable take ID and use the pilot timings to
   size later batches.
4. **Recheck uncertain assignments.** Revisit flagged takes and any closely
   related trials whose descriptions or categories differ. Sample across
   completed categories and mixed-action clips for consistency. Keep any
   remaining uncertainty explicit in the description.

The pilot is done when all 40 takes have a description and a primary
assignment, the category list has definitions and representative takes, and
there is a measured estimate and a model choice for the remaining review.

## Terra and Luna pilot comparison

Start the visual pass with GPT-6.1 Terra at medium reasoning. Compare it
with GPT-6 Luna on the same pilot material, including straightforward
walks and gestures, similar takes with different finishes, and long
sequences. OpenAI recommends Terra for visual reasoning and Luna for
focused, repeatable work. The pilot measures how each handles these
specific clips. [OpenAI model selection guide](https://developers.openai.com/api/docs/guides/model-selection)

Give both models the same ordered, time-stamped frames and category
definitions. Compare their descriptions against the rendered playback.
Score the main action, category choice, direction, handedness, and
sequence of movements where observable. Record factual corrections,
time, and the need for a second view or replay. Use Luna for straightforward
takes if its descriptions hold up in the pilot. Route ambiguous gestures,
near-duplicates, and long sequences to Terra, with a closer view or higher
reasoning effort where it improves the result. Use scripts to check
coverage, IDs, and valid time ranges.

## What each take gets

| Field | Review rule |
| --- | --- |
| Title | Use a short, verb-led or action-led name. Keep a visible take ID available when several takes share a title. |
| Action description | Write one or two sentences describing the starting pose, main movement, and finish. Include direction, handedness, repetition, or a transition when it helps someone choose the take. |
| Primary category | Choose one category from the agreed list according to the main action a user would look for. |
| Search tags | Capture secondary actions and useful qualifiers such as backward, right hand, repeated, and starts at rest. |
| Time ranges | Add optional source-time ranges where longer takes have distinct usable actions. Reference the captured frames after the calibration pose. |
| Review status | Track pending, described, and needs review by take ID. Record which part needs a second look. |
| Source fields | Preserve the original title or description, source UUID, timing, and payload checksum. |

For a take titled **Alaskan vacation**, use the visible action to write the
new title and description, and retain **Alaskan vacation** in the original
description. If the visible action is a reach followed by a wave, describe
the reach and wave and tag both. Attribute any scenario or object identified
by the source description to that source.

## Proposed category list

| Category | Assign when the main action is |
| --- | --- |
| Walking & Turning | Walking forward, backward, or sideways, or making a walking or in-place turn. |
| Running & Agility | Jogging, running, sprinting, or taking quick lateral steps, cuts, and dodges. |
| Jumping & Landing | Jumping, hopping, leaping, or landing after takeoff. |
| Balance & Recovery | Balancing, correcting a stumble or slip, falling, or recovering from a loss of balance. |
| Stairs & Climbing | Going up or down stairs, stepping onto a raised surface, climbing, or hanging. |
| Posture Changes | Sitting, standing up, kneeling, lying down, or moving between the floor and standing. |
| Reaching & Handling | Reaching for, lifting, carrying, placing, grasping, pushing, or pulling. Use tags for a box or another object when the source identifies it. |
| Everyday Tasks | Acting out a recognizable routine such as dressing, washing, grooming, or cleaning. |
| Gestures & Pantomime | Waving, pointing, shrugging, signaling, or acting something out through body movement. |
| Dance | Performing dance steps, turns, or choreographed phrases. |
| Sports | Performing sport-specific actions such as a golf swing, basketball shot, or swim stroke. |
| Acrobatics | Performing cartwheels, handstands, flips, rolls, or similarly gymnastic movements. |
| Exercise & Mobility | Stretching, practicing yoga, or performing a drill or repeated range-of-motion exercise. |
| Action Sequences | Performing several equally important actions with no single dominant movement. |
| Poses & Reference | Holding a pose or performing a technical calibration or reference take. |

Use **Jumping & Landing** for a jump with a routine landing and
**Balance & Recovery** when regaining balance defines the take. Classify a
quick dodge under **Running & Agility** and a normal lateral walk under
**Walking & Turning**. When a take includes multiple movements, use the main
action for its category and tag the others. Check **Action Sequences** during
the pilot with examples that genuinely need it.

The current Motion Clip Session picker combines HOLD and CMU categories,
with **Show All** and **Hide All** as visibility controls. The proposed list
splits **Jumping & Recovery** and **Sitting & Reaching**, gives box handling a
home within **Reaching & Handling**, and turns **Calibration** into a broader
reference group. Resolve **Other Motion** and **Unclassified** through
review. Keep **Other HOLD Takes** as a HOLD source group while reviewing CMU.
Build a crosswalk for the other HOLD groups where their existing meaning
clearly maps to a shared category. [Current picker grouping](https://github.com/jvcleave/MessCharacterCreator/blob/main/MessCharacterCreator/MessCharacterCreator/Presentation/MotionDataBrowserViewModel.swift).

## Finish and integrate

- Deliver a versioned category list with stable IDs, display names,
  definitions, example takes, and counts. Validate one reviewed entry per
  source UUID, one primary category for each take, and time ranges within
  the captured frames. Bring any unresolved reviews to a decision before
  publishing the assignments.
- Generate the public catalog from the reviewed annotations and reuse the
  verified motion files and previews in its single release ZIP. Bind the
  Creator bundle to the published catalog digest.
- Show action descriptions in take details and make them searchable
  alongside title, take ID, tags, and original wording. Use the same
  category definitions for available and installed CMU takes. Use the
  existing source UUIDs to preserve saved session references, favorites,
  and custom pad titles.
- Verify a short review take, a long sequence, and an older installed take
  in Motion Data and the Motion Clip Session picker. Check category filters,
  descriptions, search, and reopening a saved timeline with authored trims.
  See `docs/internal/handoffs/cmu-curated-labels.md` in the Creator checkout.
