"""Host and router behaviour for the network protocol stack simulator."""

from __future__ import annotations

from ipaddress import ip_address, ip_network
from typing import Any, Mapping, Optional, Sequence

from config import (
    DEFAULT_DST_PORT,
    DEFAULT_SRC_PORT,
    DEFAULT_TTL,
    DIRECT_NEXT_HOP,
    MAX_RETRANSMISSIONS,
    MAX_SEGMENT_DATA_SIZE,
)
from protocol import Frame, Packet, Segment

Route = Mapping[str, Any]


def _find_best_route(
    routing_table: Sequence[Route], destination_ip: str
) -> Optional[Route]:
    """Return the longest-prefix route matching ``destination_ip``."""

    destination = ip_address(destination_ip)
    matching_routes = [
        route
        for route in routing_table
        if destination in ip_network(str(route["network"]), strict=False)
    ]

    if not matching_routes:
        return None

    return max(
        matching_routes,
        key=lambda route: ip_network(str(route["network"]), strict=False).prefixlen,
    )


class Host:
    """Represent an end host that can send and receive simulated traffic."""

    def __init__(
        self,
        name: str,
        ip_address_value: str,
        mac_address: str,
        routing_table: Sequence[Route],
        mac_table: Mapping[str, str],
    ) -> None:
        self.name = name
        self.ip_address = ip_address_value
        self.mac_address = mac_address
        self.routing_table = routing_table
        self.mac_table = mac_table

        self.connected_router: Optional[Router] = None
        self.connected_router_interface: Optional[str] = None

        # Sender and receiver state for the alternating-bit protocol.
        self.next_seq_num = 0
        self.expected_seq_num = 0
        self.waiting_for_ack = False
        self.last_sent_segment: Optional[Segment] = None
        self.last_destination_ip: Optional[str] = None

    def connect_router(self, router: Router, router_interface: str) -> None:
        """Attach the host to one logical router interface."""

        self.connected_router = router
        self.connected_router_interface = router_interface

    # ------------------------------------------------------------------
    # Layer 4: transport
    # ------------------------------------------------------------------

    def send_application_data(self, destination_ip: str, data_size: int) -> None:
        """Segment and send an application message to ``destination_ip``."""

        if data_size <= 0:
            raise ValueError("data size must be greater than zero")

        remaining_data = data_size

        while remaining_data > 0:
            current_data_size = min(remaining_data, MAX_SEGMENT_DATA_SIZE)
            data = "X" * current_data_size

            print(
                f"{self.name}: Layer 4: Data received from Application Layer. "
                f"Data size={current_data_size}"
            )

            segment = Segment(
                src_port=DEFAULT_SRC_PORT,
                dst_port=DEFAULT_DST_PORT,
                segment_type=Segment.DATA,
                seq_num=self.next_seq_num,
                data=data,
            )

            print(f"{self.name}: Layer 4: Checksum computed")
            print(
                f"{self.name}: Layer 4: Segment created "
                f"({segment.type_name}, seq={segment.seq_num}) (encapsulation)"
            )
            print(f"{self.name}: Layer 4: Segment sent to Network Layer")

            self.last_sent_segment = segment
            self.last_destination_ip = destination_ip
            self.waiting_for_ack = True

            attempts = 0
            while self.waiting_for_ack and attempts <= MAX_RETRANSMISSIONS:
                if attempts > 0:
                    print(
                        f"{self.name}: Layer 4: Retransmitting segment "
                        f"seq={segment.seq_num} (attempt {attempts + 1})"
                    )

                self.send_network_packet(destination_ip, segment)
                attempts += 1

            if self.waiting_for_ack:
                raise RuntimeError(
                    f"{self.name} did not receive ACK seq={segment.seq_num} "
                    f"after {attempts} attempts"
                )

            remaining_data -= current_data_size

    def receive_transport_segment(self, segment: Segment, source_ip: str) -> None:
        """Verify and process a DATA or ACK segment received from Layer 3."""

        print(f"{self.name}: Layer 4: Segment received from Network Layer")

        if not segment.verify_checksum():
            print(f"{self.name}: Layer 4: Segment discarded due to checksum error")
            return

        print(f"{self.name}: Layer 4: Checksum verified")

        if segment.segment_type == Segment.DATA:
            self._process_data_segment(segment, source_ip)
            return

        self._process_ack_segment(segment)

    def _process_data_segment(self, segment: Segment, source_ip: str) -> None:
        """Deliver new DATA once and acknowledge both new and duplicate DATA."""

        if segment.seq_num == self.expected_seq_num:
            print(
                f"{self.name}: Layer 4: DATA segment delivered to Application "
                f"Layer. Data size={len(segment.data.encode('utf-8'))}"
            )
            self.expected_seq_num = 1 - self.expected_seq_num
        else:
            print(
                f"{self.name}: Layer 4: Duplicate DATA segment received "
                f"(seq={segment.seq_num}); payload not delivered again"
            )

        ack_segment = Segment(
            src_port=segment.dst_port,
            dst_port=segment.src_port,
            segment_type=Segment.ACK,
            seq_num=segment.seq_num,
            data="",
        )

        print(
            f"{self.name}: Layer 4: Segment created "
            f"({ack_segment.type_name}, seq={ack_segment.seq_num})"
        )
        print(f"{self.name}: Layer 4: Segment sent to Network Layer")
        self.send_network_packet(source_ip, ack_segment)

    def _process_ack_segment(self, segment: Segment) -> None:
        """Accept the expected ACK and advance the sender sequence number."""

        print(f"{self.name}: Layer 4: ACK received: seq={segment.seq_num}")

        if self.waiting_for_ack and segment.seq_num == self.next_seq_num:
            self.waiting_for_ack = False
            self.last_sent_segment = None
            self.last_destination_ip = None
            self.next_seq_num = 1 - self.next_seq_num
            return

        print(
            f"{self.name}: Layer 4: Unexpected or duplicate ACK ignored "
            f"(seq={segment.seq_num})"
        )

    # ------------------------------------------------------------------
    # Layer 3: network
    # ------------------------------------------------------------------

    def send_network_packet(self, destination_ip: str, segment: Segment) -> None:
        """Encapsulate a segment, choose a route, and pass it to Layer 2."""

        packet = Packet(
            src_ip=self.ip_address,
            dst_ip=destination_ip,
            payload=segment,
            ttl=DEFAULT_TTL,
        )

        print(
            f"{self.name}: Layer 3: Segment received from Transport Layer: "
            f"SRC_IP={self.ip_address}, DST_IP={destination_ip}, TTL={packet.ttl}"
        )
        print(f"{self.name}: Layer 3: Destination IP read: {destination_ip}")

        route = self.lookup_route(destination_ip)
        print(f"{self.name}: Layer 3: Routing table lookup performed")

        if route is None:
            print(f"{self.name}: Layer 3: No route found. Packet dropped")
            return

        next_hop = route["next_hop"]
        next_hop_ip = destination_ip if next_hop is None else str(next_hop)

        print(f"{self.name}: Layer 3: Next-hop IP determined: {next_hop_ip}")
        print(
            f"{self.name}: Layer 3: Outgoing interface selected "
            f"({route['interface']})"
        )
        print(f"{self.name}: Layer 3: Packet forwarded to Data Link Layer")
        self.send_data_link_frame(packet, next_hop_ip)

    def receive_network_packet(self, packet: Packet) -> None:
        """Deliver a packet locally when its destination matches this host."""

        print(
            f"{self.name}: Layer 3: Packet received from Data Link Layer: "
            f"SRC_IP={packet.src_ip}, DST_IP={packet.dst_ip}, TTL={packet.ttl}"
        )
        print(f"{self.name}: Layer 3: Destination IP read: {packet.dst_ip}")

        if packet.dst_ip != self.ip_address:
            print(f"{self.name}: Layer 3: Packet is not for this host. Packet dropped")
            return

        print(f"{self.name}: Layer 3: Packet identified as local delivery")
        print(f"{self.name}: Layer 3: Segment delivered to Transport Layer")
        self.receive_transport_segment(packet.payload, packet.src_ip)

    # ------------------------------------------------------------------
    # Layer 2: data link
    # ------------------------------------------------------------------

    def send_data_link_frame(self, packet: Packet, next_hop_ip: str) -> None:
        """Create a frame for the next local hop and deliver it to the router."""

        print(f"{self.name}: Layer 2: Packet received from Network Layer")

        destination_mac = self.mac_table.get(next_hop_ip)
        if destination_mac is None:
            print(
                f"{self.name}: Layer 2: Destination MAC lookup failed for "
                f"next-hop IP ({next_hop_ip}). Frame dropped"
            )
            return

        print(
            f"{self.name}: Layer 2: Destination MAC lookup for next-hop IP "
            f"({next_hop_ip}) -> {destination_mac}"
        )

        frame = Frame(
            src_mac=self.mac_address,
            dst_mac=destination_mac,
            payload=packet,
        )

        print(
            f"{self.name}: Layer 2: Frame created: "
            f"SRC_MAC={self.mac_address}, DST_MAC={destination_mac}"
        )
        print(f"{self.name}: Layer 2: Frame sent")

        if self.connected_router is None or self.connected_router_interface is None:
            raise RuntimeError(f"{self.name} is not connected to a router")

        self.connected_router.receive_frame(frame, self.connected_router_interface)

    def receive_frame(self, frame: Frame) -> None:
        """Validate a frame destination and pass its packet to Layer 3."""

        print(f"{self.name}: Layer 2: Frame received")

        if frame.dst_mac != self.mac_address:
            print(
                f"{self.name}: Layer 2: Frame destination MAC does not match. "
                f"Frame dropped"
            )
            return

        print(f"{self.name}: Layer 2: Source MAC observed: {frame.src_mac}")
        print(f"{self.name}: Layer 2: Packet delivered to Network Layer")
        self.receive_network_packet(frame.payload)

    def lookup_route(self, destination_ip: str) -> Optional[Route]:
        """Return the best matching host route for a destination address."""

        return _find_best_route(self.routing_table, destination_ip)


