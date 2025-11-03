#!/usr/bin/env bash
set -euo pipefail

# ----------------------------
# Parse arguments
# ----------------------------
inConsole="false"

# Support either --inConsole=True/False or positional argument true/false
if [[ $# -ge 1 ]]; then
    arg="$1"
    if [[ "$arg" =~ ^(--inConsole=)?[Tt]rue$ ]]; then
        inConsole="true"
    fi
fi

# ----------------------------
# Setup
# ----------------------------
DEST_DIR="$HOME/test"
mkdir -p "$DEST_DIR"
echo "Logs will be saved in $DEST_DIR"

containers=$(docker ps -aq)
echo "Found containers: $containers"

# ----------------------------
# MODE 1: default (from mounted volumes)
# ----------------------------
if [[ "$inConsole" == "false" ]]; then
    echo "--- Running in MOUNT MODE ---"
    for cid in $containers; do
        echo "Processing container $cid..."

        CONTAINER_LOG="/gns3volumes/app/logs/log.txt"
        CONTAINER_CONFIG="/gns3volumes/app/logs/push_config.toml"

        # Check if both files exist inside container
        log_exists=$(docker exec "$cid" sh -c "[ -f $CONTAINER_LOG ] && echo yes || echo no" || echo no)
        config_exists=$(docker exec "$cid" sh -c "[ -f $CONTAINER_CONFIG ] && echo yes || echo no" || echo no)

        if [[ "$log_exists" == "yes" && "$config_exists" == "yes" ]]; then
            echo "Found log.txt and push_config.toml in container $cid"

            node_idx=$(docker exec "$cid" sh -c "grep -E '^NODE_IDX' $CONTAINER_CONFIG | awk -F'=' '{gsub(/ /,\"\",\$2); print \$2}'" || true)
            [[ -z "$node_idx" ]] && node_idx="$cid"

            docker cp "$cid:$CONTAINER_LOG" "$DEST_DIR/${node_idx}_log.txt"

            echo "Copied data from container $cid -> $DEST_DIR/${node_idx}_*.txt"
        else
            echo "Files not found in container $cid: log=$log_exists, config=$config_exists"
        fi
    done

# ----------------------------
# MODE 2: in-console (live reading)
# ----------------------------
else
    echo "--- Running in CONSOLE MODE ---"
    for cid in $containers; do
        echo "Processing container $cid..."

        # Paths inside container
        LOG_PATH="/app/logs/log.txt"
        CONFIG_PATH="/app/push_config.toml"

        # Check if both files exist in container
        log_exists=$(docker exec "$cid" sh -c "[ -f $LOG_PATH ] && echo yes || echo no" || echo no)
        config_exists=$(docker exec "$cid" sh -c "[ -f $CONFIG_PATH ] && echo yes || echo no" || echo no)

        if [[ "$log_exists" == "yes" && "$config_exists" == "yes" ]]; then
            echo "Found log.txt and push_config.toml in container $cid"

            node_idx=$(docker exec "$cid" sh -c "grep -E '^NODE_IDX' $CONFIG_PATH | awk -F'=' '{gsub(/ /,\"\",\$2); print \$2}'" || true)
            [[ -z "$node_idx" ]] && node_idx="$cid"

            docker exec "$cid" cat "$LOG_PATH" > "$DEST_DIR/${node_idx}_log.txt"

            echo "Copied live data from container $cid -> $DEST_DIR/${node_idx}_*.txt"
        else
            echo "Files not found in container $cid: log=$log_exists, config=$config_exists"
        fi
    done
fi

echo "--- All logs and configs collected in $DEST_DIR ---"
