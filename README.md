# Python Network Protocol Stack Simulator

A command-line Python project that demonstrates how application data moves
between two hosts on separate subnets through a router.

The simulator models simplified versions of:

- **Layer 4:** segmentation, checksum validation, DATA/ACK messages, and an
  alternating-bit reliable-delivery workflow
- **Layer 3:** IP-style packets, routing-table lookups, next-hop decisions, and
  TTL handling
- **Layer 2:** Ethernet-style frames, MAC-address lookup, local-hop delivery,
  and router MAC learning

> This is a logical simulator. It does not create real network traffic or use
> sockets. Devices exchange Python objects through method calls so the
> encapsulation and forwarding process can be followed step by step.

## Network topology

```text
Host A                  Router R1                   Host B
10.0.1.10        10.0.1.1 | 10.0.2.1        10.0.2.20
    |-------------------|   |-------------------|
       10.0.1.0/24              10.0.2.0/24
```

Host A and Host B are on different networks. Host A therefore sends each
frame to its default gateway, Router R1. The router removes the incoming
Layer 2 frame, checks the destination IP address, decreases the packet TTL,
selects an outgoing interface, and creates a new Layer 2 frame for Host B.
Acknowledgements return through the same process in reverse.

## What the project demonstrates

- Encapsulation and decapsulation across Layers 2, 3, and 4
- The difference between a final destination and a local next hop
- Routing between two directly connected subnets
- Layer 2 frame replacement at a router
- Static ARP-like IP-to-MAC lookup
- Router source-MAC learning
- Message segmentation using a 500-byte maximum payload
- Checksum generation and verification
- DATA and ACK handling with alternating sequence numbers
- Duplicate DATA detection and retransmission attempts
- TTL decrementing and expiry checks
- Command-line input validation

## How the simulation works

For a message larger than 500 bytes, the sender splits the data into multiple
segments. A 1,200-byte message becomes:

```text
500 bytes, sequence 0
500 bytes, sequence 1
200 bytes, sequence 0
```

For each segment:

1. Host A creates a transport segment and checksum.
2. Host A wraps the segment in an IP-like packet.
3. Host A sends an Ethernet-like frame to Router R1.
4. Router R1 validates the frame, learns the source MAC, decreases TTL, and
   performs a routing-table lookup.
5. Router R1 creates a new frame for Host B.
6. Host B validates and delivers the segment.
7. Host B sends a matching ACK back to Host A.
8. Host A advances to the next sequence number only after receiving the
   expected ACK.

## Project structure

```text
network-protocol-simulator/
├── main.py       # CLI entry point and topology creation
├── devices.py    # Host and Router behaviour
├── protocol.py   # Segment, Packet, and Frame data structures
├── config.py     # Addresses, interfaces, routes, and protocol settings
└── README.md
```

## Requirements

- Python **3.9 or newer**
- No third-party packages

## Run the simulator

From the project directory:

```bash
python3 main.py 10
```

This sends a single 10-byte DATA segment from Host A to Host B.

To demonstrate segmentation:

```bash
python3 main.py 1200
```

To view command help:

```bash
python3 main.py --help
```

## Example output excerpt

```text
Network topology: Host A -> Router R1 -> Host B
Application message size: 10 bytes

Host A: Layer 4: Segment created (DATA, seq=0) (encapsulation)
Host A: Layer 3: Next-hop IP determined: 10.0.1.1
Host A: Layer 2: Frame created: SRC_MAC=AA:AA:AA:AA:AA:AA, DST_MAC=BB:BB:BB:BB:BB:BB
Router R1: Layer 3: TTL decremented: 100 -> 99
Router R1: Layer 3: Outgoing interface selected (Interface 2)
Host B: Layer 4: DATA segment delivered to Application Layer. Data size=10
Host A: Layer 4: ACK received: seq=0

Simulation completed successfully.
```

## Verification performed

The project has been run with:

- a **10-byte** message to verify one-segment end-to-end delivery
- a **1,200-byte** message to verify segmentation into 500, 500, and 200
  bytes with alternating sequence numbers and matching ACKs
- invalid values such as zero, negative numbers, and non-integer input to
  verify command-line validation

## Design limitations

The project intentionally simplifies real networking:

- No real sockets, packet capture, or operating-system network interfaces
- No dynamic ARP, DHCP, DNS, NAT, or routing protocols
- Fixed topology and static routing/MAC tables
- Simplified packet headers and checksum algorithm
- No simulated random packet loss or corruption
- Synchronous method calls rather than asynchronous transmission

These constraints keep the focus on protocol layering, routing decisions, and
reliable-delivery logic.

## Skills demonstrated

- Python programming and object-oriented design
- Computer networking fundamentals
- TCP/IP-style layering and routing concepts
- Input validation and defensive checks
- Technical documentation
- Structured testing and troubleshooting

## Portfolio note

This implementation was originally developed as a university networking
project and was later cleaned, documented, and refined for portfolio use. The
repository contains the implementation only and does not include assignment
instructions, marking guides, lecturer material, or private university files.
