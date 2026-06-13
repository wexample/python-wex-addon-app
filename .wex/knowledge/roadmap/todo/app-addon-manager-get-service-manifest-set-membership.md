# get_service_manifest: use a seen-set for O(1) dedup inside tag/dependency accumulation

**Source**: `wex/wex-addon-app/src/wexample_wex_addon_app/app_addon_manager.py:278`
**Agent**: agent:performance
**Bucket**: set-membership
**Severity**: perf

## Symptom
The inner loop uses `if value not in values` where `values` is a list, giving O(n) membership checks per accumulated value across `tags` and `dependencies` keys.

## Suggested direction
Introduce a `seen: set` alongside `values: list` and test/insert into `seen` instead of `values`; safe only once the caller confirms that tag/dependency values are always hashable (they appear to be strings from context, but the annotation is `Any`).
