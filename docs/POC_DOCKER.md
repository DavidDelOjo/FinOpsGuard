# POC Docker Mode

## Objetivo
Ejecutar FinOps Guard manualmente en Docker Desktop para pruebas funcionales.

## Pasos
1. Clona el repo dentro del contenedor de trabajo o monta el volumen.
2. Crea venv e instala:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -e . pytest`
3. Prepara variables:
   - `cp .env.example .env`
   - Configura `TEAMS_WEBHOOK_URL` en `.env`.
4. Ejecuta test:
   - `pytest -q`
5. Ejecuta flujo:
   - `python scripts/run_weekly.py`

## Modos de prueba
- Mock: `FINOPSGUARD_USE_MOCK_DATA=true`
- Real AWS: `FINOPSGUARD_USE_MOCK_DATA=false`

## Notas
- `.env` nunca se sube al repo.
- Si falta webhook, el run no falla; solo omite notificacion Teams.
