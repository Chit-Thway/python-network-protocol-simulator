"""Protocol data structures used by the network simulator.

Each class models the header and payload information used at one layer:

- ``Segment``: simplified Layer 4 transport segment
- ``Packet``: simplified Layer 3 IP packet
- ``Frame``: simplified Layer 2 Ethernet frame
"""

from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class Segment:
    """Represent a simplified UDP-like DATA or ACK segment."""

    DATA: ClassVar[int] = 0
    ACK: ClassVar[int] = 1
    HEADER_SIZE: ClassVar[int] = 10

    src_port: int = 0
    dst_port: int = 0
    segment_type: int = DATA
    seq_num: int = 0
    data: str = ""
    length: int = field(init=False)
    checksum: int = field(init=False)

    def __post_init__(self) -> None:
        if not 0 <= self.src_port <= 65535:
            raise ValueError("source port must be between 0 and 65535")
        if not 0 <= self.dst_port <= 65535:
            raise ValueError("destination port must be between 0 and 65535")
        if self.segment_type not in (self.DATA, self.ACK):
            raise ValueError("segment type must be DATA or ACK")
        if self.seq_num not in (0, 1):
            raise ValueError("sequence number must be 0 or 1")

        data_size = len(self.data.encode("utf-8"))
        self.length = self.HEADER_SIZE + data_size
        self.checksum = self.compute_checksum()

    def compute_checksum(self) -> int:
        """Compute a small deterministic checksum for demonstration purposes."""

        header_total = (
            self.src_port
            + self.dst_port
            + self.length
            + self.segment_type
            + self.seq_num
        )
        payload_total = sum(self.data.encode("utf-8"))
        return (header_total + payload_total) % 256

    def verify_checksum(self) -> bool:
        """Return ``True`` when the stored checksum is still valid."""

        return self.checksum == self.compute_checksum()

    @property
    def type_name(self) -> str:
        """Return a readable segment type name."""

        return "DATA" if self.segment_type == self.DATA else "ACK"


@dataclass
class Packet:
    """Represent a simplified IPv4-like packet."""

    UDP_PROTOCOL: ClassVar[int] = 17
    HEADER_SIZE: ClassVar[int] = 12

    src_ip: str
    dst_ip: str
    payload: Segment
    ttl: int = 100
    protocol: int = field(default=UDP_PROTOCOL, init=False)
    total_length: int = field(init=False)

    def __post_init__(self) -> None:
        if self.ttl <= 0:
            raise ValueError("TTL must be greater than zero when a packet is created")
        self.total_length = self.HEADER_SIZE + self.payload.length

    def decrement_ttl(self) -> None:
        """Decrease the packet TTL by one hop."""

        self.ttl -= 1

    def is_expired(self) -> bool:
        """Return ``True`` when the packet TTL has reached zero."""

        return self.ttl <= 0


@dataclass
class Frame:
    """Represent a simplified Ethernet-like frame."""

    IPV4_TYPE: ClassVar[int] = 0x0800

    src_mac: str
    dst_mac: str
    payload: Packet
    frame_type: int = field(default=IPV4_TYPE, init=False)
