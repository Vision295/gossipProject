import json
from gns3fy import Link, Node
from gns3fy import Gns3Connector, Project

from enum import Enum

class TopologyType(Enum):
      CURRENT_MESH = 0
      FULL_MESH = 1
      BUS = 2
      CLUSTERING = 3

# --- Helper: get first free port of a node ---
def get_free_port(node, project):
      used_ports = set()
      project.get_links()
      for link in project.links:
            for n in link.nodes:
                  if n["node_id"] == node.node_id:
                        used_ports.add(n["port_number"])
      for p in node.ports:
            if p["port_number"] not in used_ports:
                  return p  # first free port
      return None

def get_link_template_base(server, project_id, filter:None | dict=None):
      return {
            "project_id":project_id,
            "connector": server,
            "link_type":"ethernet",  
            "link_id":None, 
            "filters": filter
      }

def get_node_template_base(server, project_id, name):
      if name == "Ethernet switch" :
            return {
                  "project_id":project_id,
                  "connector": server,
                  "template": name,
                  "locked": False,
                  "properties":{
                        "ports_mapping": [
                              {"name": f"Ethernet{i}", "port_number": i, "type": "access", "vlan": 1}
                              for i in range(30)
                        ]
                  }
            }
      else:
            return {
                  "project_id":project_id,
                  "connector": server,
                  "template": name,
                  "locked": False,
            }
      
class Topology:

      def __init__(self, type:TopologyType, intent:dict, name:str) -> None:
            server = Gns3Connector("http://localhost:3080")
            self.project = Project(name=name, connector=server)
            self.project.get() 
            self.project_id = self.project.project_id
            self.intent = intent

            self.switch_name  = "Ethernet switch"     if "Ethernet switch"    in self.intent else None
            self.pc_name      = "gossip_base"         if "gossip_base"        in self.intent else None

            self.pc_template_base         = get_node_template_base(server, self.project_id, self.pc_name) 
            self.switch_template_base     = get_node_template_base(server, self.project_id, self.switch_name)
            self.link_template_base       = get_link_template_base(server, self.project_id)

            self.switch_count = self.intent[self.switch_name]
            self.pc_count     = self.intent[self.pc_name]

            self.switchs, self.pcs, self.links = [], [], []

            if type == TopologyType.FULL_MESH:
                 self.gen_full_mesh()
                 self.gen_retrieval_map()

      def add_switch(self, i, all_clusters):
            addition = {
                  "name": f"S{i}",
                  "x": all_clusters[i][0] + 100,
                  "y": all_clusters[i][1] + 80, 
            }
            self.switchs.append(Node(
                  **self.switch_template_base,
                  **addition,
            ))
            self.switchs[-1].create()
            for j in range(self.pc_count // self.switch_count):
                  self.add_pc(i, j, all_clusters)
                  self.add_pc_link(i, j)


      def add_pc(self, i, j, all_clusters):
            node_addition = {
                  "name": f"PC{i*10+j}",
                  "x": all_clusters[i][0] + 40 * (j%5),
                  "y": all_clusters[i][1] + 150 * (j%2), 
            }
            self.pcs[i].append(Node(
                  **self.pc_template_base,
                  **node_addition
            ))
            self.pcs[i][-1].create()
      
      def add_pc_link(self, i, j):
            link_addition = {
                  "nodes":[
                        {"node_id": self.switchs[-1].node_id, "adapter_number":0, "port_number": j},
                        {"node_id": self.pcs[i][-1].node_id, "adapter_number": 0, "port_number": 0},
                  ],
            }
            self.links[i].append(Link(
                  **link_addition,
                  **self.link_template_base,
            ))
            self.links[i][-1].create()
      
      def add_switch_link(self, a, b, sa, sb):
            pa = get_free_port(sa, self.project)
            pb = get_free_port(sb, self.project)
            link_addition = {
                  "nodes":[
                        {"node_id": sa.node_id, "adapter_number": pa["adapter_number"], "port_number": pa["port_number"]},
                        {"node_id": sb.node_id, "adapter_number": pb["adapter_number"], "port_number": pb["port_number"]},
                  ],
            }

            self.links[-1].append(Link(
                  **link_addition,
                  **self.link_template_base
            ))
            self.links[-1][-1].create()


      def gen_full_mesh(self):
            ### generate 10 pcs connected to one switch 
            ### connect all switches in a full mesh
            all_clusters = [
                  [200, 200], [200, 400], [200, 600],
                  [400, 200], [400, 400], [400, 600],
                  [600, 200], [600, 400], [600, 600],
                  [400, 800],
            ]
            for i in range(self.switch_count):
                  self.pcs.append([])
                  self.links.append([])
                  self.add_switch(i, all_clusters)
            
            self.links.append([])
            self.project.get_links()
            for i, sa in enumerate(self.switchs):
                  for j, sb in enumerate(self.switchs):
                        if j <= i:
                              continue  # avoid duplicates (S1-S2 only once)
                        self.add_switch_link(i, j, sa, sb)

      def gen_retrieval_map(self):
            data = {}

            for index, switch in enumerate(self.switchs):
                 data[f"{switch.name} : {switch.node_id}"] = list(map(lambda x: f"{x.name} : {x.node_id}", self.pcs[index]))

            with open("retrieval_map.json", "w") as f:
                  json.dump(data, f, indent=6)
      



# Open and read a JSON file
with open("intent.json", "r") as file:
    data = json.load(file)  # parses JSON into a Python dict or list

topo = Topology(TopologyType.FULL_MESH, data, "testdocker")

