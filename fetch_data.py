import json
import re
from pathlib import Path
from collections import defaultdict
from sysconfig import get_paths
from typing import List, Dict, Any, Tuple
from math import *
from functools import reduce

RESULTS_DIR = Path("results")

# ---------------------------------------------------------
# 1. Detect highest Y (experiment folder)
# ---------------------------------------------------------
def get_latest_experiment():
      ys = [int(p.name) for p in RESULTS_DIR.iterdir() if p.is_dir() and p.name.isdigit()]
      if not ys:
            raise RuntimeError("No experiment folders found in results/")
      return RESULTS_DIR / str(max(ys))


# ---------------------------------------------------------
# 2. Parse all X.txt (X != 0) + 0.txt in latest Y
# ---------------------------------------------------------

# Regexes
send_block_re = re.compile(r"Send block data (\d+) to ([0-9\.]+)")
recv_block_re = re.compile(
      r"block_(\d+) is received.*from ([0-9\.]+), transmission delay: (\d+) ms.*\(length:\s*(\d+)"
)
time_re = re.compile(r"\[time\s*:\s*(\d+)\]")

def parse_file(path: Path): 
    data = {
        "send_events": [],
        "receive_events": [],
    }

    for line in path.read_text().splitlines():
        t_match = time_re.search(line)
        timestamp = int(t_match.group(1)) if t_match else None

        m = send_block_re.search(line)
        if m:
            blk = int(m.group(1))
            ip = m.group(2)
            data["send_events"].append({
                "time": timestamp,
                "block": blk,
                "to": ip
            })

        m = recv_block_re.search(line)
        if m:
            blk = int(m.group(1))
            ip = m.group(2)
            delay = int(m.group(3))
            length = int(m.group(4))
            data["receive_events"].append({
                "time": timestamp,
                "block": blk,
                "from": ip,
                "delay_ms": delay,
                "length": length
            })

    return data


def get_paths_with_destinations(sender, receivers, sender_ip="172.19.0.0"):
    """
    Generates a list of paths for EVERY packet reception.
    One send event can create MULTIPLE paths (one for each receiver that got it).
    Format: {'block': id, 'path': [(time, ip), (time, ip)], 'delay': ms}
    """
    paths = []

    # 1. Iterate through every send event
    for s_event in sender.get("send_events", []):
        
        block_id = s_event.get("block")
        send_time = s_event.get("time")
        target_ip = s_event.get("to")  # The intended destination
        
        # 2. For THIS send event, find ALL receivers that received it
        for receiver in receivers:
            
            # Get receiver IP
            current_receiver_ip = receiver.get("ip", None)
            
            # If IP not in dict, try to infer from receive_events or send_events
            if not current_receiver_ip:
                if receiver.get("receive_events"):
                    # Could be stored in the receive event somehow
                    # or we need it to be provided
                    pass
                if receiver.get("send_events"):
                    # Maybe in send_events?
                    pass
            
            # 3. Check all receive events for THIS receiver
            for r_event in receiver.get("receive_events", []):
                
                # Match conditions:
                # - Same block ID
                # - Came from sender_ip
                # - Receive time after send time
                if (r_event.get("block") == block_id and 
                    r_event.get("from") == sender_ip and
                    r_event.get("time") > send_time):
                    
                    receive_time = r_event.get("time")
                    delay = receive_time - send_time
                    
                    # Create path for this specific reception
                    current_path = [
                        (send_time, sender_ip),
                        (receive_time, current_receiver_ip or target_ip)
                    ]
                    
                    # Append this path
                    paths.append({
                        "block": block_id,
                        "path": current_path,
                        "delay": delay,
                        "target_ip": target_ip,
                        "actual_receiver": current_receiver_ip or target_ip
                    })

    return paths


