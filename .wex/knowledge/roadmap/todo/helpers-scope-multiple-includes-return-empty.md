# build_scopes returns empty set for multiple inclusions

**Source**: `src/wexample_wex_addon_app/helpers/scope.py:24`
**Agent**: agent:tests
**Bucket**: scope-unclear
**Severity**: bug

## Symptom
`build_scopes("content,location")` returns an empty set. Each non-negated part is
applied with `result &= {scope}`, so a second inclusion intersects away the first and
nothing remains. A single inclusion and exclusion-only filters work as expected.

## Suggested direction
Decide the intended semantics for inclusions (most likely a union of the named scopes,
intersected only against exclusions) and reconcile how include and exclude parts combine
in one filter string. Touches the filter contract, so confirm callers before changing.
