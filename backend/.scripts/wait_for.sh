#!/bin/bash
# wait_for.sh - Poll a health endpoint until it returns successfully
#
# Usage: ./wait_for.sh <url> [timeout_seconds] [interval_seconds]
#
# Example: ./wait_for.sh http://localhost:8000/health 60 2

set -e

URL="${1:-http://localhost:8000/health}"
TIMEOUT="${2:-60}"
INTERVAL="${3:-2}"

echo "Waiting for $URL to become available..."
echo "Timeout: ${TIMEOUT}s, Check interval: ${INTERVAL}s"

elapsed=0
while [ $elapsed -lt $TIMEOUT ]; do
    if curl -s -f "$URL" > /dev/null 2>&1; then
        echo "✓ Service is ready at $URL"
        exit 0
    fi

    echo "  ... waiting (${elapsed}s/${TIMEOUT}s)"
    sleep $INTERVAL
    elapsed=$((elapsed + INTERVAL))
done

echo "✗ Timeout reached. Service not available at $URL"
exit 1
