# CMU action review pilot

The [review plan](../docs/CMU_MOTION_ACTION_REVIEW_PLAN.md) defines the workflow.
The pilot roster fixes the 40 source UUIDs and review batches. The category
file holds the proposed definitions. The annotations file accumulates reviewed
takes in roster order. An absent row is pending. A row marked `needs-review`
has a specific question in `reviewNote`.

Optional segments use inclusive, one-based captured source frame numbers. The
first captured frame corresponds to zero seconds. Its calibration pose precedes
it in the BVH. Convert a captured frame to seconds with
`(frame - 1) * frameInterval`.

Run `python3 review/validate.py` before committing a batch. Add `--complete`
for the pilot coverage check and `--catalog-complete` for the release coverage
check. Review renders and model evidence are kept in local build storage.

The [pilot results](pilot-results.md) record the model comparison and timing.
For subject review, add each batch to `subjects/<subject>.json` with
`schemaVersion`, `subject`, and a `takes` array using the annotation format.
Reuse pilot entries by source UUID. Keep takes in capture order within a
subject, and leave a precise follow-up note on any provisional assignment.

To add or replace adjudicated rows, run
`python3 review/checkpoint.py SUBJECT DRAFT.json`. The draft needs a `takes`
array with each take ID and editorial fields. The tool copies pinned source
fields from the catalog and validates the proposed checkpoint before writing it.

Run `python3 review/pending.py SUBJECT` to check the queue for a subject. It
shows reviewed takes that share the pinned BVH digest and calls out differences
in source context. Reuse only editorial fields that apply to both records.
Use `--ids` to get the pending take IDs for the Creator renderer.

The [source timing audit](source-timing.md) lists takes with leading all-zero
captured frames and the open decision about their usable starts.

For an affected take, `firstUsableFrame` identifies the first usable pose in
original captured-frame coordinates. Keep the pinned BVH, source timing, and
existing trim coordinates. Log take-specific concerns as `needs-review` with
a `reviewNote` while continuing other batches.

Run `python3 review/pending.py --issues` for the later review queue. It lists
flagged annotations and audited source issues that still await annotation.
The regular pending queue skips rows that already have an annotation.
