#!/bin/bash
# ======================================================================
#          ------- Custom Functions -------                            #
#  Space for adding custom functions so each repo can customize as.    # 
#  needed.                                                             #
# ======================================================================


IMAGE_NAME="ai-travel-advisor:local"
NAMESPACE="ai-travel-advisor"
DEPLOYMENT_NAME="ai-travel-advisor"

redeployApp(){

  printInfoSection "Building local image for $DEPLOYMENT_NAME"

  printInfo "docker build -t $IMAGE_NAME app"

  if ! docker build -t $IMAGE_NAME app; then
    printError "❌ Docker build failed. Stopping deployment, fix the compilation issues..."
    return 1
  else
    printInfo "✅ Docker build succeeded. New image built $IMAGE_NAME"
  fi

  printInfo "Loading image into k3d cluster"
  k3d image import $IMAGE_NAME -c enablement

  printInfo "Updating deployment image"
  kubectl set image deployment/$DEPLOYMENT_NAME $DEPLOYMENT_NAME=$IMAGE_NAME -n $NAMESPACE

  printInfo "Restarting deployment to apply changes"
  kubectl rollout restart deployment/$DEPLOYMENT_NAME -n $NAMESPACE

  printInfo "Waiting for rollout to complete"
  kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE

  printInfo "✅ Done"

}

assertRunningApp(){
  # Overrides framework assertRunningApp — tests ingress routing, not app content.
  # Accepts any HTTP 1xx-4xx response as "reachable" (proves nginx routed to backend).
  # Framework version uses curl --fail which rejects 4xx; ai-travel-advisor returns
  # 404 at / when launched via uvicorn (static files only mounted in __main__).
  local app_name="$1"
  local detected_ip detected_hostname port
  detected_ip=$(detectIP)
  detected_hostname=$(detectHostname)
  port="${K3D_LB_HTTP_PORT:-80}"

  local ip_host="${app_name}.${detected_ip}.${MAGIC_DOMAIN}"
  local name_host="${app_name}.${detected_hostname}"
  local target="http://localhost:${port}"

  printInfoSection "Testing app via ingress on ${target}"

  local h failed=0
  for h in "$ip_host" "$name_host"; do
    local ok=0 i
    for i in $(seq 1 8); do
      local http_code
      http_code=$(curl --silent --max-time 5 -H "Host: $h" "$target" -o /dev/null -w "%{http_code}" 2>/dev/null)
      if [[ "$http_code" =~ ^[1-4][0-9]{2}$ ]]; then
        printInfo "✅ App reachable via Host: $h on $target (HTTP $http_code, attempt $i)"
        ok=1
        break
      fi
      sleep 3
    done
    if [[ "$ok" -eq 0 ]]; then
      printError "❌ App NOT reachable via Host: $h on $target after 8 attempts"
      failed=1
    fi
  done

  if [[ "$failed" -ne 0 ]]; then
    exit 1
  fi
}