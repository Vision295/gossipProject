import docker
from gns3fy import Gns3Connector, Project, Node


# 1️⃣ Connect to your GNS3 server
server = Gns3Connector("http://localhost:3080")

# 2️⃣ Load your project
project = Project(name="testdocker", connector=server)
project.get()

data = {
      "name": "gossip_base",
      "template_id": "d006d8f3-6408-4d44-867c-953cca5422d3",
      "x": 100,
      "y": 100,
      "compute_id": "local",  # default GNS3 compute
}

def create_node(project, server, data):

      # 5️⃣ Create the node
      new_node = Node(project_id=project.project_id, connector=server, **data)
      new_node.create()
      print(f"✅ Created node '{new_node.name}' with ID: {new_node.node_id}")

create_node(project, server, data)
