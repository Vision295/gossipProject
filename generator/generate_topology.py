import enum
import json
from enum import Enum
from project_generator import ProjectGenerator
from math import sqrt


class TopologyType(Enum):
      CURRENT_MESH = 0
      FULL_MESH = 1
      BUS = 2
      CLUSTERED = 3
      RANDOM = 4
      HIERARCHICAL = 5
      
class TopologyGenerator(ProjectGenerator):
      """Class to generate different topologies"""

      def __init__(self, type:TopologyType, intent:dict, project_name:str, file_name:str) -> None:
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
            super().__init__(intent, project_name)
            self.type = type
            match self.type:
                  case TopologyType.FULL_MESH:
                        self.gen_full_mesh()
                  case TopologyType.BUS:
                        self.gen_bus_mesh()

            self.gen_retrieval_map(file_name)

      
      
      def gen_bus_mesh(self):
            self.gen_base()
            for index, value in enumerate(self.switchs[:-1]):
                  self.add_switch_link(value, self.switchs[index+1])


      def gen_full_mesh(self):
            """generates a full mesh using the previous seen methods"""
            self.gen_base()
            for i, sa in enumerate(self.switchs):
                  for j, sb in enumerate(self.switchs):
                        if j <= i:
                              continue  # avoid duplicates (S1-S2 only once)
                        self.add_switch_link(sa, sb)



# Open and read a JSON file
with open("json/intent.json", "r") as file:
    data = json.load(file)  # parses JSON into a Python dict or list

topo = TopologyGenerator(TopologyType.FULL_MESH, data, "fullmesh", "fullmesh")

