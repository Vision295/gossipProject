from tokenize import tabsize
import docker
from docker.models.containers import Container
import time
import os
import re
import json
from fetch_data import fetch_data
from generator import *
from cleanup import full_cleanup
from gns3fy import Gns3Connector, Project 


"""
      Try to automate the experiences : 
            - load all docker containers then shutdown then reload
            - change the links to see differences in convergence time
            - change the number of pcs
            - change the size of the file
"""
HOME = "/run/media/theophile/Windows/Users/theop/Documents/_Perso/_Etudes/_INSA/_4TC1/networksProject/code/results"
def new_experience(experience_type:str) -> dict:
      """we consider the count of all experiences to differenciate the fetches of 
      data in different directories
      
      :param experience_type: the type of experience we consider
      :type str: String
      :return: the full data of all tracks updated
      :rtype: dict
      """

      # Read current number and update it
      with open("json/exp_count.json", "r") as f:
            exp = json.load(f)
            exp[experience_type] += 1
      with open("json/exp_count.json", "w") as f:
            json.dump(exp, f)

      dest_dir = os.path.expanduser(HOME + f"/{exp[experience_type]}") 
      os.makedirs(dest_dir, exist_ok=True)
      with open("json/intent.json", "r") as f:
            data = json.load(f)
      with open(f"results/{exp[experience_type]}/intent.json", "w") as f:
            json.dump(data, f, indent=6)
      return dest_dir


def run_bw_reduction(bandwidth:float=50):
      client = docker.from_env()
      container_list:list[Container] = client.containers.list(filters={"status": "running"})
      for container in container_list:
            if is_switch(container):
                  print(f"→ Start the BW reduction on SWITCH {container.name}")
                  # container.exec_run(script, user="root", detach=True)
                  for i in range(0, 15):
                        try:
                              container.exec_run(f"ovs-vsctl set interface eth{i} ingress_policing_rate={bandwidth}", user="root", detach=True)
                              time.sleep(0.01)
                              container.exec_run(f"ovs-vsctl set interface eth{i} ingress_policing_burst=0", user="root", detach=True)
                              time.sleep(0.01)
                              print(f"  ✅ Started gossip in {container.name}")
                        except Exception as e:
                              print(f"  ⚠️ Failed in {container.name}: {e}")
            else:
                  try:
                        container.exec_run(f"tc qdisc add dev eth0 root handle 1: htb default 1", user="root", detach=True)
                        time.sleep(0.01)
                        container.exec_run(f"tc class add dev eth0 parent 1: classid 1:1 htb rate {bandwidth}mbit ceil {bandwidth}mbit", user="root", detach=True)
                        time.sleep(0.01)
                        print(f"  ✅ Started gossip in {container.name}")
                  except Exception as e:
                        print(f"  ⚠️ Failed in {container.name}: {e}")

def start_gossip(container_list:list[Container], bw:int):
      """starts the gossip protocol by running the ./entrypoint.sh command on all containers

      :param container_list: list of all the container nodes on my gns3 project
      :type container_list: list[Container]
      """
      # Step 1: Start gossip
      sender = container_list[0]
      for container in container_list:
            if is_switch(container):
                  node_idx = 1
            else:
                  node_idx = find_node_idx(container)
            if node_idx != 0:
                  try:
                        print(f"→ Starting gossip sequence in {container.name}")
                        # container.exec_run(f"tc qdisc add dev eth0 root handle 1: htb default 1", user="root", detach=True)
                        # time.sleep(0.5)
                        # container.exec_run(f"tc class add dev eth0 parent 1: classid 1:1 htb rate {bw}mbit ceil {bw}mbit", user="root", detach=True)
                        # time.sleep(0.5)
                        container.exec_run("bash -c 'cd /app && ./entrypoint.sh'", user="root", detach=True)
                        print(f"  ✅ Started gossip in {container.name}")
                  except Exception as e:
                        print(f"  ⚠️ Failed in {container} curl http://localhost:3080/v2/version.name: {e}")
            else:
                  sender = container
      try:
            # container.exec_run(f"tc qdisc add dev eth0 root handle 1: htb default 1", user="root", detach=True)
            # time.sleep(0.5)
            # sender.exec_run(f"tc class add dev eth0 parent 1: classid 1:1 htb rate {bw}mbit ceil {bw}mbit", user="root", detach=True)
            # time.sleep(0.5)
            sender.exec_run("bash -c 'cd /app && ./entrypoint.sh'", user="root", detach=True)
            print(f"  ✅ Started gossip in {sender.name}")
      except Exception as e:
            print(f"  ⚠️ Failed in {sender.name}: {e}")


is_switch = lambda container: container.exec_run("which ovs-vsctl", user="root").exit_code == 0




def find_node_idx(container):
      # Get push_config.toml
      config_result = container.exec_run("cat /app/push_config.toml", user="root")
      config_content = config_result.output.decode(errors="ignore")

      # Extract NODE_IDX (e.g. NODE_IDX = 1)
      match = re.search(r"NODE_IDX\s*=\s*(\S+)", config_content)
      node_idx = match.group(1).strip() if match else container.name
      return node_idx
      

def fetch_rename_logs(container: Container, dest_dir):
      """fetches the log file in a given container and stores it in the corresponding directory
      renaming is based on the content of the push_config.toml file

      :param container: container of a node in gns3
      :type container: Container
      """
      print(f"→ Fetching log and config from {container.name}")


      # Get log content
      if (is_switch(container)) : 
            print("switch")
            return
      print("not switch")
      log_result = container.exec_run("cat /app/log.txt", user="root")
      log_content = log_result.output.decode(errors="ignore")

      node_idx = find_node_idx(container)

      # Save log to file
      dest_path = os.path.join(dest_dir, f"{node_idx}.txt")
      with open(dest_path, "w") as f:
            f.write(log_content)
            print(f"  ✅ Saved {dest_path}")



def run_gossip_sequence(wait_seconds: int = 60, bandwidth:int = 50, dest_dir=""):
      """runs the full gossip sequence for 60 seconds then fetch all data

      :param wait_seconds: amount of time to wait in between the launch of all entrypoints and the fetch of the data, defaults to 60
      :type wait_seconds: int, optional
      """
      # get docker env
      client = docker.from_env()
      containers:list[Container] = client.containers.list(filters={"status": "running"})

      print(f"Found {len(containers)} running containers")
      start_gossip(containers, bandwidth)

      print(f"⏳ Waiting {wait_seconds} seconds before fetching data ...")
      time.sleep(wait_seconds)
      
      for container in containers:
            try:
                  fetch_rename_logs(container, dest_dir)
            except Exception as e:
                  print(f"  ⚠️ Failed fetching from {container.name}: {e}")

      print("🎯 All logs collected and saved in", dest_dir)


def run_experiment(filename, data):
      name = filename

      full_cleanup(name)

      topo = TopologyGenerator(TopologyType.FULL_MESH, data, name)
      server = Gns3Connector("http://localhost:3080")
      project = Project(name=name, connector=server)
      dest_dir = new_experience("full_mesh")
      project.get()
      for node in project.nodes:
            node.start()

      time.sleep(1)
      run_bw_reduction(data["bandwidth_mbps"])
      run_gossip_sequence(wait_seconds=30, bandwidth=50, dest_dir=dest_dir)
      fetch_data(data)


if __name__ == "__main__":
      with open("json/intent.json", "r") as file:
            data = json.load(file)  # parses JSON into a Python dict or list
      run_experiment("untitled", data)