# Produccion - AWS Lambda (escenario recomendado)

## 1. Resumen de arquitectura
- EventBridge Schedule -> Lambda `finopsguard-weekly`
- Lambda usa Cost Explorer
- Webhook Teams en Secrets Manager
- Logs en CloudWatch

## 2. Prerrequisitos
- AWS CLI y SAM CLI configurados en la cuenta cliente.
- Permisos para desplegar CloudFormation, Lambda, IAM, Events, Logs, Secrets.
- Secret creado con webhook Teams.

## 3. Crear secreto de Teams

```bash
aws secretsmanager create-secret \
  --name finopsguard/teams_webhook_url \
  --description "Teams webhook for FinOps Guard" \
  --secret-string 'https://...'
```

Guarda el ARN que devuelve el comando.

## 4. Build y deploy con SAM
Desde la raiz del repo:

```bash
sam build -t prod/lambda/template.yaml
sam deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name finopsguard-prod \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    FunctionName=finopsguard-weekly \
    ScheduleExpression='cron(0 8 ? * MON *)' \
    TeamsWebhookSecretArn='arn:aws:secretsmanager:REGION:ACCOUNT:secret:finopsguard/teams_webhook_url-XXXX'
```

## 5. Prueba manual

```bash
aws lambda invoke \
  --function-name finopsguard-weekly \
  --payload '{}' \
  /tmp/finopsguard_response.json && cat /tmp/finopsguard_response.json
```

## 6. Operacion
- Cambiar horario semanal: actualizar `ScheduleExpression` con `sam deploy`.
- Rotar webhook: actualiza el secreto en Secrets Manager.
- Revisar fallos: CloudWatch Logs del function.

## 7. Coste esperado
Para una ejecucion semanal corta, Lambda + EventBridge + Logs suele ser significativamente mas barato que ECS siempre encendido.
