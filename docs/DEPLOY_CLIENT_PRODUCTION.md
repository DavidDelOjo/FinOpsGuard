# FinOps Guard - Guia de implementacion en cuenta cliente (Produccion)

Este documento describe como desplegar FinOps Guard en una cuenta AWS de cliente de forma segura y operable.

## 1. Modelo de despliegue recomendado

Usa **ejecucion dentro de la cuenta del cliente** (no en tu cuenta) para evitar problemas de acceso y compliance.

Arquitectura minima:
- `EventBridge Scheduler` (disparo diario/semanal)
- `ECS Fargate` o `Lambda` (ejecucion del script)
- `Secrets Manager` (webhook Teams y secretos)
- `CloudWatch Logs` (auditoria y troubleshooting)

## 2. Prerrequisitos

### 2.1 Acordar alcance con cliente
- Cuentas/OU a analizar (single-account o AWS Organizations).
- Canal Teams destino del reporte.
- Frecuencia: diaria, semanal o ambas.
- Horario de ejecucion (zona horaria de negocio).

### 2.2 Accesos necesarios
- Permiso para crear recursos en AWS del cliente.
- Permisos de lectura de costes:
  - `ce:GetCostAndUsage`
  - `ce:GetDimensionValues` (opcional, recomendado)
  - `organizations:ListAccounts` (si multi-cuenta)
- Permisos para logs/secrets/scheduler.

## 3. Preparacion del codigo

En tu repo local:

```bash
cd /ruta/al/repo/FinOpsGuard
cp .env.example .env
# NO subir .env al repositorio
```

Asegura que el codigo esta en rama principal y versionado:

```bash
git checkout main
git pull
git tag v0.1.0
```

## 4. Crear webhook de Teams del cliente

En Teams (canal del cliente):
1. Crear flujo tipo "Enviar alertas de webhook a un canal".
2. Copiar la URL de webhook generada.
3. Guardarla en AWS Secrets Manager (no en codigo):

```bash
aws secretsmanager create-secret \
  --name finopsguard/teams_webhook_url \
  --description "Teams webhook for FinOps Guard reports" \
  --secret-string 'https://...'
```

## 5. Imagen de ejecucion (contenedor)

Construye y publica imagen en ECR del cliente:

```bash
aws ecr create-repository --repository-name finopsguard || true

aws ecr get-login-password | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com

docker build -t finopsguard:0.1.0 .
docker tag finopsguard:0.1.0 <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/finopsguard:0.1.0
docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/finopsguard:0.1.0
```

## 6. IAM de produccion (minimo)

Crear un rol de ejecucion `FinOpsGuardExecutionRole` con permisos:
- Cost Explorer lectura (`ce:GetCostAndUsage`, `ce:GetDimensionValues`).
- Logs (`logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`).
- Secrets Manager lectura del secreto `finopsguard/teams_webhook_url`.
- (Opcional) `kms:Decrypt` si el secreto usa KMS customer-managed key.

## 7. Variables de entorno en runtime

Configura variables en tarea ECS/Lambda:
- `AWS_REGION=us-east-1`
- `FINOPSGUARD_USE_MOCK_DATA=false`
- `TEAMS_WEBHOOK_SECRET_ARN=arn:aws:secretsmanager:...:secret:finopsguard/teams_webhook_url`

Nota: en produccion evita pasar `TEAMS_WEBHOOK_URL` en texto plano.

## 8. Ejecucion programada

### Opcion A: EventBridge + ECS Fargate
- Crear Task Definition con imagen ECR.
- Comando contenedor: `python scripts/run_weekly.py`.
- Scheduler semanal (ejemplo lunes 08:00 UTC).

### Opcion B: EventBridge + Lambda (si empaquetas app para Lambda)
- Menor coste operativo en cargas pequenas.
- Menor flexibilidad que contenedor para futuras extensiones.

## 9. Prueba de humo (go-live)

1. Ejecutar una corrida manual con mock:

```bash
FINOPSGUARD_USE_MOCK_DATA=true python scripts/run_weekly.py
```

2. Verificar tarjeta en Teams.
3. Ejecutar corrida real:

```bash
FINOPSGUARD_USE_MOCK_DATA=false python scripts/run_weekly.py
```

4. Verificar logs en CloudWatch y confirmar estado `exit code 0`.

## 10. Hardening y operacion

- Rotar webhook Teams cada 90 dias (o politica cliente).
- Alertar fallos de ejecucion (CloudWatch Alarm + email/Teams).
- Versionar despliegues por tag de imagen (`v0.1.0`, `v0.1.1`, ...).
- Mantener entorno `staging` antes de `production`.
- Crear runbook de incidencia (fallo CE, fallo webhook, timeout).

## 11. Checklist final de entrega al cliente

- [ ] Repositorio y version entregada.
- [ ] Rol IAM con minimo privilegio validado.
- [ ] Secreto Teams cargado en Secrets Manager.
- [ ] Scheduler activo y probado.
- [ ] Dashboard/logs y alarmas configuradas.
- [ ] Evidencia de prueba de humo compartida.
- [ ] Plan de soporte y mantenimiento acordado.

## 12. Comandos utiles de troubleshooting

Ver ejecucion local:

```bash
python scripts/run_weekly.py
```

Validar acceso Cost Explorer:

```bash
python - <<'PY'
import boto3
from datetime import date, timedelta
ce = boto3.client("ce", region_name="us-east-1")
end = date.today(); start = end - timedelta(days=30)
r = ce.get_cost_and_usage(
    TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
    Granularity="DAILY",
    Metrics=["UnblendedCost"],
    GroupBy=[{"Type":"DIMENSION","Key":"LINKED_ACCOUNT"},{"Type":"DIMENSION","Key":"SERVICE"}],
)
print("ResultsByTime:", len(r.get("ResultsByTime", [])))
PY
```

Validar webhook Teams:

```bash
python - <<'PY'
import json, os, requests
url = os.environ["TEAMS_WEBHOOK_URL"]
r = requests.post(url, data=json.dumps({"text": "FinOps Guard connectivity test"}), headers={"Content-Type":"application/json"}, timeout=10)
print(r.status_code, r.text[:200])
PY
```
