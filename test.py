from collections import defaultdict
from typing import List, Dict, Any, Optional

def calculate_network_metrics(sender: Dict[str, Any], receivers: List[Dict[str, Any]], sender_ip: str = "172.19.0.0"):
    """
    Calculates P2P network metrics: Delay, Packet Loss (Overall, Per PC, Per Block).
    
    Args:
        sender: Dict containing "send_events" and "receive_events".
        receivers: List of Dicts, each containing "send_events" and "receive_events".
        sender_ip: The IP of the main sender node (used to filter receive events).
    """
    
    # --- Data Structures ---
    # Structure: stats[target_ip][block_id] = {'sent': 0, 'received': 0, 'delays': []}
    pc_stats = defaultdict(lambda: defaultdict(lambda: {'sent': 0, 'received': 0, 'delays': []}))
    
    # Global accumulators
    total_sent = 0
    total_received = 0
    all_delays = []
    
    # Block accumulators: block_stats[block_id] = {'sent': 0, 'received': 0}
    block_stats = defaultdict(lambda: {'sent': 0, 'received': 0, 'delays': []})

    # --- 1. Process Sender (Outgoing Traffic) ---
    for event in sender.get("send_events", []):
        target_ip = event.get("to")
        block_id = event.get("block")
        
        # Update Per PC stats
        pc_stats[target_ip][block_id]['sent'] += 1
        
        # Update Global/Block stats
        total_sent += 1
        block_stats[block_id]['sent'] += 1

    # --- 2. Process Receivers (Incoming Traffic) ---
    # We attempt to match receivers to the IPs the sender sent to. 
    # Since the receiver objects list might not have an ID, we iterate and aggregate.
    
    # Helper to find where a received block belongs
    # In a real scenario, we map a receiver object to an IP. 
    # Here, we assume the receivers list corresponds to the target IPs found in sender 
    # OR we simply aggregate all received packets matching the sender's origin.
    
    for i, receiver in enumerate(receivers):
        # specific_receiver_ip = receiver.get("ip", f"Unknown_Receiver_{i}") 
        # Note: Without an explicit IP in the receiver object, we must rely on 
        # the sender's data to define the 'Target PC'. 
        
        for event in receiver.get("receive_events", []):
            # We only care about packets coming FROM our Sender
            if event.get("from") == sender_ip:
                block_id = event.get("block")
                delay = event.get("delay_ms", 0)
                
                # Logic: We credit this received packet to the PC stats.
                # Since we don't know which PC 'receiver' is from the struct,
                # we have to find a PC that was expecting this block.
                # (Simple approach: Credit to the first PC expecting this block that hasn't received it yet, 
                # or simpler: Aggregate delays globally if mapping is impossible).
                
                # For this implementation, we will update Global and Block stats accurately.
                # For PC stats, we will aggregate delays based on the block mapping.
                
                total_received += 1
                all_delays.append(delay)
                
                block_stats[block_id]['received'] += 1
                block_stats[block_id]['delays'].append(delay)

                # Attempt to attribute to a PC (Best Effort without explicit Receiver ID)
                # We look for a target that was sent this block
                for target_ip, blocks in pc_stats.items():
                    if block_id in blocks:
                        # We attribute the delay/receipt here for the sake of the "Per PC" view
                        blocks[block_id]['received'] += 1
                        blocks[block_id]['delays'].append(delay)
                        break 

    # --- 3. Calculate Final Metrics ---

    # A. Overall Metrics
    overall_loss = ((total_sent - total_received) / total_sent * 100) if total_sent > 0 else 0
    overall_avg_delay = (sum(all_delays) / len(all_delays)) if all_delays else 0

    results = {
        "overall": {
            "packet_loss_percent": round(overall_loss, 2),
            "average_delay_ms": round(overall_avg_delay, 2),
            "total_sent": total_sent,
            "total_received": total_received
        },
        "per_block": {},
        "per_pc": {}
    }

    # B. Per Block Metrics
    for blk, data in block_stats.items():
        loss = ((data['sent'] - data['received']) / data['sent'] * 100) if data['sent'] > 0 else 0
        avg_d = (sum(data['delays']) / len(data['delays'])) if data['delays'] else 0
        results["per_block"][blk] = {
            "loss_percent": round(loss, 2),
            "avg_delay_ms": round(avg_d, 2)
        }

    # C. Per PC Metrics
    for ip, blocks in pc_stats.items():
        pc_sent = sum(b['sent'] for b in blocks.values())
        pc_recv = sum(b['received'] for b in blocks.values())
        pc_delays = [d for b in blocks.values() for d in b['delays']]
        
        loss = ((pc_sent - pc_recv) / pc_sent * 100) if pc_sent > 0 else 0
        avg_d = (sum(pc_delays) / len(pc_delays)) if pc_delays else 0
        
        results["per_pc"][ip] = {
            "loss_percent": round(loss, 2),
            "avg_delay_ms": round(avg_d, 2),
            "sent": pc_sent,
            "received": pc_recv
        }

    return results

# --- Usage Example ---

# Mock Data based on your description
sender_data = {
    "send_events": [
        {"time": 1764735293385, "block": 1, "to": "172.19.0.1"},
        {"time": 1764735293385, "block": 1, "to": "172.19.0.8"}, # Sending block 1 to two places
        {"time": 1764735293386, "block": 2, "to": "172.19.0.1"},
    ],
    "receive_events": []
}

# List of receivers (assuming they capture the events)
receivers_data = [
    {
        "send_events": [],
        "receive_events": [
            # This looks like Receiver 172.19.0.1 receiving Block 1
            {"time": 1764739593053, "block": 1, "from": "172.19.0.0", "delay_ms": 15, "length": 51224},
             # This looks like Receiver 172.19.0.1 receiving Block 2
            {"time": 1764739593055, "block": 2, "from": "172.19.0.0", "delay_ms": 10, "length": 51224},
        ]
    },
    {
        "send_events": [],
        "receive_events": [
             # This looks like Receiver 172.19.0.8 receiving Block 1
             # Note: If this list was empty, Packet Loss for .8 would be 100%
            {"time": 1764739593053, "block": 1, "from": "172.19.0.0", "delay_ms": 22, "length": 51224},
        ]
    }
]

metrics = calculate_network_metrics(sender_data, receivers_data, sender_ip="172.19.0.0")

import json
print(json.dumps(metrics, indent=4))