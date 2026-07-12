"""Command-line entry point for the network protocol stack simulator."""

import argparse
from typing import Tuple

from config import (
    HOST_A,
    HOST_A_IP,
    HOST_A_MAC,
    HOST_A_MAC_TABLE,
    HOST_A_ROUTING_TABLE,
    HOST_B,
    HOST_B_IP,
    HOST_B_MAC,
    HOST_B_MAC_TABLE,
    HOST_B_ROUTING_TABLE,
    INTERFACE_1,
    INTERFACE_2,
    ROUTER_R1,
    ROUTER_R1_INTERFACES,
    ROUTER_R1_MAC_TABLE,
    ROUTER_R1_ROUTING_TABLE,
)
from devices import Host, Router


def create_network() -> Tuple[Host, Host, Router]:
    """Create and connect the fixed Host A -> Router R1 -> Host B topology."""

    host_a = Host(
        name=HOST_A,
        ip_address_value=HOST_A_IP,
        mac_address=HOST_A_MAC,
        routing_table=HOST_A_ROUTING_TABLE,
        mac_table=HOST_A_MAC_TABLE,
    )
    host_b = Host(
        name=HOST_B,
        ip_address_value=HOST_B_IP,
        mac_address=HOST_B_MAC,
        routing_table=HOST_B_ROUTING_TABLE,
        mac_table=HOST_B_MAC_TABLE,
    )
    router_r1 = Router(
        name=ROUTER_R1,
        interfaces=ROUTER_R1_INTERFACES,
        routing_table=ROUTER_R1_ROUTING_TABLE,
        mac_table=ROUTER_R1_MAC_TABLE,
    )

    host_a.connect_router(router_r1, INTERFACE_1)
    host_b.connect_router(router_r1, INTERFACE_2)
    router_r1.connect_host(INTERFACE_1, host_a)
    router_r1.connect_host(INTERFACE_2, host_b)

    return host_a, host_b, router_r1


def parse_args() -> argparse.Namespace:
    """Parse and validate command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Simulate reliable data transfer from Host A to Host B through "
            "a router using simplified Layer 2, Layer 3, and Layer 4 protocols."
        )
    )
    parser.add_argument(
        "message_size",
        type=int,
        help="application message size in bytes (must be greater than zero)",
    )
    args = parser.parse_args()

    if args.message_size <= 0:
        parser.error("message_size must be greater than zero")

    return args


def main() -> int:
    """Run one end-to-end network simulation."""

    args = parse_args()
    host_a, _, _ = create_network()

    print("Network topology: Host A -> Router R1 -> Host B")
    print(f"Application message size: {args.message_size} bytes\n")

    try:
        host_a.send_application_data(
            destination_ip=HOST_B_IP,
            data_size=args.message_size,
        )
    except (RuntimeError, ValueError) as exc:
        print(f"Simulation failed: {exc}")
        return 1

    print("\nSimulation completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
