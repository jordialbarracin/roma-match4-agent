#!/bin/bash
set -e

echo "[ROMA] Starting resident daemon on AMD ROCm environment..."
python3 -m uvicorn src.daemon.server:app --host 127.0.0.1 --port 8000 &
DAEMON_PID=$!

echo "[ROMA] Waiting for daemon health check..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/health > /dev/null; then
        echo "[ROMA] Daemon is healthy and ready for queries."
        break
    fi
    sleep 1
done

# If arguments were provided to entrypoint, execute them
if [ $# -gt 0 ]; then
    exec "$@"
else
    # Keep container alive for evaluation harness execution
    wait $DAEMON_PID
fi