def get_paths_with_destinations_optimized(sender, receivers, sender_ip="172.19.0.0"):
    """
    Optimized version: Uses nearest-time matching when there are multiple 
    possible receive events (handles retransmissions better).
    """
    paths = []

    # Build a map: receiver -> list of receive events
    receiver_events_map = []
    for receiver in receivers:
        receiver_ip = receiver.get("ip", None)
        events = receiver.get("receive_events", [])
        receiver_events_map.append({
            "ip": receiver_ip,
            "events": events
        })

    # 1. Iterate through every send event
    for s_event in sender.get("send_events", []):
        
        block_id = s_event.get("block")
        send_time = s_event.get("time")
        target_ip = s_event.get("to")
        
        # 2. For each receiver, find the BEST matching receive event
        for receiver_info in receiver_events_map:
            
            receiver_ip = receiver_info["ip"]
            
            # Find all matching receive events for this send
            matching_events = []
            for r_event in receiver_info["events"]:
                if (r_event.get("block") == block_id and 
                    r_event.get("from") == sender_ip and
                    r_event.get("time") > send_time):
                    matching_events.append(r_event)
            
            # If multiple matches, pick the one with smallest time difference
            # (most likely to be the actual reception of THIS send)
            if matching_events:
                # Sort by time difference
                matching_events.sort(key=lambda e: e.get("time") - send_time)
                
                # Take the closest one
                best_match = matching_events[0]
                receive_time = best_match.get("time")
                delay = receive_time - send_time
                
                # Create path
                current_path = [
                    (send_time, sender_ip),
                    (receive_time, receiver_ip or target_ip)
                ]
                
                paths.append({
                    "block": block_id,
                    "path": current_path,
                    "delay": delay,
                    "target_ip": target_ip,
                    "actual_receiver": receiver_ip or target_ip
                })

    return paths


def get_paths_with_all_receptions(sender, receivers, sender_ip="172.19.0.0"):
    """
    Alternative approach: Create a path for EVERY single receive event,
    matching it to the corresponding send event.
    
    This ensures we capture ALL receptions, including duplicates/retransmissions.
    """
    paths = []
    
    # Build lookup: (block_id, target_ip) -> list of send events
    send_lookup = {}
    for s_event in sender.get("send_events", []):
        key = (s_event.get("block"), s_event.get("to"))
        if key not in send_lookup:
            send_lookup[key] = []
        send_lookup[key].append(s_event)
    
    # For each receiver, process all their receive events
    for receiver in receivers:
        receiver_ip = receiver.get("ip", None)
        
        for r_event in receiver.get("receive_events", []):
            block_id = r_event.get("block")
            from_ip = r_event.get("from")
            receive_time = r_event.get("time")
            
            # Only process if it came from our sender
            if from_ip != sender_ip:
                continue
            
            # Find the matching send event
            key = (block_id, receiver_ip)
            
            if key in send_lookup and send_lookup[key]:
                # Find the most recent send before this receive
                valid_sends = [s for s in send_lookup[key] if s.get("time") < receive_time]
                
                if valid_sends:
                    # Take the closest send event before this receive
                    send_event = max(valid_sends, key=lambda s: s.get("time"))
                    send_time = send_event.get("time")
                    delay = receive_time - send_time
                    
                    # Create path
                    current_path = [
                        (send_time, sender_ip),
                        (receive_time, receiver_ip or send_event.get("to"))
                    ]
                    
                    paths.append({
                        "block": block_id,
                        "path": current_path,
                        "delay": delay,
                        "target_ip": send_event.get("to"),
                        "actual_receiver": receiver_ip or send_event.get("to")
                    })
    
    return paths

