#!/usr/bin/env python3
"""
Hook: discover_dex_issuer

Находит в кластере публичный URL Dex (модуль user-authn DKP) и генерирует
OIDC client_secret для Velero UI.

Источники Dex issuer (в порядке приоритета):
1. Спец. ConfigMap d8-user-authn/dex-config (если есть)
2. ModuleConfig user-authn (publishAPI.https.mode + global.modules.publicDomainTemplate)
3. Глобальный ConfigMap d8-system/deckhouse-discovery (clusterDomain + dex.<clusterDomain>)
"""
import json
import os
import secrets
import string
import sys
import yaml


def main():
    binding_context_path = os.environ.get("BINDING_CONTEXT_PATH")
    values_path = os.environ.get("VALUES_PATH")
    config_values_path = os.environ.get("CONFIG_VALUES_PATH")
    values_json_patch_path = os.environ.get("VALUES_JSON_PATCH_PATH")

    if "--config" in sys.argv:
        print(yaml.safe_dump({
            "configVersion": "v1",
            "onStartup": 5,
            "schedule": [
                {"name": "every-5min", "crontab": "*/5 * * * *"}
            ],
            "kubernetes": [
                {
                    "name": "global-cm",
                    "apiVersion": "v1",
                    "kind": "ConfigMap",
                    "namespace": {"nameSelector": {"matchNames": ["d8-system"]}},
                    "nameSelector": {"matchNames": ["deckhouse-discovery"]},
                    "executeHookOnEvent": ["Added", "Modified"],
                    "executeHookOnSynchronization": True,
                    "queue": "/modules/velero/discover",
                },
                {
                    "name": "user-authn-mc",
                    "apiVersion": "deckhouse.io/v1alpha1",
                    "kind": "ModuleConfig",
                    "nameSelector": {"matchNames": ["user-authn", "global"]},
                    "executeHookOnEvent": ["Added", "Modified"],
                    "executeHookOnSynchronization": True,
                    "queue": "/modules/velero/discover",
                },
            ],
        }))
        return

    # Загружаем существующие values
    with open(values_path, "r") as f:
        values = yaml.safe_load(f) or {}

    velero_internal = values.get("velero", {}).get("internal", {}) or {}

    # Получаем publicDomainTemplate из global ModuleConfig
    public_domain_template = None
    cluster_domain = None
    try:
        with open(binding_context_path, "r") as f:
            ctx = json.load(f)
    except Exception:
        ctx = []

    for snapshot_set in ctx:
        snapshots = snapshot_set.get("snapshots", {}) or {}

        # global ModuleConfig + user-authn ModuleConfig
        for obj in snapshots.get("user-authn-mc", []):
            mc = obj.get("object", {}) or {}
            name = mc.get("metadata", {}).get("name")
            spec = mc.get("spec", {}) or {}
            settings = spec.get("settings", {}) or {}
            if name == "global":
                modules = settings.get("modules", {}) or {}
                public_domain_template = modules.get(
                    "publicDomainTemplate", public_domain_template
                )

        # global cluster domain via deckhouse-discovery
        for obj in snapshots.get("global-cm", []):
            cm = obj.get("object", {}) or {}
            data = cm.get("data", {}) or {}
            if "clusterDomain" in data:
                cluster_domain = data["clusterDomain"]

    # Определяем dex issuer
    dex_issuer = None
    if public_domain_template:
        # Шаблон вида '%s.example.com' → подставим dex
        dex_issuer = "https://" + (public_domain_template % "dex")
    elif cluster_domain:
        dex_issuer = f"https://dex.{cluster_domain}"

    # Генерация client secret один раз и сохранение
    client_secret = velero_internal.get("oidcClientSecret")
    if not client_secret:
        alphabet = string.ascii_letters + string.digits
        client_secret = "".join(secrets.choice(alphabet) for _ in range(48))

    # Генерация локального admin-пароля для UI (fallback)
    ui_admin = velero_internal.get("uiAdminPassword")
    if not ui_admin:
        alphabet = string.ascii_letters + string.digits
        ui_admin = "".join(secrets.choice(alphabet) for _ in range(24))

    patches = []
    if dex_issuer:
        patches.append({
            "op": "add",
            "path": "/velero/internal/dexIssuer",
            "value": dex_issuer,
        })
    patches.append({
        "op": "add",
        "path": "/velero/internal/oidcClientSecret",
        "value": client_secret,
    })
    patches.append({
        "op": "add",
        "path": "/velero/internal/uiAdminPassword",
        "value": ui_admin,
    })

    if values_json_patch_path:
        with open(values_json_patch_path, "w") as f:
            json.dump(patches, f)


if __name__ == "__main__":
    main()
