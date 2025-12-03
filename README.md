# wexample-wex-addon-app

Version: 0.0.55

App management with wex

## Table of Contents

- [Status Compatibility](#status-compatibility)
- [Basic Usage](#basic-usage)
- [Api Reference](#api-reference)
- [Tests](#tests)
- [Code Quality](#code-quality)
- [Versioning](#versioning)
- [Changelog](#changelog)
- [Migration Notes](#migration-notes)
- [Roadmap](#roadmap)
- [Security](#security)
- [Privacy](#privacy)
- [Support](#support)
- [Contribution Guidelines](#contribution-guidelines)
- [Maintainers](#maintainers)
- [License](#license)
- [Useful Links](#useful-links)
- [Suite Integration](#suite-integration)
- [Compatibility Matrix](#compatibility-matrix)
- [Dependencies](#dependencies)
- [Suite Signature](#suite-signature)


## Status & Compatibility

**Maturity**: Production-ready

**Python Support**: >=3.10

**OS Support**: Linux, macOS, Windows

**Status**: Actively maintained

## Usage

### Setup & Installation

**Initial setup of the development environment:**
```bash
# Install dependencies for the suite and all packages (production mode)
app::setup/install

# Install dependencies + local editable packages (development mode)
app::setup/install --env local
```

**For a single package:**
```bash
# Production: Install PDM dependencies only
.wex/bin/app-manager setup

# Development: Install dependencies + local editable packages
.wex/bin/app-manager app::setup/install --env local
```

### Complete Development & Publication Workflow

**1. Initial Setup (one-time)**
```bash
# Install dependencies and local editable packages for development
app::setup/install --env local
```

**2. Development Cycle**
```bash
# Rectify code across all packages
app::file-state/rectify --all-packages

# Bump only packages with changes (excluding suite)
app::package/bump --packages-only --force

# Check for circular dependencies
app::dependencies/check

# Propagate versions across all packages
app::version/propagate --packages-only

# Commit and push all changes
app::package/commit-and-push --all-packages --yes
```

**3. Publication**
```bash
# Publish packages with changes to PyPI
app::suite/publish
```

### File State Management
* `app::file-state/rectify [--all-packages]`: Normalizes/rectifies code for a single app or across all packages in the suite; no commits.

### Version Management

The version management commands use `SuiteOrEachPackageMiddleware` which provides flexible execution control:
- **Default**: Executes on the suite (or single package if app_path points to a package)
- **`--all-packages`**: Executes on both the suite AND all packages
- **`--packages-only`**: Executes only on packages (excludes suite, implies `--all-packages`)
- **`--suite-only`**: Executes only on the suite (excludes packages)

Commands:
* `app::package/bump [--all-packages|--packages-only|--suite-only] [--yes] [--force]`: Bumps version for suite and/or packages. Use `--force` to bump only packages/suite with changes (no current version tag on HEAD).
* `app::version/propagate [--packages-only]`: Propagates the current package version to other packages in the suite that depend on it. Use `--packages-only` to propagate all versions at once.

### Git Operations
* `app::package/commit-and-push [--all-packages] [--yes]`: Commits and pushes changes for a single package or all packages with uncommitted changes when using `--all-packages`.

### Dependencies Management
* `app::dependencies/check`: Validates internal dependencies across the suite to prevent circular dependencies.

### Suite Execution
* `app::suite/exec-command -c <command> [--arguments "<args>"]`: Executes a manager command on all packages (e.g., `app::info/show`).
* `app::suite/exec-shell -c "<command>"`: Executes a shell command on all packages.

### Setup & Installation
* `app::setup/install`: Installs PDM dependencies for the suite and all packages. Runs `pdm install` in the suite and each package.
* `app::setup/install --env local`: Development mode - installs dependencies + all local packages as editable dependencies (pip install -e) for cross-package development.
* `.wex/bin/app-manager setup`: Low-level command that runs `pdm install` for a single package (called by app-manager.sh).

### Publishing
* `app::suite/publish`: Publishes packages to PyPI. Only publishes packages with changes since their last publication tag. Automatically bumps versions, rectifies file state, commits, propagates versions, and publishes. Creates and pushes publication tags after successful publish.

### Common Workflows

**Setup development environment:**
```bash
# Full development setup with editable packages
app::setup/install --env local
```

**Bump only packages with changes (excluding suite):**
```bash
app::package/bump --packages-only --force && app::version/propagate --packages-only && app::package/commit-and-push --all-packages --yes
```

**Bump suite and all packages:**
```bash
app::package/bump --all-packages
```

**Bump only the suite:**
```bash
app::package/bump --suite-only
```

**Rectify all packages:**
```bash
app::file-state/rectify --all-packages
```

**Get info for all packages:**
```bash
app::suite/exec-command -c app::info/show
```

## API Reference

The wex-addon-app framework provides two distinct patterns for executing commands across package suites, representing an evolution from legacy inline iteration to a more modular, middleware-based approach.

### Pattern 1: Middleware-Based Iteration (Recommended)

This pattern externalizes iteration logic from the command implementation, allowing commands to focus solely on their core functionality while middlewares handle the iteration concerns.

#### How It Works

Commands are decorated with middleware that can optionally iterate over packages:

- **`AppMiddleware`**: Provides the base `app_workdir` context for a single application
- **`EachSuitePackageMiddleware`**: Extends `AppMiddleware` and adds the `--all-packages` flag
  - When `--all-packages` is **not** specified: executes the command once on the target application
  - When `--all-packages` **is** specified: automatically iterates over all packages in the suite, executing the command on each package individually

#### Example: `app::file-state/rectify`

```python
@middleware(middleware=AppMiddleware)
@middleware(middleware=EachSuitePackageMiddleware)
@command(type=COMMAND_TYPE_ADDON)
def app__file_state__rectify(
    context: ExecutionContext,
    app_workdir: BasicAppWorkdir,
    # ... other options
) -> None:
    # Command implementation focuses only on rectifying a single app
    # Iteration is handled externally by the middleware
    workdir.apply(...)
```

**Usage:**
```bash
# Rectify only the main suite application
.wex/bin/app-manager app::file-state/rectify

# Rectify all packages in the suite
.wex/bin/app-manager app::file-state/rectify --all-packages
```

**Benefits:**
- Clean separation of concerns: command logic vs. iteration logic
- Reusable middleware across multiple commands
- Consistent iteration behavior
- Easy to add iteration capability to existing commands

### Pattern 2: Delegated Iteration (For Suite-Specific Commands)

This pattern is used when the command is inherently suite-oriented and always operates on multiple packages. The iteration is delegated to helper methods on the `FrameworkPackageSuiteWorkdir`.

#### How It Works

Commands use `PackageSuiteMiddleware` to ensure they receive a `FrameworkPackageSuiteWorkdir`, then delegate iteration to:

- **`packages_execute_shell(cmd)`**: Execute shell commands on all packages
- **`packages_execute_manager(command, arguments, context)`**: Execute manager commands (e.g., `app::info/show`) on all packages

#### Example: `app::suite/exec-command`

```python
@middleware(middleware=PackageSuiteMiddleware)
@command(type=COMMAND_TYPE_ADDON)
def app__suite__exec_command(
    context: ExecutionContext,
    command: str,
    app_workdir: FrameworkPackageSuiteWorkdir,
    arguments: str = None,
) -> None:
    # Delegate iteration to the workdir helper
    app_workdir.packages_execute_manager(
        command=command,
        arguments=shell_split_cmd(arguments) if arguments else None,
        context=context
    )
```

**Usage:**
```bash
# Execute a manager command on all packages
.wex/bin/app-manager app::suite/exec-command -c app::info/show

# Execute a shell command on all packages
.wex/bin/app-manager app::suite/exec-shell -c "ls -la"
```

**Benefits:**
- Explicit suite-wide operations
- Centralized iteration logic in workdir helpers
- Consistent error handling and progress reporting
- Suitable for commands that only make sense in a suite context

### Migration Guide: Legacy to Modern Patterns

**Legacy approach** (deprecated):
```python
def old_command(context, app_path):
    suite = get_suite(app_path)
    for package in suite.get_packages():  # Iteration inside command
        # Do something with package
```

**Modern approach** (Pattern 1):
```python
@middleware(middleware=EachSuitePackageMiddleware)
def new_command(context, app_workdir):
    # Iteration handled by middleware when --all-packages is used
    # Command only handles single app logic
```

**Modern approach** (Pattern 2):
```python
@middleware(middleware=PackageSuiteMiddleware)
def suite_command(context, app_workdir: FrameworkPackageSuiteWorkdir):
    # Delegate iteration to workdir helper
    app_workdir.packages_execute_manager(...)
```

### Choosing the Right Pattern

- **Use Pattern 1 (Middleware-Based)** when:
  - The command can operate on both single apps and suites
  - You want optional iteration via `--all-packages`
  - The command logic is app-focused, not suite-focused

- **Use Pattern 2 (Delegated)** when:
  - The command is inherently suite-oriented
  - Iteration is always required (no single-app mode)
  - You're executing shell commands or other manager commands on packages

## Tests

This project uses `pytest` for testing and `pytest-cov` for code coverage analysis.

### Installation

First, install the required testing dependencies:
```bash
.venv/bin/python -m pip install pytest pytest-cov
```

### Basic Usage

Run all tests with coverage:
```bash
.venv/bin/python -m pytest --cov --cov-report=html
```

### Common Commands
```bash
# Run tests with coverage for a specific module
.venv/bin/python -m pytest --cov=your_module

# Show which lines are not covered
.venv/bin/python -m pytest --cov=your_module --cov-report=term-missing

# Generate an HTML coverage report
.venv/bin/python -m pytest --cov=your_module --cov-report=html

# Combine terminal and HTML reports
.venv/bin/python -m pytest --cov=your_module --cov-report=term-missing --cov-report=html

# Run specific test file with coverage
.venv/bin/python -m pytest tests/test_file.py --cov=your_module --cov-report=term-missing
```

### Viewing HTML Reports

After generating an HTML report, open `htmlcov/index.html` in your browser to view detailed line-by-line coverage information.

### Coverage Threshold

To enforce a minimum coverage percentage:
```bash
.venv/bin/python -m pytest --cov=your_module --cov-fail-under=80
```

This will cause the test suite to fail if coverage drops below 80%.

## Code Quality & Typing

All the suite packages follow strict quality standards:

- **Type hints**: Full type coverage with mypy validation
- **Code formatting**: Enforced with black and isort
- **Linting**: Comprehensive checks with custom scripts and tools
- **Testing**: High test coverage requirements

These standards ensure reliability and maintainability across the suite.

## Versioning & Compatibility Policy

Wexample packages follow **Semantic Versioning** (SemVer):

- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

We maintain backward compatibility within major versions and provide clear migration guides for breaking changes.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history and release notes.

Major changes are documented with migration guides when applicable.

## Migration Notes

When upgrading between major versions, refer to the migration guides in the documentation.

Breaking changes are clearly documented with upgrade paths and examples.

## Known Limitations & Roadmap

Current limitations and planned features are tracked in the GitHub issues.

See the [project roadmap](https://github.com/wexample/python-wex_addon_app/issues) for upcoming features and improvements.

## Security Policy

### Reporting Vulnerabilities

If you discover a security vulnerability, please email contact@wexample.com.

**Do not** open public issues for security vulnerabilities.

We take security seriously and will respond promptly to verified reports.

## Privacy & Telemetry

This package does **not** collect any telemetry or usage data.

Your privacy is respected — no data is transmitted to external services.

## Support Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community support
- **Documentation**: Comprehensive guides and API reference
- **Email**: contact@wexample.com for general inquiries

Community support is available through GitHub Discussions.

## Contribution Guidelines

We welcome contributions to the Wexample suite!

### How to Contribute

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

## Maintainers & Authors

Maintained by the Wexample team and community contributors.

See [CONTRIBUTORS.md](CONTRIBUTORS.md) for the full list of contributors.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Free to use in both personal and commercial projects.

## Useful Links

- **Homepage**: https://github.com/wexample/python-wex-addon-app
- **Documentation**: [docs.wexample.com](https://docs.wexample.com)
- **Issue Tracker**: https://github.com/wexample/python-wex-addon-app/issues
- **Discussions**: https://github.com/wexample/python-wex-addon-app/discussions
- **PyPI**: [pypi.org/project/wexample-wex-addon-app](https://pypi.org/project/wexample-wex-addon-app/)

## Integration in the Suite

This package is part of the Wexample Suite — a collection of high-quality, modular tools designed to work seamlessly together across multiple languages and environments.

### Related Packages

The suite includes packages for configuration management, file handling, prompts, and more. Each package can be used independently or as part of the integrated suite.

Visit the [Wexample Suite documentation](https://docs.wexample.com) for the complete package ecosystem.

## Compatibility Matrix

This package is part of the Wexample suite and is compatible with other suite packages.

Refer to each package's documentation for specific version compatibility requirements.

## Dependencies

- attrs: >=23.1.0
- cattrs: >=23.1.0
- tomlkit: 
- wexample-wex-core: ==6.0.67


# About us

[Wexample](https://wexample.com) stands as a cornerstone of the digital ecosystem — a collective of seasoned engineers, researchers, and creators driven by a relentless pursuit of technological excellence. More than a media platform, it has grown into a vibrant community where innovation meets craftsmanship, and where every line of code reflects a commitment to clarity, durability, and shared intelligence.

This packages suite embodies this spirit. Trusted by professionals and enthusiasts alike, it delivers a consistent, high-quality foundation for modern development — open, elegant, and battle-tested. Its reputation is built on years of collaboration, refinement, and rigorous attention to detail, making it a natural choice for those who demand both robustness and beauty in their tools.

Wexample cultivates a culture of mastery. Each package, each contribution carries the mark of a community that values precision, ethics, and innovation — a community proud to shape the future of digital craftsmanship.

