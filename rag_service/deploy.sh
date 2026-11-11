#!/usr/bin/env bash
# Deploy this folder to the DATA 790 Azure Container Apps environment. Run it from inside rag_service/ after `az login`.
#
#   ./deploy.sh                 # first deploy and every redeploy
#   BUILD=local ./deploy.sh     # only if cloud builds are blocked (TasksOperationsNotAllowed) — needs Docker Desktop
#
# Reads course.env (the course's Azure settings, from the Canvas zip) and .env (your keys and onyen).
# Both are git-ignored, so none of this ends up in your public repo.
set -euo pipefail

for f in course.env .env; do
  [ -f "$f" ] || { echo "✗ $f not found next to deploy.sh (course.env is in the Canvas zip; .env comes from .env.example)"; exit 1; }
  set -a
  # shellcheck source=/dev/null
  . "./$f"
  set +a
done

: "${AZ_SUBSCRIPTION:?missing from course.env}" "${AZ_RESOURCE_GROUP:?missing from course.env}"
: "${AZ_CONTAINERAPPS_ENV:?missing from course.env}" "${AZ_REGISTRY:?missing from course.env}"
TAG_KEY="${AZ_TAG_KEY:-onyen}"
: "${UNC_AI_API_KEY:?set it in .env}" "${APP_API_KEY:?set it in .env}" "${ONYEN:?set it in .env}"

ONYEN="$(printf '%s' "$ONYEN" | tr '[:upper:]' '[:lower:]')"
if [ "$ONYEN" = "your-onyen" ] || ! [[ "$ONYEN" =~ ^[a-z0-9]{2,24}$ ]]; then
  echo "✗ ONYEN in .env should be your onyen (letters and digits)"; exit 1
fi
if [ "$APP_API_KEY" = "change-me" ]; then
  echo "✗ APP_API_KEY in .env is still the placeholder — make one:  python -c \"import secrets; print(secrets.token_urlsafe(24))\""; exit 1
fi

RG="$AZ_RESOURCE_GROUP"
ACR="$AZ_REGISTRY"
APP="rag-$ONYEN"
IMAGE="$ACR.azurecr.io/$APP:$(date +%Y%m%d-%H%M%S)"
TAGS=("$TAG_KEY=$ONYEN" "course=DATA790")

az account set --subscription "$AZ_SUBSCRIPTION"
az extension add --name containerapp --upgrade --yes --only-show-errors >/dev/null 2>&1 || true

# The environment and registry are shared course infrastructure, created by the instructor.
az containerapp env show -n "$AZ_CONTAINERAPPS_ENV" -g "$RG" --query name -o tsv >/dev/null 2>&1 \
  || { echo "✗ course environment $AZ_CONTAINERAPPS_ENV not found in $RG — post in the Q&A thread"; exit 1; }
ACR_USER=$(az acr credential show -n "$ACR" --query username -o tsv)
ACR_PASS=$(az acr credential show -n "$ACR" --query "passwords[0].value" -o tsv)

echo "→ 1/3 build  $IMAGE"
if [ "${BUILD:-cloud}" = "local" ]; then
  printf '%s' "$ACR_PASS" | docker login "$ACR.azurecr.io" -u "$ACR_USER" --password-stdin >/dev/null
  docker build --platform linux/amd64 -f Dockerfile -t "$IMAGE" ..       # amd64 even on Apple Silicon — Azure runs amd64
  docker push "$IMAGE"
else
  az acr build --registry "$ACR" --image "$IMAGE" --file Dockerfile ..   # builds in Azure; honors .dockerignore
fi

echo "→ 2/3 run    $APP  (in $AZ_CONTAINERAPPS_ENV, tagged ${TAGS[*]})"
if az containerapp show -n "$APP" -g "$RG" --query name -o tsv >/dev/null 2>&1; then
  # redeploy: refresh secrets, roll out the new image as a new revision
  az containerapp secret set -n "$APP" -g "$RG" --only-show-errors \
    --secrets "unc-ai-api-key=$UNC_AI_API_KEY" "app-api-key=$APP_API_KEY" >/dev/null
  az containerapp update -n "$APP" -g "$RG" --only-show-errors --image "$IMAGE" \
    --set-env-vars UNC_AI_API_KEY=secretref:unc-ai-api-key APP_API_KEY=secretref:app-api-key \
    --min-replicas 0 --max-replicas 2 --tags "${TAGS[@]}" >/dev/null
else
  # first deploy: keys go in as secrets and reach the container as env vars by reference — never as plain values
  az containerapp create -n "$APP" -g "$RG" --environment "$AZ_CONTAINERAPPS_ENV" --only-show-errors \
    --image "$IMAGE" --registry-server "$ACR.azurecr.io" \
    --registry-username "$ACR_USER" --registry-password "$ACR_PASS" \
    --ingress external --target-port 8000 --min-replicas 0 --max-replicas 2 \
    --secrets "unc-ai-api-key=$UNC_AI_API_KEY" "app-api-key=$APP_API_KEY" \
    --env-vars UNC_AI_API_KEY=secretref:unc-ai-api-key APP_API_KEY=secretref:app-api-key \
    --tags "${TAGS[@]}" >/dev/null
fi

FQDN=$(az containerapp show -n "$APP" -g "$RG" --query properties.configuration.ingress.fqdn -o tsv)
echo "→ 3/3 live   https://$FQDN"
echo
echo "  health:  curl -s https://$FQDN/health"
echo "  ask:     curl -s -X POST https://$FQDN/ask -H \"X-API-Key: \$APP_API_KEY\" -H 'Content-Type: application/json' -d '{\"question\":\"...\"}'"
echo "  logs:    az containerapp logs show -n $APP -g $RG --follow"
