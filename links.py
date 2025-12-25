from gns3fy import Gns3Connector, Project, Node, Link

from automation import PROJECT_NAME


"""
test functions to manipulate filters on links : 
      - create_topology for generate a sample test of computers
      - get_project_info to retrieve every links 
      - modify_link to modify a single link filtering attribute

"""
PROJECT_NAME = "link test"

# Connect to local GNS3 server
server = Gns3Connector("http://localhost:3080")


def create_topology(project_name=PROJECT_NAME):
      """
      Create a simple topology with two VPCS and one Ethernet switch.
      Returns the Project object.
      """
      project = Project(name=project_name, connector=server)
      project.get()

      # Templates must exist in your GNS3 installation
      VPCS_TEMPLATE = "VPCS"
      SWITCH_TEMPLATE = "Ethernet switch"

      # Create nodes
      pc1 = Node(name="PC1", project_id=project.project_id, connector=server, template=VPCS_TEMPLATE, x=0, y=0)
      pc2 = Node(name="PC2", project_id=project.project_id, connector=server, template=VPCS_TEMPLATE, x=200, y=0)
      switch = Node(name="Switch", project_id=project.project_id, connector=server, template=SWITCH_TEMPLATE, x=100, y=-100)

      for node in [pc1, pc2, switch]: node.create()

      # Create links
      Link(project_id=project.project_id, connector=server, nodes=[
            {"node_id": pc1.node_id, "adapter_number": 0, "port_number": 0},
            {"node_id": switch.node_id, "adapter_number": 0, "port_number": 0},
      ]).create()

      Link(project_id=project.project_id, connector=server, nodes=[
            {"node_id": pc2.node_id, "adapter_number": 0, "port_number": 0},
            {"node_id": switch.node_id, "adapter_number": 0, "port_number": 1},
      ]).create()

      # Start all nodes
      for node in [pc1, pc2, switch]: node.start()

      print(f"✅ Topology '{project_name}' created successfully.")
      return project


def get_project_info(project):
      """
      Retrieve and display all nodes and links in a project.
      """
      project.get()
      nodes = project.nodes
      links = project.links

      print(f"\n📦 Project: {project.name}")
      print("Nodes:")

      for n in nodes : print(f" - {n.name} ({n.node_id})")
      print("\nLinks:")

      for l in links : print(f" - Link ID: {l.link_id}, Nodes: {[(n['node_id']) for n in l.nodes]}")

      return nodes, links


def modify_link(project, filter_fn, new_attributes):
      """
      Modify a link that matches a filter function.
      filter_fn(link) → bool
      new_attributes → dict of attributes to modify (e.g., {'suspend': True})
      """
      project.get()
      modified_links = []

      for link in project.links:
            if filter_fn(link):
                  print(f"Modifying link {link.link_id} ...")
                  link.update(**new_attributes)
                  modified_links.append(link.link_id)

      if modified_links:
            print(f"✅ Modified links: {modified_links}")
      else:
            print("⚠️ No links matched the filter.")


# Example usage:
if __name__ == "__main__":
      # Create the topology
      proj = create_topology()

      # Retrieve project info
      nodes, links = get_project_info(proj)

      # Example: modify a link (e.g. suspend the first one)
      modify_link(
      proj,
            filter_fn=lambda l: l.link_id == links[0].link_id,
            new_attributes={"suspend": True}
      )
