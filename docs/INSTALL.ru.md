# Установка модуля velero в Deckhouse Kubernetes Platform

## Предварительные условия

В DKP должны быть включены модули:

- `user-authn` — Dex для SSO
- `cert-manager` — выпуск TLS-сертификатов
- `ingress-nginx` (или другой ingress controller)
- `prometheus` (для ServiceMonitor; опционально)
- `snapshot-controller` (для CSI snapshots; опционально)

## 1. Сборка и публикация модуля (один раз)

Если форк/копия — соберите модуль через GitHub Actions:

1. **Settings → Actions → General → Workflow permissions** — выбрать
   **Read and write permissions**.
2. Создать тег `v0.1.0` → автоматически запустится workflow **Build**.
3. После успешной сборки сделать пакеты GHCR публичными:
   - Profile → Packages → `velero` → Package settings → Change visibility → **Public**
   - То же для `velero/release`
4. Запустить workflow **Deploy** с параметрами `release_channel=alpha`,
   `tag=v0.1.0`.

После этого в реестре `ghcr.io/<your-user>/modules` будут:

- `velero:v0.1.0` (бандл)
- `velero/release:v0.1.0`
- `velero/release:alpha`

## 2. Подключение в DKP

Применить в кластере:

```bash
d8 k apply -f examples/install-cluster.yaml
```

Файл подключает `ModuleSource`, `ModuleUpdatePolicy` и `ModuleConfig velero`.

⚠️ **Важно**: применять поэтапно или через прилагаемый `examples/install.sh`.
DKP должен сначала подтянуть модуль из реестра (~30 сек), и только потом
применяется `ModuleConfig`. См. файл — там оба варианта.

## 3. Минимальная конфигурация

Полный пример — в [examples/install-cluster.yaml](../examples/install-cluster.yaml).
Минимально нужны:

```yaml
apiVersion: deckhouse.io/v1alpha1
kind: ModuleConfig
metadata:
  name: velero
spec:
  enabled: true
  version: 1
  source: dmitrpopkov
  updatePolicy: velero-policy
  settings:
    ingress:
      host: velero.example.com
      ingressClassName: nginx
    https:
      mode: CertManager
      certManager:
        clusterIssuerName: letsencrypt
    auth:
      enabled: true
      allowedGroups:
        - velero-admins
    s3Backends:
      - name: primary
        default: true
        bucket: velero-backups
        region: us-east-1
        s3Url: https://s3.example.com
        s3ForcePathStyle: true
        accessKey: AKIAxxxxxxxx
        secretKey: SECRETxxxxxx
    nodeAgent:
      enabled: true
      uploaderType: kopia
```

## 4. Проверка

```bash
# Поды модуля
d8 k get pods -n d8-velero

# Состояние BackupStorageLocation (должен быть Available)
d8 k get backupstoragelocation -n d8-velero

# DexClient зарегистрирован?
d8 k get dexclient -n d8-velero velero-ui

# Ingress
d8 k get ingress -n d8-velero
```

## 5. Создание первого бэкапа

```bash
# Через CLI velero (нужно поставить локально)
velero backup create my-first-backup --include-namespaces my-app

# Или через UI: открыть https://velero.example.com → войти через Dex
```

## 6. Несколько BSL

Просто перечислите их в `s3Backends`:

```yaml
s3Backends:
  - name: primary
    default: true
    bucket: backups-prod
    region: ru-central-1
    s3Url: https://s3.cloud.ru
    accessKey: ...
    secretKey: ...
  - name: dr
    bucket: backups-dr
    region: us-east-1
    s3Url: https://s3.amazonaws.com
    s3ForcePathStyle: false
    accessKey: ...
    secretKey: ...
```

При создании бэкапа можно явно указать BSL:

```bash
velero backup create dr-backup --storage-location dr --include-namespaces my-app
```

## Доступ к UI

`https://<ingress.host>` → Dex login → попадание в Dashboard Velero UI.

В отсутствие Dex (`auth.enabled: false`) — локальная auth: пользователь
`admin`, пароль автоматически сгенерирован и лежит в Secret
`d8-velero/velero-ui-config` (ключ `ADMIN_PASSWORD`):

```bash
d8 k get secret -n d8-velero velero-ui-config \
  -o jsonpath='{.data.ADMIN_PASSWORD}' | base64 -d
```
