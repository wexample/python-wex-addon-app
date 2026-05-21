from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


class Migration_6_0_1__1(AbstractMigration):
    VERSION = "6.0.1"
    SEQ = 1
    DESCRIPTION = (
        "Migrate wex-5 knowledge structure: rename .wex/doc to .wex/knowledge, "
        "move README.md to .wex/knowledge/readme/introduction.md"
    )

    def apply(self, context: MigrationContext) -> None:
        wex_dir = context.target_path / ".wex"

        # Rename .wex/doc → .wex/knowledge
        doc_dir = wex_dir / "doc"
        knowledge_dir = wex_dir / "knowledge"
        if doc_dir.exists() and not knowledge_dir.exists():
            doc_dir.rename(knowledge_dir)
        else:
            knowledge_dir.mkdir(parents=True, exist_ok=True)

        # Move README.md → .wex/knowledge/readme/introduction.md
        readme = context.target_path / "README.md"
        if readme.exists():
            readme_dir = knowledge_dir / "readme"
            readme_dir.mkdir(parents=True, exist_ok=True)
            readme.rename(readme_dir / "introduction.md")

    def rollback(self, context: MigrationContext) -> None:
        wex_dir = context.target_path / ".wex"
        knowledge_dir = wex_dir / "knowledge"

        # Move .wex/knowledge/readme/introduction.md back to README.md
        introduction = knowledge_dir / "readme" / "introduction.md"
        if introduction.exists():
            introduction.rename(context.target_path / "README.md")

            readme_dir = knowledge_dir / "readme"
            try:
                readme_dir.rmdir()
            except OSError:
                pass

        # Rename .wex/knowledge → .wex/doc if it was originally named doc
        # (we can only safely do this if knowledge was empty after removing readme)
        doc_dir = wex_dir / "doc"
        if not doc_dir.exists():
            try:
                knowledge_dir.rename(doc_dir)
            except OSError:
                pass
