import json
from gns3fy import Gns3Connector, Project, Link, Node
import ipaddress
from typing import Set
from math import sqrt
from enum import Enum
import requests

class Protocol(Enum):
    UDP="UDP"
    TCP="TCP"

PortNumber = int        # TODO
NodeDict = dict         # TODO
ProjectId = str         # TODO
FilterDict = dict       # TODO
LinkDict = dict         # TODO
DockerProperties = dict # TODO
      
class ProjectGenerator:
      """Class to generate different topologies"""

      def __init__(self, intent:dict, project_name:str) -> None:
            """basic init :
            - project data (ProjectId, Project)
            - intent file (json)
            - basic templates (switchs, pcs)
            - track on pcs and switch (list of switch and pcs and counts)

            :param type: the type of topology to generate
            :type type: TopologyType
            :param intent: the intent file which contains the following information - {iprange, #ofpcs, #ofswitches, ...}
            :type intent: dict
            :param project_name: name of the project
            :type project_name: str
            """
            self.server = Gns3Connector("http://localhost:3080")
            self.project = Project(name=project_name, connector=self.server)
            self.project.get()
            self.project_id = self.project.project_id
            if not self.project_id : return None
            self.intent = intent

            # update switch and pc types based on intent
            self.switch_name  = "Open vSwitch"    if "Open vSwitch"    in self.intent else "Open vSwitch"
            self.pc_name      = "gossip"          if "gossip"         in self.intent else "gossiptcpudp"

            # get templates
            self.set_switch_template_base() 
            self.set_pc_template_base()
            self.set_link_template_base()

            # init the counts on pc and switches
            self.total_number_pc          = self.intent[self.pc_name]
            self.total_number_switch      = self.intent[self.switch_name]
            self.switch_count = 0
            self.pc_count     = 0

            # self.protocol = Protocol.UDP if self.intent["protocol"] == "UDP" else Protocol.TCP
            self.protocol = self.intent["protocol"]
            self.block_name = self.intent["block_name"]
            self.max_block = self.intent["max_block"]
            self.f_out = self.intent["f_out"]
            self.block_gen_time = self.intent["block_gen_time"]

            # init the list of pcs and switchs
            self.switchs, self.pcs, self.switch_links = [], [], []

            # gets the list of neighbors to pass as argument on creation of pc
            self.neighborListToStr = ""
            self.set_ip_list()
            self.gen_position()

      def get_all_used_ports(self, node:Node) -> None | Set[PortNumber]:
            """gets all the ports connected to a node from project (requires the project to be openned)

            :param node: Node
            :type node: Node
            :param project: Project
            :type project: Project
            :return: a set of numbers representing the port number
            :rtype: None | Set[Portnumber]
            """
            used_ports = set()
            self.project.get_links()
            for link in self.project.links:
                  if not link       : return None
                  if not link.nodes : return None
                  for n in link.nodes:
                        if n["node_id"] == node.node_id:
                              used_ports.add(n["port_number"])
            return used_ports

      def get_free_port(self, index:int):
            """get the first free port (resquires the project to be open)

            :param node: node from a project 
            :type node: Node
            :param project: project openned
            :type project: Project
            :return: number of the first available port
            :rtype: None | Unknown
            """
            ports = self.switch_links[index]
            for i in range(16):
                  if i not in ports:
                        self.switch_links[index].append(i)
                        return i
            return 0

      def set_link_template_base(self):
            """generate a template for link creation

            :param filter: filters to a link (delay, ...), defaults to None
            :type filter: None | FilterDict, optional
            """
            self.link_template_base = {
                  "project_id":self.project_id,
                  "connector": self.server,
                  "link_type":"ethernet",  
                  "link_id":None, 
            }

      def set_pc_template_base(self):
            self.pc_template_base = {
                  "project_id":self.project_id,
                  "connector": self.server,
                  "template": self.pc_name,
                  "locked": False,
            }
      
      def set_switch_template_base(self):
            self.switch_template_base = {
                  "project_id":self.project_id,
                  "connector": self.server,
                  "template": self.switch_name,
                  "locked": False,
                  "properties":{
                        # "ports_mapping": [
                        #       {"name": f"Ethernet{i}", "port_number": i, "type": "access", "vlan": 1}
                        #       for i in range(60)
                        # ]
                  }
            }

      ### TODO : define envformat
      def set_ip_list(self) -> None:
            """sets the ip list of format : "IP1,IP2,..." to pass it in the env variables 
            on creation of a node."""

            ip_range = self.intent.get("ip_range", None)
            if ip_range is None or self.total_number_pc <= 0 : return None
            
            network = ipaddress.ip_network(ip_range, strict=False)
            start_ip = network.network_address  # first IP in the network
            ip_list = [str(start_ip + i) for i in range(self.total_number_pc + 1)][1:]

            self.neighborListToStr = ",".join(ip_list)

      def get_docker_properties(self) -> DockerProperties:
            """gets the environment variables to set for the docker container. 
            These variables are used to create a push_config.toml file based 
            on some exclusive properties depending on the node number.

            :return: a dict of properties
            :rtype: DockerProperties
            """
            return {
                  "properties": {
                              "environment": "\n".join([
                              f"PACKET_SIZE=1500",
                              f"NODE_IDX={self.pc_count}",
                              f"PORT={8300+self.pc_count}",
                              f"NEIGHBORS={self.neighborListToStr}",
                              f"MAX_BLOCK={self.max_block}",
                              f"BLOCK_GEN_TIME={self.block_gen_time}",
                              "PULL_INTERVAL=4000",
                              f'BLOCK_FILE="{self.block_name}"',
                              "ONLY_PUSH=false",
                              f"F_OUT={self.f_out}",
                              f'PROTOCOL="{self.protocol}"'
                        ])
                  }
            }

      def add_switch(self, i:int, all_clusters:list[tuple[int, int]]):
            """adds a switch to the switch list and creates it each switch node is based on :
            - a set of additionnal features (its position and name)
            - a set of standard features (its template type, ...)

            :param i: the i-th switch
            :type i: int
            :param all_clusters: based on some position on the gns3 scrreen (tuple[int, int] is its x, y coord)
            :type all_clusters: list[tuple[int, int]]
            """
            addition = {
                  "name": f"S{self.switch_count}",
                  "x": all_clusters[i][0] + 100,
                  "y": all_clusters[i][1] + 80, 
            }
            self.switchs.append(Node(
                  **self.switch_template_base,
                  **addition,
            ))
            self.switchs[-1].create()
            self.switch_count += 1
            # foreach switch we have to create self.totoal_number_pc // self.totoal_number_switch pcs
            self.switch_links.append([])
            for j in range(self.total_number_pc // self.total_number_switch):
                  self.add_pc(i, j, all_clusters)
                  switch_port = self.get_free_port(i)
                  self.add_link(self.pcs[i][j], 0, self.switchs[i], switch_port)

      def add_pc(self, i:int, j:int, all_clusters:list[tuple[int, int]]):
            """adds a pc to the pc list and creates it each pc node is based on :
            - a set of additionnal features (its position and name)
            - a set of standard features (its template type, ...)
            - a set of environment variables

            :param i: from the i-th switch
            :type i: int
            :param j: create the j-th pc
            :type j: int
            :param all_clusters: its position depends on the position of the switchs defined here
            :type all_clusters: list[tuple[int, int]]
            """
            node_addition = {
                  "name": f"PC{self.pc_count}",
                  "x": all_clusters[i][0] + 40 * (j%5),
                  "y": all_clusters[i][1] + 150 * (j%2), 
            }
            self.pcs[i].append(Node(
                  **node_addition,
                  # here we get the env variables 
                  **self.get_docker_properties(),
                  **self.pc_template_base,
            ))
            self.pcs[i][-1].create()
            self.pc_count += 1
      
      def add_link(self, node_a:Node, pa:int, node_b:Node, pb:int):
            """adds a link between two switches this function is seperated because 
            we have to iterate over each switches only once

            :param switch_a: switch a
            :type switch_a: Node
            :param switch_b: switch a
            :type switch_b: Node
            """
            self.project.get()
            self.project.create_link(
                  node_a.name,
                  f"eth{pa}",
                  node_b.name,
                  f"eth{pb}"
            )

      def apply_filter_to_last_link(self, filter):
            self.project.get_links()
            link = self.project.links[-1]  # the most recently created link

            self.apply_filter(link, filter)

      def apply_filter(self, link, filters):
            link.filters = filters
            data = {
                  "project_id": link.project_id,
                  "link_id": link.link_id,
                  "link_type": link.link_type,
                  "nodes": link.nodes,
                  "filters": link.filters  # apply filters here
            }

            url = f"http://localhost:3080/v2/projects/{link.project_id}/links/{link.link_id}"
            resp = requests.put(url, json=data)
            resp.raise_for_status()  # raise error if failed
            link.get()
            

      def gen_position(self):
            self.base_position = []
            square_length = int(sqrt(self.total_number_switch)) + 1
            x, y = 0, 0
            for _ in range(self.total_number_switch):
                  self.base_position.append(
                        (-1100+200*x, -500+200*(y%square_length))
                  )
                  x += 1
                  y += square_length == x
                  x = 0*(x == square_length) + x*(x != square_length)

      def gen_base(self):
            # generate pcs connected to one switch 
            # connect all switches in a full mesh
            for i in range(self.total_number_switch):
                  self.pcs.append([])
                  self.add_switch(i, self.base_position)
            
            # loop through all switches to create a full mesh
            self.project.get_links()

      def gen_retrieval_map(self, file_name):
            """creates a file : retrieval map to retrieve the nodes from a created full_mesh
            the format of the file is as followes :
            {"switch_name : switch_id" : [list of "pc_name : pc_id"]}"""
            data = {}

            for index, switch in enumerate(self.switchs):
                 data[f"{switch.name} : {switch.node_id}"] = list(map(lambda x: f"{x.name} : {x.node_id}", self.pcs[index]))

            with open(f"json/{file_name}_retrieval_map.json", "w") as f:
                  json.dump(data, f, indent=6)
      