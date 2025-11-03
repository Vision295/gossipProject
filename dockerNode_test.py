from gns3fy import Gns3Connector, Project, Node

# 1️⃣ Connect to your GNS3 server
server = Gns3Connector("http://localhost:3080")

# 2️⃣ Load your project
project = Project(name="test2", connector=server)
project.get()

# 4️⃣ Define the node using your Docker template
# Template ID for 'gossip1': ca9a07ae-a2d9-4a6f-8e06-cbf3b9668414
node_data = {
    "name": "gossip_node1",
    "template_id": "ca9a07ae-a2d9-4a6f-8e06-cbf3b9668414",
    "x": 100,
    "y": 100,
    "compute_id": "local",  # default GNS3 compute
}

# 5️⃣ Create the node
new_node = Node(project_id=project.project_id, connector=server, **node_data)
new_node.create()
print(f"✅ Created node '{new_node.name}' with ID: {new_node.node_id}")

# 6️⃣ (Optional) Start the node
new_node.start()
print(f"🚀 Started node '{new_node.name}'")
