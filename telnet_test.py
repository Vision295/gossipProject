and how can i get this from the following code : 
import json
import time
import telnetlib
from generate_topology import Topology, TopologyType
from gns3fy import Node
import ipaddress
from project_info import (
      HOST,
      TIMEOUT
)


def get_number(node:Node):
      if node:
            return int(node.name.removeprefix("PC"))
      else:
            return -1


class TelnetVpc:

      def __init__(self, intent:dict)  -> None:
            self.topo = Topology(TopologyType.CURRENT_MESH, {})
            self.intent = intent

      def ip_setup(self):
            self.ip_range = self.intent["ip_range"]
            self.network = ipaddress.ip_network(self.ip_range, strict=False)
            self.ip_list = list(self.network.hosts())

      def assign_ips(self):
            self.ip_setup()
            for pcs in self.topo.pcs:
                  for pc in pcs:
                        tn = telnetlib.Telnet(HOST, pc.console, TIMEOUT)
                        host_ip = self.ip_list[get_number(pc)]
                        netmask = str(self.network.netmask)
                        gateway = str(self.ip_list[-1])
                        what_to_write = f"ip {host_ip} {netmask} {gateway}\n"
                        tn.write(what_to_write.encode('ascii'))




with open("intent.json", "r") as file:
    data = json.load(file)  # parses JSON into a Python dict or list
telnetObj = TelnetVpc(data)
telnetObj.assign_ips()
