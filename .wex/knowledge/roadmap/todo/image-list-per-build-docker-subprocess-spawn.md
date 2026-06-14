# app__image__list spawns one `docker images` subprocess per build

**Source**: `wex/wex-addon-app/src/wexample_wex_addon_app/commands/image/list.py:49`
**Agent**: agent:performance
**Bucket**: benchmark-first
**Severity**: perf

## Symptom
The loop over `builds.items()` invokes `subprocess.run(["docker", "images", ..., tag])`
once per build, paying full docker CLI startup cost N times. With many builds this scales
linearly in process spawns, which dominates the command's wall time.

## Suggested direction
Consider a single `docker images` call (no tag filter, with a repo/tag column) and match
rows locally, or a batched query, instead of one subprocess per build. Benchmark with a
builds.yml of ~1, ~10, ~50 entries to confirm the spawn overhead before restructuring.
