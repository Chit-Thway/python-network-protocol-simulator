"""Static configuration for the network protocol stack simulator.

The simulator models two hosts on separate /24 networks connected by a
single router. Address-resolution data is intentionally stored in fixed
lookup tables so the project can focus on encapsulation, routing, forwarding,
and reliable delivery behaviour.
"""

from typing import Final

# General protocol settings
DEFAULT_TTL: Final[int] = 100
MAX_SEGMENT_DATA_SIZE: Final[int] = 500
MAX_RETRANSMISSIONS: Final[int] = 2
DEFAULT_SRC_PORT: Final[int] = 5000
DEFAULT_DST_PORT: Final[int] = 80
DIRECT_NEXT_HOP: Final[str] = "DIRECT"

# Device names
HOST_A: Final[str] = "Host A"
HOST_B: Final[str] = "Host B"
ROUTER_R1: Final[str] = "Router R1"

# IP addresses
HOST_A_IP: Final[str] = "10.0.1.10"
HOST_B_IP: Final[str] = "10.0.2.20"
ROUTER_R1_IF1_IP: Final[str] = "10.0.1.1"
ROUTER_R1_IF2_IP: Final[str] = "10.0.2.1"

# MAC addresses
HOST_A_MAC: Final[str] = "AA:AA:AA:AA:AA:AA"
HOST_B_MAC: Final[str] = "DD:DD:DD:DD:DD:DD"
ROUTER_R1_IF1_MAC: Final[str] = "BB:BB:BB:BB:BB:BB"
ROUTER_R1_IF2_MAC: Final[str] = "CC:CC:CC:CC:CC:CC"

# Interface names
INTERFACE_1: Final[str] = "Interface 1"
INTERFACE_2: Final[str] = "Interface 2"

# Host routing tables
HOST_A_ROUTING_TABLE = (
    {
        "network": "10.0.1.0/24",
        "interface": INTERFACE_1,
        "next_hop": None,
    },
    {
        "network": "10.0.2.0/24",
        "interface": INTERFACE_1,
        "next_hop": ROUTER_R1_IF1_IP,
    },
)

HOST_B_ROUTING_TABLE = (
    {
        "network": "10.0.2.0/24",
        "interface": INTERFACE_2,
        "next_hop": None,
    },
    {
        "network": "10.0.1.0/24",
        "interface": INTERFACE_2,
        "next_hop": ROUTER_R1_IF2_IP,
    },
)

# Router routing table. Both networks are directly connected.
ROUTER_R1_ROUTING_TABLE = (
    {
        "network": "10.0.1.0/24",
        "interface": INTERFACE_1,
        "next_hop": DIRECT_NEXT_HOP,
    },
    {
        "network": "10.0.2.0/24",
        "interface": INTERFACE_2,
        "next_hop": DIRECT_NEXT_HOP,
    },
)

# Static MAC lookup tables. These simulate ARP-like resolution.
HOST_A_MAC_TABLE = {
    ROUTER_R1_IF1_IP: ROUTER_R1_IF1_MAC,
    HOST_A_IP: HOST_A_MAC,
}

HOST_B_MAC_TABLE = {
    ROUTER_R1_IF2_IP: ROUTER_R1_IF2_MAC,
    HOST_B_IP: HOST_B_MAC,
}

ROUTER_R1_MAC_TABLE = {
    HOST_A_IP: HOST_A_MAC,
    HOST_B_IP: HOST_B_MAC,
    ROUTER_R1_IF1_IP: ROUTER_R1_IF1_MAC,
    ROUTER_R1_IF2_IP: ROUTER_R1_IF2_MAC,
}

# Router interface configuration
ROUTER_R1_INTERFACES = {
    INTERFACE_1: {
        "ip": ROUTER_R1_IF1_IP,
        "mac": ROUTER_R1_IF1_MAC,
    },
    INTERFACE_2: {
        "ip": ROUTER_R1_IF2_IP,
        "mac": ROUTER_R1_IF2_MAC,
    },
}
