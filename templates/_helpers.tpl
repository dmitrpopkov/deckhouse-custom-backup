{{/*
Общие хелперы модуля velero
*/}}

{{- define "velero.namespace" -}}
d8-velero
{{- end -}}

{{- define "velero.labels" -}}
app.kubernetes.io/managed-by: deckhouse
heritage: deckhouse
module: velero
{{- end -}}

{{- define "velero.uiHost" -}}
{{- $ingress := dig "ingress" dict .Values.velero -}}
{{- dig "host" "" $ingress -}}
{{- end -}}

{{- define "velero.dexIssuer" -}}
{{- $internal := dig "internal" dict .Values.velero -}}
{{- dig "dexIssuer" "" $internal -}}
{{- end -}}

{{- define "velero.oidcSecret" -}}
{{- $internal := dig "internal" dict .Values.velero -}}
{{- dig "oidcClientSecret" "" $internal -}}
{{- end -}}

{{- define "velero.uiAdminPassword" -}}
{{- $internal := dig "internal" dict .Values.velero -}}
{{- dig "uiAdminPassword" "" $internal -}}
{{- end -}}

{{- define "velero.authEnabled" -}}
{{- $auth := dig "auth" dict .Values.velero -}}
{{- $enabled := dig "enabled" true $auth -}}
{{- $enabled -}}
{{- end -}}
