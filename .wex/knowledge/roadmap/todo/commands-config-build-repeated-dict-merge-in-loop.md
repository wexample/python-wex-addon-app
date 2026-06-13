# _runtime: sequential dict_merge calls in service and hook loops

**Source**: `wex/wex-addon-app/src/wexample_wex_addon_app/commands/config/build.py:88`
**Agent**: agent:performance
**Bucket**: restructure
**Severity**: perf

## Symptom
`_runtime` calls `dict_merge(merged, contribution)` inside two separate loops (services loop lines 88–90, hook loop lines 96–98), producing a new dict on every iteration. With many services or hooks the intermediate allocations add up.

## Suggested direction
Collect all contributions into an ordered list and reduce with a single chained `dict_merge`, or accept an iterable in `dict_merge` itself — both approaches remove the per-iteration intermediate dict allocation while preserving merge order.
