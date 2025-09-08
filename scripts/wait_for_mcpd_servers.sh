# wait_for_mcpd_servers.sh
#
# Checks the health of MCP servers run by mcpd.
# - hits the mcpd API to check the health of all servers
# - repeats this every $interval seconds until $timeout is reached
# - if all servers are ok before $timeout, returns 0, 1 otherwise

timeout=20
elapsed=0
interval=2

URL="http://localhost:8090/api/v1/health/servers"

while [ $elapsed -lt $timeout ]; do
    response=$(curl -s --fail --connect-timeout $timeout $URL 2>/dev/null)
    if [ $? -eq 0 ] && [ "$(echo "$response" | jq '.servers | all(.status == "ok")' 2>/dev/null)" = "true" ]; then
        echo "All servers are up!"
        exit 0
    fi
    echo "Waiting for servers... (${elapsed}s/${timeout}s)"
    sleep $interval
    elapsed=$((elapsed + interval))
done

echo "Timeout: Servers not ready after ${timeout} seconds"
exit 1