class Router:
    """Represent a router that forwards packets between connected networks."""

    def __init__(
        self,
        name: str,
        interfaces: Mapping[str, Mapping[str, str]],
        routing_table: Sequence[Route],
        mac_table: Mapping[str, str],
    ) -> None:
        self.name = name
        self.interfaces = interfaces
        self.routing_table = routing_table
        self.mac_table = mac_table
        self.connected_hosts: dict[str, Host] = {}
        self.learned_mac_table: dict[str, str] = {}

    def connect_host(self, interface: str, host: Host) -> None:
        """Attach a logical host to one router interface."""

        if interface not in self.interfaces:
            raise ValueError(f"unknown router interface: {interface}")
        self.connected_hosts[interface] = host

    # ------------------------------------------------------------------
    # Layer 2: data link
    # ------------------------------------------------------------------

    def receive_frame(self, frame: Frame, incoming_interface: str) -> None:
        """Validate an incoming frame, learn its source, and pass it to Layer 3."""

        print(f"{self.name}: Layer 2: Frame received on {incoming_interface}")

        interface = self.interfaces.get(incoming_interface)
        if interface is None:
            print(f"{self.name}: Layer 2: Unknown incoming interface. Frame dropped")
            return

        if frame.dst_mac != interface["mac"]:
            print(
                f"{self.name}: Layer 2: Frame is not addressed to "
                f"{incoming_interface}. Frame dropped"
            )
            return

        self.learned_mac_table[frame.src_mac] = incoming_interface
        print(
            f"{self.name}: Layer 2: Source MAC learned: "
            f"{frame.src_mac} on {incoming_interface}"
        )
        print(f"{self.name}: Layer 2: Packet delivered to Network Layer")
        self.receive_network_packet(frame.payload)

    def send_data_link_frame(
        self, packet: Packet, next_hop_ip: str, outgoing_interface: str
    ) -> None:
        """Create a new frame and deliver it through the selected interface."""

        print(f"{self.name}: Layer 2: Packet received from Network Layer")

        destination_mac = self.mac_table.get(next_hop_ip)
        if destination_mac is None:
            print(
                f"{self.name}: Layer 2: Destination MAC lookup failed for "
                f"next-hop IP ({next_hop_ip}). Frame dropped"
            )
            return

        interface = self.interfaces.get(outgoing_interface)
        if interface is None:
            print(f"{self.name}: Layer 2: Unknown outgoing interface. Packet dropped")
            return

        print(
            f"{self.name}: Layer 2: Destination MAC lookup for next-hop IP "
            f"({next_hop_ip}) -> {destination_mac}"
        )

        frame = Frame(
            src_mac=interface["mac"],
            dst_mac=destination_mac,
            payload=packet,
        )

        print(
            f"{self.name}: Layer 2: Frame created: "
            f"SRC_MAC={frame.src_mac}, DST_MAC={frame.dst_mac}"
        )
        print(f"{self.name}: Layer 2: Frame forwarded on {outgoing_interface}")

        next_device = self.connected_hosts.get(outgoing_interface)
        if next_device is None:
            print(
                f"{self.name}: Layer 2: No connected device on "
                f"{outgoing_interface}. Frame dropped"
            )
            return

        next_device.receive_frame(frame)

    # ------------------------------------------------------------------
    # Layer 3: network
    # ------------------------------------------------------------------

    def receive_network_packet(self, packet: Packet) -> None:
        """Decrease TTL, choose a route, and forward the packet."""

        print(
            f"{self.name}: Layer 3: Packet received from Data Link Layer: "
            f"SRC_IP={packet.src_ip}, DST_IP={packet.dst_ip}, TTL={packet.ttl}"
        )
        print(f"{self.name}: Layer 3: Destination IP read: {packet.dst_ip}")

        previous_ttl = packet.ttl
        packet.decrement_ttl()
        print(
            f"{self.name}: Layer 3: TTL decremented: "
            f"{previous_ttl} -> {packet.ttl}"
        )

        if packet.is_expired():
            print(f"{self.name}: Layer 3: Packet dropped due to TTL expiry")
            return

        route = self.lookup_route(packet.dst_ip)
        print(f"{self.name}: Layer 3: Routing table lookup performed")

        if route is None:
            print(f"{self.name}: Layer 3: No route found. Packet dropped")
            return

        outgoing_interface = str(route["interface"])
        next_hop = route["next_hop"]
        next_hop_ip = (
            packet.dst_ip if next_hop == DIRECT_NEXT_HOP else str(next_hop)
        )

        print(f"{self.name}: Layer 3: Next-hop IP determined: {next_hop_ip}")
        print(
            f"{self.name}: Layer 3: Outgoing interface selected "
            f"({outgoing_interface})"
        )
        print(f"{self.name}: Layer 3: Packet forwarded to Data Link Layer")
        self.send_data_link_frame(packet, next_hop_ip, outgoing_interface)

    def lookup_route(self, destination_ip: str) -> Optional[Route]:
        """Return the best matching router route for a destination address."""

        return _find_best_route(self.routing_table, destination_ip)
