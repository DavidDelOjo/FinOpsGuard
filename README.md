# FinOps Guard

FinOps Guard is a Strands-oriented multi-node cost monitoring agent for AWS.

It detects cloud spend anomalies, generates remediation recommendations, and publishes weekly reports to Microsoft Teams and email.

## MVP Scope
- AWS cost and usage ingest (90-day window)
- Daily anomaly detection by account/service/tag
- LLM-backed insights and action recommendations
- Weekly reports to Teams and email

## Project Layout
- `finopsguard/graph.py`: orchestrates the pipeline nodes
- `finopsguard/models.py`: shared data contracts
- `finopsguard/tools/notify_teams.py`: Teams webhook notifier
- `finopsguard/prompts/`: prompt templates for insight and action stages
- `config.yaml`: runtime configuration
- `poc/docker/`: local proof-of-concept mode
- `prod/lambda/`: production deployment mode (AWS Lambda + scheduler)

## Quick Start
1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -e .`
3. Copy environment variables:
   - `cp .env.example .env`
   - Set `TEAMS_WEBHOOK_URL` in `.env` with your Teams webhook URL.
4. Run local weekly flow:
   - `python scripts/run_weekly.py`

## Notes
- This is an implementation skeleton ready to integrate real AWS data tools and your selected LLM provider.
- No destructive actions are automated.
- Production deployment guide for client accounts: `docs/DEPLOY_CLIENT_PRODUCTION.md`
- POC Docker runbook: `docs/POC_DOCKER.md`
- Lambda production runbook: `docs/DEPLOY_LAMBDA_PROD.md`
