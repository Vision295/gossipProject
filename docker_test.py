import docker
from docker.models.containers import Container
import time
import os
import re
import json

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
            json.dump(data, f)
            return data

experiences = new_experience("full_mesh")

# retrieves the results 
home = "/run/media/theophile/Windows/Users/theop/Documents/_Perso/_Etudes/_INSA/_4TC1/networksProject/code/results"
DEST_DIR = os.path.expanduser(home + f"/{experiences['full_mesh']}") 
os.makedirs(DEST_DIR, exist_ok=True)

def run_gossip_sequence(wait_seconds: int = 60):
      client = docker.from_env()
      containers:list[Container] = client.containers.list(filters={"status": "running"})

      print(f"Found {len(containers)} running containers")

      # Step 1: Start gossip
      for c in containers:
            print(f"→ Starting gossip sequence in {c.name}")
            try:
                  c.exec_run("bash -c 'cd /app && ./entrypoint.sh'", user="root")
                  print(f"  ✅ Started gossip in {c.name}")
            except Exception as e:
                  print(f"  ⚠️ Failed in {c.name}: {e}")

      # Step 2: Wait
      print(f"⏳ Waiting {wait_seconds} seconds before running exitpoint.sh ...")
      time.sleep(wait_seconds)

      # Step 4: Fetch and rename logs
      for c in containers:
            try:
                  print(f"→ Fetching log and config from {c.name}")

                  # Get push_config.toml
                  config_result = c.exec_run("cat /app/push_config.toml", user="root")
                  config_content = config_result.output.decode(errors="ignore")

                  # Extract NODE_IDX (e.g. NODE_IDX = 1)
                  match = re.search(r"NODE_IDX\s*=\s*(\S+)", config_content)
                  node_idx = match.group(1).strip() if match else c.name
                  print(f"  NODE_IDX = {node_idx}")

                  # Get log content
                  log_result = c.exec_run("cat /app/log.txt", user="root")
                  log_content = log_result.output.decode(errors="ignore")

                  # Save log to file
                  dest_path = os.path.join(DEST_DIR, f"{node_idx}.txt")
                  with open(dest_path, "w") as f:
                        f.write(log_content)
                        print(f"  ✅ Saved {dest_path}")

            except Exception as e:
                  print(f"  ⚠️ Failed fetching from {c.name}: {e}")

      print("🎯 All logs collected and saved in", DEST_DIR)

if __name__ == "__main__":
      run_gossip_sequence(wait_seconds=60)
