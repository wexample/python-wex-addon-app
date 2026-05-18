from __future__ import annotations

from wexample_wex_addon_app.publication.strategy.abstract_publication_strategy import (
    AbstractPublicationStrategy,
)


class MainPushPublicationStrategy(AbstractPublicationStrategy):
    """Push directly to main — tag push always triggers CI immediately."""
