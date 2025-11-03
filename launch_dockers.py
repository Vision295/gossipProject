import docker
from gns3fy import Gns3Connector, Project, Node


# 1️⃣ Connect to your GNS3 server
server = Gns3Connector("http://localhost:3080")

# 2️⃣ Load your project
project = Project(name="testdocker", connector=server)
project.get()

data = {
      "name": "gossip_env",
      "template_id": "d006d8f3-6408-4d44-867c-953cca5422d3",
      "x": 100,
      "y": 100,
      "compute_id": "local",  # default GNS3 compute
      "properties": {"environment": "ENV1=1"}
}

def create_node(project, server, data):

      # 5️⃣ Create the node
      new_node = Node(project_id=project.project_id, connector=server, **data)
      new_node.create()
      print(f"✅ Created node '{new_node.name}' with ID: {new_node.node_id}")
      return new_node



def get_id(nameId:str):
      return nameId.split(":")[1].strip()

class DockerEdit:

      def __init__(self, name:str, retriever:dict) -> None:
            server = Gns3Connector("http://localhost:3080")
            self.project = Project(name=name, connector=server)
            self.project.get() 
            self.project_id = self.project.project_id
            self.retriever = retriever

            self.dockerClient       = docker.from_env()
            self.dockerContainers   = []

      def retrieve_topology(self):
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

            """
            self.dockerClient.containers.get()
            exec_result = container.exec_run(command)
            """
            ...




node = create_node(project, server, data)
node.get()
