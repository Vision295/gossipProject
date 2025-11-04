from gns3fy import Gns3Connector, Project

def get_project_info():
      # 1️⃣ Connect to your GNS3 server
      gns3_server = Gns3Connector("http://localhost:3080")

      # 2️⃣ Get your project by name (or use project_id)
      project = Project(name="test2", connector=gns3_server)
      project.get()  # fetch project data from the server

      # 3️⃣ Load all nodes in this project
      project.get_nodes()

      # 4️⃣ Inspect general project info
      print("=== PROJECT INFO ===")
      print(f"Project Name: {project.name}")
      print(f"Project ID:   {project.project_id}")
      print(f"Path:         {project.path}")
      print(f"Status:       {project.status}")

      # 5️⃣ Iterate through all nodes
      print("\n=== NODE DETAILS ===")
      for node in project.nodes:
            node.get()  # fetch detailed info for each node
            print(f"\nNode Name: {node.name}")
            print(f"  Node ID: {node.node_id}")
            print(f"  Type: {node.node_type}")
            print(f"  Template: {node.template}")
            print(f"  Status: {node.status}")
            print(f"  Compute ID: {node.compute_id}")
            print(f"  Console: {node.console_type} on {node.console_host}:{node.console}")
            print(f"  Coordinates: ({node.x}, {node.y})")
            print(f"  Locked: {node.locked}")
            print(f"  Ports: {node.ports}")
            print(f"  Properties: {node.properties}")
            print(f"  Template ID: {node.template_id}")
            print(f"  Node Directory: {node.node_directory}")


if __name__ == "__main__":
      get_project_info()