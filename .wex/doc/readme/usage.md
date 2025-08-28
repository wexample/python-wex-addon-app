## Usage

* `app::files-state/rectify`: Normalizes/rectifies code across the suite; no commits.
* `app::suite/bump-changed --yes [--all|--package X]`: Bumps only packages that have new content (no current version tag on HEAD), then propagates versions and commits/pushes.
* `app::suite/prepare --yes [--all|--package X]`: Validates internal deps, propagates versions, and commits/pushes if needed.
* `app::suite/publish [--all|--package X]`: Publishes only packages that need it; adds/pushes publication tag after successful publish; never bumps here.