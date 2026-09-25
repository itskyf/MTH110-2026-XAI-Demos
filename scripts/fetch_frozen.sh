#!/usr/bin/env bash
set -o errexit -o nounset -o pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir --parents "${REPO_ROOT}/data"

printf 'Fetching v1.0.0/frozen.json\n' >&2
gh release download v1.0.0 \
	--repo itskyf/MTH110-2026-XAI-Demos \
	--pattern frozen.json \
	--dir "${REPO_ROOT}/data"
printf 'Saved %s/data/frozen.json\n' "$REPO_ROOT" >&2
