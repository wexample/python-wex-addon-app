"""Domain tags exposed by this addon — one entry per `domain:*` value its commands use."""

from __future__ import annotations


class DomainTag:
    """Functional domain this addon's commands touch."""

    APP_LIFECYCLE = "domain:app-lifecycle"
    CACHE = "domain:cache"
    CONFIG = "domain:config"
    CONTAINER = "domain:container"
    DB = "domain:db"
    DEPLOY = "domain:deploy"
    DNS = "domain:dns"
    DOCKER = "domain:docker"
    ENV = "domain:env"
    GIT = "domain:git"
    HTTP = "domain:http"
    INSTALL = "domain:install"
    INTROSPECTION = "domain:introspection"
    LOG = "domain:log"
    MIGRATION = "domain:migration"
    NETWORK = "domain:network"
    PACKAGE = "domain:package"
    PERFORMANCE = "domain:performance"
    PROXY = "domain:proxy"
    REGISTRY = "domain:registry"
    RELEASE = "domain:release"
    SERVICE = "domain:service"
    SSH = "domain:ssh"
    SYSTEM = "domain:system"
    TEST = "domain:test"
    WEBHOOK = "domain:webhook"
