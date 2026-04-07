from __future__ import annotations

from wexample_wex_addon_app.service.app_service import AppService


class LetsencryptService(AppService):
    def get_runtime_contribution(self) -> dict:
        contribution = super().get_runtime_contribution()

        domains = self.app_workdir.get_config().search("domains").get_list_or_default([])
        contribution["domains_string"] = " ".join(str(d) for d in domains)

        return contribution
