# wex_addon_app

Version: 20.5.0

App management with wex

## Table of Contents

- [Tests](#tests)
- [Suite Integration](#suite-integration)
- [Dependencies](#dependencies)
- [Versioning](#versioning)
- [License](#license)
- [Suite Integration](#suite-integration)
- [Suite Signature](#suite-signature)
- [Api Reference](#api-reference)
- [Basic Usage](#basic-usage)
- [Introduction](#introduction)
- [Suite Publication](#suite-publication)
- [Roadmap](#roadmap)
- [Status Compatibility](#status-compatibility)
- [Useful Links](#useful-links)
- [Migration Notes](#migration-notes)

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

## Integration in the Suite

This package is part of the Wexample Suite — a collection of high-quality, modular tools designed to work seamlessly together across multiple languages and environments.

### Related Packages

The suite includes packages for configuration management, file handling, prompts, and more. Each package can be used independently or as part of the integrated suite.

Visit the [Wexample Suite documentation](https://docs.wexample.com) for the complete package ecosystem.

## Dependencies

- attrs: >=23.1.0
- cattrs: >=23.1.0
- jinja2: >=3.0
- tomlkit: 
- wexample-migration: >=10.0.0
- wexample-runner: >=9.0.0
- wexample-wex-core: >=24.1.0

## Versioning & Compatibility Policy

Wexample packages follow **Semantic Versioning** (SemVer):

- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

We maintain backward compatibility within major versions and provide clear migration guides for breaking changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Free to use in both personal and commercial projects.

## Integration in the Suite

This package is part of the Wexample Suite — a collection of high-quality, modular tools designed to work seamlessly together across multiple languages and environments.

### Related Packages

The suite includes packages for configuration management, file handling, prompts, and more. Each package can be used independently or as part of the integrated suite.

Visit the [Wexample Suite documentation](https://docs.wexample.com) for the complete package ecosystem.

# About us

[Wexample](https://wexample.com) stands as a cornerstone of the digital ecosystem — a collective of seasoned engineers, researchers, and creators driven by a relentless pursuit of technological excellence. More than a media platform, it has grown into a vibrant community where innovation meets craftsmanship, and where every line of code reflects a commitment to clarity, durability, and shared intelligence.

This packages suite embodies this spirit. Trusted by professionals and enthusiasts alike, it delivers a consistent, high-quality foundation for modern development — open, elegant, and battle-tested. Its reputation is built on years of collaboration, refinement, and rigorous attention to detail, making it a natural choice for those who demand both robustness and beauty in their tools.

Wexample cultivates a culture of mastery. Each package, each contribution carries the mark of a community that values precision, ethics, and innovation — a community proud to shape the future of digital craftsmanship.

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
app::package/push --all-packages --yes
```

**3. Publication**
```bash
# Publish packages with changes to PyPI
package::suite/publish
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
* `app::package/push [--all-packages] [--yes]`: Commits and pushes changes for a single package or all packages with uncommitted changes when using `--all-packages`.

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
* `package::suite/publish`: Publishes packages to PyPI. Only publishes packages with changes since their last publication tag. Automatically bumps versions, rectifies file state, commits, propagates versions, and publishes. Creates and pushes publication tags after successful publish.

### Common Workflows

**Setup development environment:**
```bash
# Full development setup with editable packages
app::setup/install --env local
```

**Bump only packages with changes (excluding suite):**
```bash
app::package/bump --packages-only --force && app::version/propagate --packages-only && app::package/push --all-packages --yes
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

## Introduction

### App Manager Architecture

The wex-addon-app framework uses a subprocess-based architecture to manage individual packages within a suite. Each package is managed through its own **App Manager** instance, which is a self-contained Python application that handles package-specific operations.

#### How It Works

Each package in a suite has access to an App Manager executable located at `.wex/bin/app-manager`. This manager is automatically installed and configured for each package, providing a consistent interface for executing commands on that specific package.

**Key characteristics:**

- **Isolation**: Each package runs commands in its own subprocess via the App Manager
- **Custom behavior**: Packages can have specialized classes, imports, and dependencies without affecting others
- **Consistency**: All packages share the same command interface through their App Manager
- **Flexibility**: Package-specific configurations and behaviors are encapsulated within each package's context

#### Example Usage

From any package directory, you can execute commands through the App Manager:

```bash
# Show information about the current package
.wex/bin/app-manager app::info/show

# Rectify file state for the current package
.wex/bin/app-manager app::file-state/rectify

# Bump the package version
.wex/bin/app-manager app::package/bump
```

The App Manager executable is located at:
```
/path/to/package/.wex/bin/app-manager
```

This architecture enables suite-level operations to delegate work to individual packages while maintaining proper isolation and allowing each package to implement custom behavior as needed.

### Suite-Level Operations

When working with a package suite (a collection of related packages), the framework provides commands that can iterate over all packages, executing the App Manager for each one. This is handled through two main patterns:

1. **Middleware-based iteration** (`EachSuitePackageMiddleware`): Commands that can optionally iterate over all packages using the `--all-packages` flag
2. **Delegated iteration** (`PackageSuiteMiddleware`): Suite-specific commands that always operate on multiple packages

See the [API Reference](api-reference.md.j2) for detailed information on these patterns.

# Suite Publication

## Commande

```bash
wex package::suite/publish --yes
```

Depuis la racine de la suite (ex. `PACKAGES/PYTHON/`).

---

## Ce que fait `suite/publish`

**1. Affiche le statut**
Chaque package indique sa version, le type de bump prévu (`patch` / `minor` / `major`) et s'il est `to publish` ou `up to date`.

**2. Valide les dépendances internes**
Vérifie que les imports correspondent aux déclarations dans les `pyproject.toml`.
Auto-corrige aussi les pins `==` sur des packages internes → convertis en `>=` (les packages modifiés sont alors inclus automatiquement dans la publication).

**3. Synchronise les bibliothèques externes** (`libraries/sync`)
Si un package est configuré avec des `libraries` externes (suites tierces), leurs versions sont mises à jour.

**4. Publie dans l'ordre topologique** (feuilles → tronc)
Pour chaque package avec des changements :
- **Bump** : incrémente la version selon le type de changement détecté
- **Rectify** : applique le file state (README, structure, etc.)
- **Commit & push** : commit les changements sur une branche `version-x.y.z`
- **Propagate** : met à jour les dépendants dans la suite avec `>=nouvelle_version` (uniquement pour les bumps intermediate/major)
- **Publish** : upload sur PyPI

---

## Types de bump

| Type | Chiffre modifié | Propagation aux dépendants |
|---|---|---|
| `minor` (patch) | 3ème (`x.y.Z`) | Non — `>=` déjà satisfait |
| `intermediate` (minor) | 2ème (`x.Y.z`) | Oui |
| `major` | 1er (`X.y.z`) | Oui |

La détection est automatique : changements dans `src/` → intermediate ou major, reste → minor.

---

## Règles sur les contraintes

Les dépendances **internes** (packages de la suite) doivent toujours utiliser `>=`, jamais `==`.
Un pin `==` survivra aux bumps mineurs sans se mettre à jour, causant des échecs de résolution (`pip`/`uv` backtracking silencieux).

La validation au début de `suite/publish` auto-corrige les violations.

---

## Après la publication

Mettre à jour `requirements.txt` dans les projets consommateurs :

```bash
uv pip compile requirements.in --upgrade --output-file requirements.txt
```

> `pip-compile` peut échouer avec `ResolutionTooDeepError` sur des suites profondes — utiliser `uv` à la place.

## Known Limitations & Roadmap

Current limitations and planned features are tracked in the GitHub issues.

See the [project roadmap](https://github.com/wexample/python-wex_addon_app/issues) for upcoming features and improvements.

## Status & Compatibility

**Maturity**: Production-ready

**Python Support**: >=3.10

**OS Support**: Linux, macOS, Windows

**Status**: Actively maintained

## Useful Links

- **Homepage**: https://github.com/wexample/python-wex-addon-app
- **Documentation**: [docs.wexample.com](https://docs.wexample.com)
- **Issue Tracker**: https://github.com/wexample/python-wex-addon-app/issues
- **Discussions**: https://github.com/wexample/python-wex-addon-app/discussions
- **PyPI**: [pypi.org/project/wex_addon_app](https://pypi.org/project/wex_addon_app/)

## Migration Notes

When upgrading between major versions, refer to the migration guides in the documentation.

Breaking changes are clearly documented with upgrade paths and examples.
