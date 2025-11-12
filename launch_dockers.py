from json import load
import docker
from gns3fy import Gns3Connector, Project, Node
from load_simulation_multiprocessing import *

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
            self.project.get() 
            self.project_id = self.project.project_id
            self.retriever = retriever

            self.dockerClient       = docker.from_env()
            self.dockerContainers   = []

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
                  self.dockerContainers.append(map(
                        lambda x: self.dockerClient.containers.get(x.properties),
                        pcList
                  )) 

      def run_cmd_on_each_node(self, cmd:str):
            for container in self.dockerContainers:
                  container.exec_run(cmd, user="root")
            

      def run_gossip_sequence(self, wait_seconds: int = 60):
            run_gossip_sequence(wait_seconds)