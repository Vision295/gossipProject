import json
import docker
from docker.models.containers import Container
from gns3fy import Gns3Connector, Project, Node
from load_simulation import run_gossip_sequence
import re

def get_id(nameId:str) -> str:
      """get id from retriever map

      :param nameId: name and id in a string 
      :type nameId: str
      :return: the id
      :rtype: str
      """
      return nameId.split(":")[1].strip()

class DockerEdit:
      """class to manage every docker edits (should be joinned with load_simulation later)"""

      def __init__(self, project_name:str, retriever:dict) -> None:
            """basic init like in topology + docker initialization

            :param project_name: project name
            :type project_name: str
            :param retriever: retriever dict from json
            :type retriever: dict
            """
            server = Gns3Connector("http://localhost:3080")
            self.project = Project(name=project_name, connector=server)
            self.project.get()  # type: ignore
            self.project_id = self.project.project_id # type: ignore
            self.retriever = retriever

            self.dockerClient       = docker.from_env()
            self.dockerContainers   = []
            self.retrieve_docker_containers()

      def retrieve_topology(self):
            """retrieve from the generated topology and find the docker containers to execute 
            some commands later on"""
            self.switches     = []
            self.pcs          = []
            for switch, pcList in self.retriever.items():
                  self.switches.append(
                        Node(node_id=get_id(switch))
                  )
                  self.pcs.append(map(
                        lambda x: Node(node_id=get_id(x)),
                        pcList
                  ))

      def retrieve_docker_containers(self):
            self.dockerContainers:list[Container] = self.dockerClient.containers.list(filters={"status": "running"})

      def run_cmd_on_each_node(self, cmd:str):
            outputs = []
            for container in self.dockerContainers:
                  outputs.append(
                        str(container.exec_run(cmd, user="root", detach=True).output.decode(error="ignore"))
                  )
            return outputs
            
      def find_node_idx(self, output):
            match = re.search(r"NODE_IDX\s*=\s*(\S+)", output)
            return match.group(0).strip() if match else 0
      

      def start_gossip(self):
            """starts the gossip protocol by running the ./entrypoint.sh command on all containers
            :param container_list: list of all the container nodes on my gns3 project
            :type container_list: list[Container]
            """
            # Step 1: Start gossip
            output = self.run_cmd_on_each_node("cat /app/push_config.toml")
            sender = self.dockerContainers[next((i for i, v in enumerate(output) if self.find_node_idx(v) == 0), 0)]
            self.dockerContainers.remove(sender)
            self.run_cmd_on_each_node("bash -c 'cd /app && ./entrypoint.sh'")


      def fetch_rename_logs(self):

            """fetches the log file in a given container and stores it in the corresponding directory
            renaming is based on the content of the push_config.toml file

            :param container: container of a node in gns3
            :type container: Container
            """
            log_content = self.run_cmd_on_each_node("cat /app/log.txt")
            node_idx = [self.find_node_idx(container) for container in self.dockerContainers]

            # dest_path = os.path.join(DEST_DIR, f"{node_idx}.txt")
            # with open(dest_path, "w") as f:
            #       f.write(log_content)
            #       print(f"  ✅ Saved {dest_path}")


      def run_gossip_sequence(self, wait_seconds: int = 60):
            self.start_gossip()
            return
            self.fetch_rename_logs()
            run_gossip_sequence(wait_seconds)


with open( "json/fullmesh_retrieval_map.json", "r") as f:
      retrieval = json.load(f)

dock = DockerEdit("testTCP", retrieval)
dock.retrieve_topology()
dock.run_gossip_sequence(20)