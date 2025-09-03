# wexample-wex-addon-app

App management with wex

Version: 0.0.42

## Requirements

- Python >=3.10

## Dependencies

- pydantic>=2,<3
- wexample-wex-core==6.0.44

## Installation

```bash
pip install wexample-wex-addon-app
```

## Usage

## Usage

* `app::files-state/rectify`: Normalizes/rectifies code across the suite; no commits.
* `app::suite/bump-changed --yes [--all|--package X]`: Bumps only packages that have new content (no current version tag on HEAD), then propagates versions and commits/pushes.
* `app::suite/prepare --yes [--all|--package X]`: Validates internal deps, propagates versions, and commits/pushes if needed.
* `app::suite/publish [--all|--package X]`: Publishes only packages that need it; adds/pushes publication tag after successful publish; never bumps here.

## Links

- Homepage: https://github.com/wexample/python-wex-addon-app

## License

MIT
## Credits

This package has been developed by [Wexample](https://wexample.com), a collection of tools and utilities to streamline development workflows.

Visit [wexample.com](https://wexample.com) to discover more tools and resources for efficient development.