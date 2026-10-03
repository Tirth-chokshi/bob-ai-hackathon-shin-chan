# Render Demo Deployment

This deploys the app as a password-protected demo. The Render URL is reachable from the internet, but the app and all API routes require HTTP Basic Authentication over Render's HTTPS connection. Share the credentials only with demo viewers.

## Deploy

1. Rotate the IBM Bob API key that was present in the local `src/.env` before using it anywhere else. The container deliberately does not copy `.env`, `data/`, or local virtual environments.
2. In Render, create a new **Blueprint** from this repository and select `render.yaml`.
3. When prompted, set `APP_AUTH_USERNAME`, `APP_AUTH_PASSWORD`, and `BOB_API_KEY`. Enter your IBM Bob API key securely into Render's environment variable prompt so it remains completely hidden and never committed to version control. Set a unique, randomly generated password for basic auth (e.g. generate one locally with `openssl rand -hex 32`).
4. Deploy. Render builds the frontend and Python service from the `Dockerfile`; the `/_health` endpoint is used for health checks.
5. Open the service URL. The browser's Basic Auth prompt should appear before the app loads.

Production mode fails closed: if either authentication variable is missing, the app returns `503` instead of serving the UI or API. Do not remove the auth variables to make the demo easier to access.

## IBM Bob and X API
 
`BOB_API_KEY` is configured as a protected secret in Render (`sync: false` in `render.yaml`), ensuring no credentials are ever exposed in Git repositories or client bundles. The application supports upload, forensic coordination analysis, network graph visualization, timeline clustering, and all cached Bob assessments.

If X search is needed, add `X_BEARER_TOKEN` as a secret environment variable in Render. Never add API keys to `render.yaml`, the Docker image, frontend build variables, or committed files.

## Demo Data Limits

The free Render service has ephemeral storage and may sleep when idle. Uploaded datasets and analysis results can be lost on restart or redeploy. Use only data approved for a shared demo; do not upload confidential investigations or personal data. This configuration is for demonstrations, not operational casework.

The shared Basic Auth credential is a simple demo gate, not per-user identity or audit logging. Use an identity-aware access proxy and persistent, access-controlled storage before handling non-public data.