# Files & Folders
The main file to generate the base topology on gns3
## generator
folder to create a topology from scratch within a fresh gns3 project included meshs : bus, full mesh, clustered 1 & 2
## cleanup.py
Removes the current topology on gns3
## launch_dockers.py 
Currently under developpement : to synch generate_topology and launch_simulation to be able to edit in docker containers easily
## project_info.py and links.py
Basic info and tests on links between nodes
## load_simulation.py and automation.py
Files to create simulations of the gossip sequence execution and to automate its execution
## *.json
intent : parameters to generate the topology
exp_count : counts the number of experiences done per type
## *.toml
files to setup the container and to launch the gossip sequence
