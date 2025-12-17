import json
from enum import Enum
from .project_generator import ProjectGenerator
import random

def generic_filter():
      return {"delay": [random.randrange(1, 21)]}

class TopologyType(Enum):
      CURRENT_MESH      =    "currentmesh"
      FULL_MESH         =    "fullmesh"
      BUS               =    "bus"
      CLUSTERED2        =    "clustered2"
      CLUSTERED3        =    "clustered3"
      RANDOM            =    "random"
      HIERARCHICAL      =    "hierarchical"
      
class TopologyGenerator(ProjectGenerator):
      """Class to generate different topologies"""

      def __init__(self, type:TopologyType, intent:dict, project_name:str) -> None:
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
                  case TopologyType.CLUSTERED2:
                        self.gen_clustered2_mesh()
                  case TopologyType.CLUSTERED3:
                        self.gen_clustered3_mesh()



      def gen_clustered2_mesh(self):
            self.gen_base()
            for index, value in enumerate(self.switchs[:-1]):
                  pa, pb = self.get_free_port(index), self.get_free_port(index+1)
                  self.add_link(value, pa, self.switchs[index+1], pb)
                  self.apply_filter_to_last_link(generic_filter())
            pa, pb = self.get_free_port(0), self.get_free_port(-1)
            self.add_link(self.switchs[0], 0, self.switchs[-1], -1)
            

      def choose_links_at_random(self, n):
            set_of_links = set()
            for i in range(n - 1):
                  set_of_links.add((i, i+1))
                  set_of_links.add((i+1, i))
            set_of_links.add((0, n - 1))
            set_of_links.add((n - 1, 0))
            l = list(range(n))
            while len(set_of_links) < n*3:
                  sa = random.choice(l)
                  l.remove(sa)
                  sb = random.choice(l)
                  l.remove(sb)
                  set_of_links.add((sa, sb))
                  set_of_links.add((sb, sa))
                  l.append(sa)
                  l.append(sb)
            return set_of_links



      def gen_clustered3_mesh(self):
            set_of_links = self.choose_links_at_random(self.total_number_switch)
            indexes = []
            self.gen_base()
            for (sa, sb) in set_of_links:
                  if (sa, sb) in indexes:
                        continue
                  if (sb, sa) in indexes:
                        continue
                  pa, pb = self.get_free_port(sa), self.get_free_port(sb)
                  self.add_link(self.switchs[sa], pa, self.switchs[sb], pb)
                  indexes.append((sa, sb))


      
      def gen_bus_mesh(self):
            self.gen_base()
            for index, value in enumerate(self.switchs[:-1]):
                  pa, pb = self.get_free_port(index), self.get_free_port(index+1)
                  self.add_link(value, pa, self.switchs[index+1], pb)
                  self.apply_filter_to_last_link(generic_filter())
            pa, pb = self.get_free_port(0), self.get_free_port(-1)
            self.add_link(self.switchs[0], pa, self.switchs[-1], pb)
            self.apply_filter_to_last_link(generic_filter())


      def gen_full_mesh(self):
            """generates a full mesh using the previous seen methods"""
            self.gen_base()
            for i, sa in enumerate(self.switchs):
                  for j, sb in enumerate(self.switchs):
                        if j <= i:
                              continue  # avoid duplicates (S1-S2 only once)
                        self.add_link(sa, i, sb, j)




