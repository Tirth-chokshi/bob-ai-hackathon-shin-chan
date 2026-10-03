# Render Demo Deployment

This deploys the app as a password-protected demo. The Render URL is reachable from the internet, but the app and all API routes require HTTP Basic Authentication over Render's HTTPS connection. Share the credentials only with demo viewers.

## Deploy

1. Rotate the IBM Bob API key that was present in the local `src/.env` before using it anywhere else. The container deliberately does not copy `.env`, `data/`, or local virtual environments.
2. In Render, create a new **Blueprint** from this repository and select `render.yaml`.
3. When prompted, set `APP_AUTH_USERNAME` and `APP_AUTH_PASSWORD`. Use a unique, randomly generated password and store it only in Render's environment settings and an approved password manager. For example, generate one locally with `openssl rand -hex 32`.
4. Deploy. Render builds the frontend and Python service from the `Dockerfile`; the `/_health` endpoint is used for health checks.
5. Open the service URL. The browser's Basic Auth prompt should appear before the app loads.

Production mode fails closed: if either authentication variable is missing, the app returns `503` instead of serving the UI or API. Do not remove the auth variables to make the demo easier to access.

## IBM Bob and X API

No `BOB_API_KEY` workaround is needed for the demo: leave it unset. The app still supports upload, coordination analysis, and any cached Bob assessments, but cannot request new Bob classifications. The container does not install IBM Bob Shell, so adding a key to Render alone would not enable inference. X search is also disabled because `X_BEARER_TOKEN` is not configured.

If live Bob or X API access is added later, enter credentials only as Render environment secrets. Never add them to `render.yaml`, the Docker image, frontend build variables, or committed files. Live Bob inference additionally requires a supported server-side Bob CLI installation.

## Demo Data Limits

The free Render service has ephemeral storage and may sleep when idle. Uploaded datasets and analysis results can be lost on restart or redeploy. Use only data approved for a shared demo; do not upload confidential investigations or personal data. This configuration is for demonstrations, not operational casework.

The shared Basic Auth credential is a simple demo gate, not per-user identity or audit logging. Use an identity-aware access proxy and persistent, access-controlled storage before handling non-public data.