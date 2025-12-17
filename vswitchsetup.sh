#!/bin/bash
set -e

BRIDGE="br0"
NETWORK="172.19.0"
MTU=1500

# 1️⃣ Delete old bridge if exists
ovs-vsctl --if-exists del-br $BRIDGE

# 2️⃣ Create bridge
ovs-vsctl add-br $BRIDGE
ip link set dev $BRIDGE up
ovs-vsctl set bridge $BRIDGE stp_enable=false

# 3️⃣ Loop to create veth pairs and attach to bridge
for i in $(seq 0 15); do
    VETH="veth$i"
    PEER="peer$i"
    IP_ADDR="$NETWORK.$((i+1))/24"

    # Delete old veth if exists
    ip link del $VETH 2>/dev/null || true

    # Create veth pair
    ip link add $VETH type veth peer name $PEER

    # Attach one end to bridge
    ovs-vsctl add-port $BRIDGE $VETH
    ip link set dev $VETH up

    # Configure IP on peer
    ip addr add $IP_ADDR dev $PEER
    ip link set dev $PEER up

    # Set MTU
    ip link set dev $VETH mtu $MTU
    ip link set dev $PEER mtu $MTU
done

# 4️⃣ Test connectivity
echo "Bridge and interfaces configured. Ping test:"
for i in $(seq 1 16); do
    ping -c 1 "$NETWORK.$i" >/dev/null 2>&1 && echo "$NETWORK.$i reachable" || echo "$NETWORK.$i unreachable"
done

echo "Setup complete. You can now run your TCP gossip program."
