#!/usr/bin/env bash
set -euo pipefail

if [[ $# != 4 ]]; then
    echo "Usage: bash tools/render_previews.sh CREATOR_CHECKOUT XCODE_DERIVED_DATA STAGED_INPUTS NEW_OUTPUT" >&2
    exit 2
fi

tool_directory="$(cd "$(dirname "$0")" && pwd)"
creator_checkout="$(cd "$1" && pwd)"
staged_inputs="$(cd "$3" && pwd)"
runner="$creator_checkout/Tools/Reference/run-app-check.sh"

if [[ ! -f "$runner" || ! -f "$staged_inputs/render.json" ]]; then
    echo "Expected the Creator app-check runner and staged render.json." >&2
    exit 2
fi

CMU_PREVIEW_INPUT="$staged_inputs" exec bash "$runner" \
    "$tool_directory/RenderCMUCatalogPreviews.swift" "$2" "$4"
