import subprocess
import docker
from docker.models.containers import Container
import time
import os
import re
import json
import threading

def new_experience(experience_type:str) -> dict:
      """we consider the count of all experiences to differenciate the fetches of 
      data in different directories
      
      :param experience_type: the type of experience we consider
      :type str: String
      :return: the full data of all tracks updated
      :rtype: dict
      """

      # Read current number and update it
      with open("exp_count.json", "r") as f:
            data = json.load(f)
            data[experience_type] += 1
      with open("exp_count.json", "w") as f:
            json.dump(data, f)
            return data

experiences = new_experience("full_mesh")

# the directory in which to put the results 
home = "/run/media/theophile/Windows/Users/theop/Documents/_Perso/_Etudes/_INSA/_4TC1/networksProject/code/results"
DEST_DIR = os.path.expanduser(home + f"/{experiences['full_mesh']}") 
os.makedirs(DEST_DIR, exist_ok=True)

def exec_entrypoint_in_terminal(container: Container) -> threading.Thread:
      """
      Mimics opening a terminal for each node and running docker exec + entrypoint.sh
      Runs each container's entrypoint in a separate thread (like separate terminals)
      Uses -it flags to ensure proper TTY allocation (just like manual terminal execution)
      """
      def run_in_thread():
            try:
                  print(f"  🔌 Opening terminal session for {container.name}...")
                  
                  # This mimics: docker exec -it <id> bash
                  # Then inside bash: ./entrypoint.sh
                  # The -it flags are CRITICAL - they allocate a pseudo-TTY just like a real terminal
                  result = subprocess.run([
                        "docker", "exec", "-it", container.id,
                        "bash", "-c", "cd /app && ./entrypoint.sh"
                  ], 
                  stdout=subprocess.PIPE,
                  stderr=subprocess.PIPE,
                  text=True,
                  timeout=120  # 2 minute timeout per container
                  )
                  
                  if result.returncode == 0:
                        print(f"  ✅ {container.name} entrypoint completed successfully")
                  else:
                        print(f"  ⚠️ {container.name} entrypoint exit code: {result.returncode}")
                        if result.stderr:
                              print(f"     Error: {result.stderr}")
                  
            except subprocess.TimeoutExpired:
                  print(f"  ⚠️ {container.name} timed out after 120 seconds")
            except Exception as e:
                  print(f"  ⚠️ Failed to run entrypoint in {container.name}: {e}")
      
      # Create and start thread for this container
      thread = threading.Thread(target=run_in_thread, daemon=False)
      thread.start()
      return thread


def start_gossip_parallel(container_list: list[Container]) -> None:
      """
      Mimics opening a terminal for each node and running entrypoint.sh in parallel
      This is exactly like opening multiple terminals and running the command in each one simultaneously
      """
      print(f"\n📡 Starting gossip on all {len(container_list)} containers in parallel...")
      print("(This mimics opening a terminal for each node)")
      
      threads = []
      
      # Start all containers in parallel (like opening multiple terminals)
      for container in container_list:
            thread = exec_entrypoint_in_terminal(container)
            threads.append((container.name, thread))
      
      # Wait for all threads to complete
      print(f"\n⏳ Waiting for all {len(threads)} containers to complete their setup...")
      for container_name, thread in threads:
            thread.join()
            print(f"   ✓ {container_name} thread finished")
      
      print("✅ All containers setup complete!\n")


def find_node_idx(container: Container) -> str:
      """Extracts NODE_IDX from container config"""
      try:
            result = subprocess.run([
                  "docker", "exec", "-i", container.id,
                  "cat", "/app/push_config.toml"
            ], capture_output=True, text=True, check=True, timeout=10)
            
            config_content = result.stdout

            # Extract NODE_IDX (e.g. NODE_IDX = 1)
            match = re.search(r"NODE_IDX\s*=\s*(\S+)", config_content)
            node_idx = match.group(1).strip() if match else container.name
            return str(node_idx)
      except Exception as e:
            print(f"  ⚠️ Failed to find NODE_IDX in {container.name}: {e}")
            return container.name


def fetch_rename_logs(container: Container) -> None:
      """
      Mimics: docker exec <id> cat log.txt
      Then copies the data to the results folder, renaming based on NODE_IDX
      """
      try:
            print(f"→ Fetching log from {container.name}...")
            
            node_idx = find_node_idx(container)
            print(f"  NODE_IDX = {node_idx}")

            # This mimics: docker exec <id> cat /app/log.txt
            result = subprocess.run([
                  "docker", "exec", "-i", container.id,
                  "cat", "/app/log.txt"
            ], capture_output=True, text=True, check=True, timeout=10)
            
            log_content = result.stdout

            # Save log to file in results folder
            dest_path = os.path.join(DEST_DIR, f"{node_idx}.txt")
            with open(dest_path, "w") as f:
                  f.write(log_content)
            print(f"  ✅ Saved to {dest_path}")
            
      except subprocess.CalledProcessError as e:
            print(f"  ⚠️ Failed to fetch log from {container.name}: {e}")
      except Exception as e:
            print(f"  ⚠️ Failed fetching from {container.name}: {e}")


def fetch_all_logs(container_list: list[Container]) -> None:
      """
      Mimics running: docker exec <id> cat log.txt
      on each container, then copying the data to a folder
      """
      print(f"\n📂 Fetching logs from all {len(container_list)} containers...")
      print(f"(Saving to: {DEST_DIR})\n")
      
      for container in container_list:
            fetch_rename_logs(container)
      
      print(f"\n🎯 All logs collected and saved in {DEST_DIR}\n")


def run_gossip_sequence(wait_seconds: int = 60) -> None:
      """
      Runs the full gossip sequence exactly as you do manually:
      1. Open docker exec terminal for each node (in parallel)
      2. Run ./entrypoint.sh on each (simultaneously)
      3. Wait for the gossip protocol to run
      4. Fetch log.txt from each container
      5. Copy data to results folder
      """
      # Get docker env
      client = docker.from_env()
      containers: list[Container] = client.containers.list(filters={"status": "running"})

      print(f"🐳 Found {len(containers)} running containers")
      print("=" * 60)
      
      # Step 1: Start gossip on all containers in parallel (like opening multiple terminals)
      start_gossip_parallel(containers)
      
      # Step 2: Wait for the gossip protocol to run
      print(f"⏳ Waiting {wait_seconds} seconds for gossip protocol to run...")
      time.sleep(wait_seconds)
      
      # Step 3: Fetch all logs
      fetch_all_logs(containers)
      
      print("=" * 60)
      print("✨ Gossip sequence completed!")


if __name__ == "__main__":
      run_gossip_sequence(wait_seconds=60)