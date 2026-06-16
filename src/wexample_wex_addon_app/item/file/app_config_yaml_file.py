from __future__ import annotations

from wexample_filestate.item.file.yaml_file import YamlFile
from wexample_helpers.decorator.base_class import base_class


@base_class
class AppConfigYamlFile(YamlFile):
    """A wex app `.wex/config.yml` (base or per-env)."""

    def read_domains(self) -> list[str]:
        """Return declared domains, merging `domain:` (single) and `domains:` (list)."""
        try:
            data = self.read_parsed(strict=False) or {}
        except Exception:
            return []
        out: list[str] = []
        seen: set[str] = set()
        single = data.get("domain")
        if isinstance(single, str) and single:
            out.append(single)
            seen.add(single)
        multi = data.get("domains") or []
        if isinstance(multi, list):
            for d in multi:
                if isinstance(d, str) and d and d not in seen:
                    out.append(d)
                    seen.add(d)
        return out
