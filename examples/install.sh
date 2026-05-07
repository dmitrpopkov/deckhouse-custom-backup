#!/usr/bin/env bash
# Поэтапная установка модуля velero в DKP с ожиданием появления модуля
# в реестре кластера.
set -euo pipefail

KUBECTL="${KUBECTL:-d8 k}"
FILE="${1:-install-cluster.yaml}"
MODULE_NAME="${MODULE_NAME:-velero}"

echo "==> [1/4] Применяю ModuleSource + ModuleUpdatePolicy"
awk 'BEGIN{c=0} /^---/{c++} c<3 {print}' "$FILE" | $KUBECTL apply -f -

echo "==> [2/4] Жду пока DKP подтянет модуль ${MODULE_NAME} (до 3 минут)"
for i in {1..36}; do
  if $KUBECTL get module "$MODULE_NAME" >/dev/null 2>&1; then
    echo "    модуль ${MODULE_NAME} появился в кластере"
    break
  fi
  printf "."
  sleep 5
done
echo ""

echo "==> [3/4] Текущее состояние:"
$KUBECTL get modulesource dmitrpopkov 2>/dev/null || true
$KUBECTL get module "$MODULE_NAME" 2>/dev/null || {
  echo "ОШИБКА: модуль ${MODULE_NAME} не появился. Проверьте:"
  $KUBECTL describe modulesource dmitrpopkov
  exit 1
}
$KUBECTL get modulereleases.deckhouse.io 2>/dev/null | grep -E "NAME|${MODULE_NAME}" || true

echo ""
echo "==> [4/4] Применяю ModuleConfig"
awk 'BEGIN{c=0} /^---/{c++} c==3 {print}' "$FILE" | $KUBECTL apply -f -

echo ""
echo "✓ Готово. Контролируем:"
echo "  $KUBECTL get moduleconfig ${MODULE_NAME}"
echo "  $KUBECTL get pods -n d8-velero -w"
echo "  $KUBECTL get backupstoragelocation -n d8-velero"
