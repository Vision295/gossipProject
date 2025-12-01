import json
from tkinter import CURRENT
from gns3fy import Gns3Connector, Project, Node
import time
from generator import *


# What i could miss : block size, bandwidth limitation
# TODO: make the set of link constraints
# TODO: make the clustered 1 and 2 work 
# TODO: rum everything for 1 mesh 1 size

SWITCH_TEMPLATE_NAME = "Ethernet switch"
PC_TEMPLATE_NAME = "gossiptcpudp"

mesh_info = {
     TopologyType.FULL_MESH: {"S": (3, 15), "M": (10, 50), "L": (20, 100),"XL": (40, 200)},
     TopologyType.BUS: {
          "S": (7, 14), "M": (25, 50), "L": (50, 100), "XL": (100, 200),
          "L1to1": (50, 50),"XL1to1": (100, 100)},
     TopologyType.CLUSTERED2: {"S": (3, 15), "M": (10, 50), "L": (20, 100),"XL": (40, 200)}, 
     TopologyType.CLUSTERED3: {"S": (3, 15), "M": (10, 50), "L": (20, 100),"XL": (40, 200)}, 
#      TopologyType.RANDOM,
#      TopologyType.HIERARCHICAL
}
protocol_list = ["UDP", "TCP"]
links_list = [{} for i in range(10)]

mesh, size = "", ""
nb_switch, nb_pc = 0, 0
protocol = ""
links = {}

intent_base = {
      mesh+size:{
            SWITCH_TEMPLATE_NAME: nb_switch,
            PC_TEMPLATE_NAME: nb_pc,
            "ip_range": "172.19.0.100/24",
            "protocol": protocol,
            "mesh": mesh,
            "links": links
      }
}



# Connect to GNS3 server
server = Gns3Connector(url="http://localhost:3080")

project = Project(
    name="my_empty_project",
    connector=server
)
project.create()        # type: ignore
project.open()          # type: ignore
project.get()           # type: ignore
print("Project created:", project.project_id)

with open("json/intent.json", "r") as file:
    data = json.load(file)  # parses JSON into a Python dict or list

topo = TopologyGenerator(TopologyType.FULL_MESH, data, "my_empty_project", "fullmesh")


for node in project.nodes:
      node.start()


time.sleep(120)
project.close()
project.delete()
