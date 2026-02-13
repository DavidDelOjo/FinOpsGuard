Diseño Técnico (1 página) — Agente FinOps Guard con Strands (Teams)

Objetivo
Reducir gasto cloud y detectar anomalías con recomendaciones accionables semanales para equipos de Ingeniería y Finanzas.

Alcance MVP (4 semanas)

AWS como proveedor inicial (Cost Explorer + CloudWatch).
Detección diaria de anomalías por servicio/cuenta/tag.
Recomendaciones automáticas con ahorro estimado mensual.
Reporte semanal por Microsoft Teams y correo.
Dashboard básico (top gasto, anomalías, oportunidades).
Arquitectura (Strands, Python)
Patrón Graph con nodos deterministas + LLM para análisis y priorización.

IngestNode: obtiene costos (90 días), uso y metadatos de recursos.
NormalizeNode: normaliza a esquema común (date, account, service, tag, cost_usd).
AnomalyNode: detecta desvíos (EWMA + z-score) por dimensión.
InsightNode (LLM): explica causa probable y severidad con evidencia.
ActionNode (LLM + reglas): propone acciones (rightsizing, Savings Plans/RI, lifecycle, idle resources).
ReportNode: genera resumen ejecutivo y backlog técnico.
NotifyNode: envía resultados por Teams/email y opcionalmente crea ticket.
Flujo
Scheduler (daily/weekly) -> Ingest -> Normalize -> Anomaly -> Insight -> Action -> Report -> Notify

Herramientas (tools)

aws_cost_tool: Cost Explorer, Budgets, Compute Optimizer.
metrics_tool: CloudWatch.
inventory_tool: inventario EC2/RDS/EBS/S3.
notify_tool: Microsoft Teams (Webhook o Graph API) + SMTP/Email.
ticket_tool (opcional): Jira/Linear.
policy_tool: reglas de negocio (exclusiones, entornos críticos, ownership tags).
Esquema de datos mínimo

daily_costs: serie temporal por servicio/cuenta/tag.
anomalies: fecha, dimensión, delta_abs, delta_pct, score, severidad.
recommendations: acción, recurso, ahorro_estimado_usd, esfuerzo, riesgo.
reports: snapshot semanal y estado de ejecución.
Prompts clave

Insight: “Explica anomalía solo con datos adjuntos; devuelve hipótesis, evidencia y confianza.”
Action: “Propón máximo 5 acciones priorizadas por ahorro/riesgo/esfuerzo; incluye paso operativo verificable.”
Guardrails: sin automatizar cambios destructivos; si faltan datos, marcar “evidencia insuficiente”.
KPIs

Ahorro identificado (USD) y ahorro realizado (USD).
% de anomalías con causa válida.
Tiempo medio detección -> acción.
Cobertura de tagging (owner, env, cost_center).
Seguridad y gobierno

IAM de solo lectura para ingesta; escritura solo en notificaciones/tickets.
Secrets en AWS Secrets Manager.
Trazabilidad por nodo (inputs, outputs, decisiones).
Exclusiones por cuentas críticas y ventanas de cambio.
Plan de implementación (7 días)

Definir cuentas AWS, tags obligatorios y umbrales.
Implementar IngestNode + NormalizeNode y validar calidad de datos.
Implementar AnomalyNode con baseline de 30 días.
Implementar InsightNode con validación de evidencia.
Implementar ActionNode con catálogo FinOps.
Implementar ReportNode + envío por Teams/email.
Pruebas end-to-end, tuning y despliegue controlado.