def get_general_data(sender: Dict, receivers: List[Dict], n_blocks: int) -> Dict:
      general_data = {}
      # to get:     "general_delay", "general_packet_loss"
      send_dates = []
      for send_event in sender["send_events"]:
            if send_event["block"] > len(send_dates):
                 send_dates.append(send_event["time"])


      data_paths = get_paths_with_destinations(sender, receivers)
      for d in data_paths[:2]:
            print("===================")
            print(d)
      data_paths = get_paths_with_destinations(sender, receivers)
      print("\n\n\n")
      for d in data_paths[:2]:
            print("===================")
            print(d)
      print("\n\n\n")
      data_paths = get_paths_with_destinations_optimized(sender, receivers)
      for d in data_paths[:2]:
            print("===================")
            print(d)
                  
      delay_per_block = [-1 for _ in range(n_blocks)]
      for path in data_paths:
            times = [x[0] for x in path["path"]]
            delay_per_block[path["block"] - 1] += max(times) - min(times)
      print(delay_per_block)
      exit()

      print(send_dates)
      # to get : "delay_per_pc", "delay_per_block_per_pc", "packet_loss_per_pc"
      delay_per_block_per_pc:list[list[Dict]] = []
      """
      [
            [
                  event1_block1_pc1{}, 
                  event1_block2_pc1{},
                  ...
            ],
            [
                  event1_block1_pc2{}, 
                  event1_block2_pc2{},
                  ...
            ],
            ...
      ]
      """
      
      for pc, receiver in enumerate(receivers):
            delay_per_block_per_pc.append([{} for _ in range(n_blocks)])
            for receiver_event in receiver["receive_events"]:
                  block, time = receiver_event["block"], receiver_event["time"] 
                  delay_per_block_per_pc[pc][block-1] = abs(send_dates[block - 1] - time)

      print(delay_per_block_per_pc)
      # to get : "delay_per_block", "packet_loss_per_block"
      for send_event in sender:
            block = send_event["block"]
            general_data[block]["send_date"] = send_dates[block]


           

      return sender      


def analyze_network_events(sender: Dict, receivers: List[Dict], experiment_setup:dict) -> Dict[str, Any]:
      """
      Main function to analyze network events and return complete results.
      All delays are computed from first send time of each block to when receivers get it.
      """
      
      # Overall general data
      max_block = experiment_setup["max_block"]
      result = get_general_data(sender, receivers, max_block)
#     result["general_delay"] = get_general_delay(general_data)
#     result["general_packet_loss"] = get_general_packet_loss(general_data)
    
#     # Per block data
#     per_block_data = get_per_block_data(sender, receivers)
#     result["blocks"] = {}
#     for block_id, block_data in per_block_data:
#         result["blocks"][block_id] = {
#             "delay_per_block": get_delay_per_block(block_data),
#             "packet_loss_per_block": get_general_packet_loss(block_data)
#         }
    
#     # Per PC data
#     per_pc_data = get_per_pc_data(sender, receivers)
#     result["pcs"] = {}
#     for pc_ip, pc_data in per_pc_data:
#         result["pcs"][pc_ip] = {
#             "delay_per_pc": get_delay_per_pc(pc_data),
#             "delay_per_block_per_pc": get_delay_per_block_per_pc(pc_data),
#             "packet_loss_per_pc": get_general_packet_loss(pc_data)
#         }
    
      print(result)
      exit()
      return result
# ---------------------------------------------------------
# 3. Aggregate over all X != 0
# ---------------------------------------------------------
def aggregate(folder: Path, experiment_setup:dict):
      files = list(folder.glob("*.txt"))

      sender_file = folder / "0.txt"
      receiver_files = [f for f in files if f.name != "0.txt"]

      sender = parse_file(sender_file)

      receivers = []
      for f in receiver_files:
            receivers.append(parse_file(f))

      # Compute average delays per block across receivers
      delay_map = {}   # block_id -> list of delays

      for rec in receivers:
            for ev in rec["receive_events"]:
                  delay_map.setdefault(ev["block"], []).append(ev["delay_ms"])

      avg_delays = {
            blk: (sum(lst) / len(lst)) for blk, lst in delay_map.items()
      }

      result = analyze_network_events(sender, receivers, experiment_setup)

      return {
            "sender": sender,
           "receivers": receivers
      }
    

# ---------------------------------------------------------
# 4. Save JSON file
# ---------------------------------------------------------
def fetch_data(experiment_setup:dict):
      folder = get_latest_experiment()
      result = aggregate(folder, experiment_setup)

      out_path = folder / "analysis.json"
      out_path.write_text(json.dumps(result, indent=4))

      print(f"analysis.json generated in: {out_path}")



# with open("json/intent.json", "r") as file:
#       data = json.load(file)  # parses JSON into a Python dict or list
# fetch_data(data)