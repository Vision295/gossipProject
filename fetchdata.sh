#!/usr/bin/env bash
set -euo pipefail

# Folder to save logs
DEST_DIR="$HOME/test"
mkdir -p "$DEST_DIR"
echo "Logs will be saved in $DEST_DIR"

# Get all containers (active and inactive)
containers=$(docker ps -aq)
echo "Found containers: $containers"

for cid in $containers; do
    echo "Processing container $cid..."

    # Inspect the container to find mounted volumes
    docker inspect "$cid" --format '{{range .Mounts}}{{.Source}}:{{.Destination}}{{"\n"}}{{end}}' | while IFS= read -r mount; do
        [[ -z "$mount" ]] && continue
        host_path="${mount%%:*}"
        container_path="${mount#*:}"
        echo "Found mount: Host=$host_path -> Container=$container_path"

        # Check for log and config files inside the host path
        log_file="$host_path/log.txt"
        config_file="$host_path/push_config.toml"

        echo "Checking for files: $log_file and $config_file"
        if [[ -f "$log_file" && -f "$config_file" ]]; then
            # Extract NODE_IDX from push_config.toml
            node_idx=$(grep -E '^NODE_IDX' "$config_file" | awk -F'=' '{gsub(/ /,"",$2); print $2}')
            if [[ -n "$node_idx" ]]; then
                echo "Found NODE_IDX=$node_idx in $config_file"
                cp "$log_file" "$DEST_DIR/${node_idx}.txt"
                echo "Copied $log_file -> $DEST_DIR/${node_idx}.txt"
            else
                echo "NODE_IDX not found in $config_file"
            fi
        else
            echo "Files not found in this mount."
        fi
    done
done

echo "All logs collected in $DEST_DIR"
