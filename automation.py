from gns3fy import Gns3Connector, Project
from generator import *
from load_simulation import *



# What i could miss : block_size, bandwidth limitation
# TODO: make the set of link constraints
# TODO: make the clustered 1 and 2 work 
# TODO: rum everything for 1 mesh 1 size

SWITCH_TEMPLATE_NAME = "Open vSwitch"
PC_TEMPLATE_NAME = "gossiptcpudp"
PROJECT_NAME = "gossip_project"

full_mesh_info = {
     TopologyType.FULL_MESH: {"S": (3, 15), "M": (10, 50), "L": (20, 100),"XL": (40, 200)},
     TopologyType.BUS: {
          "S": (7, 14), "M": (25, 50), "L": (50, 100), "XL": (100, 200),
          "L1to1": (50, 50),"XL1to1": (100, 100)},
     TopologyType.CLUSTERED2: {"S": (3, 15), "M": (10, 50), "L": (20, 100),"XL": (40, 200)}, 
     TopologyType.CLUSTERED3: {"S": (3, 15), "M": (10, 50), "L": (20, 100),"XL": (40, 200)}, 
#      TopologyType.RANDOM,
#      TopologyType.HIERARCHICAL
}
mesh_info = {
     TopologyType.FULL_MESH: {"S": (3, 15), "M": (10, 50)},
     TopologyType.BUS: {"S": (7, 14), "M": (25, 50), "L1to1": (50, 50)},
     TopologyType.CLUSTERED2: {"S": (3, 15), "M": (10, 50)}, 
     TopologyType.CLUSTERED3: {"S": (3, 15), "M": (10, 50)}, 
#      TopologyType.RANDOM,
#      TopologyType.HIERARCHICAL
}
protocol_list = ["UDP", "TCP"]
blocks_list = ["block_50KB"] # , "block_100KB", "block_500KB", "block_1000KB", "block_5000KB"]
# bandwidth = 100

# mesh, size = "", ""
# nb_switch, nb_pc = 0, 0
# protocol = ""
# block = ""

# intent_base = {
#       mesh+size:{
#             SWITCH_TEMPLATE_NAME: nb_switch,
#             PC_TEMPLATE_NAME: nb_pc,
#             "ip_range": "172.19.0.100/24",
#             "protocol": protocol,
#             "mesh": mesh,
#       }
# }

def iterate_through_intents():
      for mesh_type, mesh_value in mesh_info.items():
            for _, size_value in mesh_value.items():
                  for protocol in protocol_list:
                        nb_switch = size_value[0]
                        nb_pc = size_value[1]
                        for i in range(5):
                              yield {
                                    SWITCH_TEMPLATE_NAME: nb_switch,
                                    PC_TEMPLATE_NAME: nb_pc,
                                    "ip_range": "172.19.0.100/24",
                                    "protocol": protocol,
                                    "mesh": mesh_type,
                              }


# Connect to GNS3 server
server = Gns3Connector(url="http://localhost:3080")

def full_automation():
      project = Project(
            name="my_empty_project",
            connector=server
      )
      project.create()        # type: ignore
      project.open()          # type: ignore
      project.get()           # type: ignore
      print("Project created:", project.project_id)
      for experiment in iterate_through_intents():
            run_experiment("project_gossip", experiment)
      project.close()
