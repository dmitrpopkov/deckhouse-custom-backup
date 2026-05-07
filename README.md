# Deckhouse Module: Velero Backup

Модуль Deckhouse Kubernetes Platform для **Velero** — резервное копирование
ресурсов кластера и persistent volumes.

## Особенности

- 📦 **Несколько S3 backends** одновременно — `BackupStorageLocation` для каждого
  объявленного хранилища (MinIO, Ceph RGW, AWS S3 и любое S3-совместимое)
- 🌐 **Веб-интерфейс** [otwld/velero-ui](https://github.com/otwld/velero-ui) с
  отдельным порталом и **SSO через Dex DKP** (OIDC)
- 💾 **Node Agent (FS Backup)** включён по умолчанию — бэкап `PersistentVolume`
  без CSI snapshot driver, через kopia или restic
- 📸 **CSI Volume Snapshots** — поддержка snapshot-ов через CSI plugin
- 📊 **Prometheus ServiceMonitor** для мониторинга
- 🛡️ **NetworkPolicy** между namespace
- 🔐 **DexClient CR** регистрируется автоматически — никаких ручных правок Dex

## Архитектура

```
                              ┌─────────────────┐
   user (browser) ─── HTTPS ──┤  Velero UI Ing  │
                              │   /api  /       │
                              └────────┬────────┘
                                       │
                              ┌────────▼────────┐
                              │   velero-ui     │   ◄── OIDC ──► Dex (DKP user-authn)
                              │  (otwld/UI)     │
                              └────────┬────────┘
                                       │ kube API
                              ┌────────▼────────┐
                              │    velero       │   ◄──── BackupStorageLocations ───► S3 (MinIO/AWS/Ceph)
                              │   server pod    │
                              └────────┬────────┘
                                       │
                          ┌────────────▼────────────┐
                          │   node-agent DaemonSet  │   (kopia/restic FS backup)
                          └─────────────────────────┘
```

## Быстрый старт

См. [docs/INSTALL.ru.md](docs/INSTALL.ru.md) — пошаговая инструкция на русском.

Готовый пример: [examples/install-cluster.yaml](examples/install-cluster.yaml).

## Лицензия

Apache-2.0. Velero © VMware Tanzu, velero-ui © otwld.
