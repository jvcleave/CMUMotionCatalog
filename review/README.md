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
for the final coverage check. Review renders and model evidence are kept in
local build storage.
