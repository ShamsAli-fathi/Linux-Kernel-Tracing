# Description

In this lab, we will use perf to trace SYN and UDP scans, providing insights into network performance. Additionally, we will employ Trace Compass to analyze how Maximum Transmission Unit (MTU) affects network communication.

## Assignment 1
**SYN and UDP scans** are common techniques used in network reconnaissance to identify open ports on a target system. A SYN scan, often referred to as a "half-open" scan, involves sending a SYN packet to a target port. If the port is open, the target responds with a SYN-ACK packet, which the scanner acknowledges with an RST packet, completing the process without establishing a full TCP connection. This method is stealthy and efficient, as it doesn't complete the TCP handshake, making it less detectable by intrusion detection systems.

In contrast, a UDP scan involves sending UDP packets to target ports. Since UDP is a connectionless protocol, the absence of a response typically indicates that the port is open, while an ICMP "port unreachable" message suggests that the port is closed. However, this method can be less reliable due to the stateless nature of UDP and the potential for firewalls to block ICMP messages.

**hping3** is a versatile network tool designed for crafting and sending custom TCP/IP packets. It supports various protocols, including TCP, UDP, and ICMP, and allows users to manipulate packet headers and payloads to test network security and performance. hping3 can be used for tasks such as port scanning, traceroute, and network performance testing, making it a valuable tool for network administrators and security professionals.

- Utilize hping3 to perform separate scans on IP address 8.8.8.8: one using the SYN flag and another using the UDP protocol.
> Try to include a data (payload) to the message. This helps getting past Google's firewall. If by any chance you were unsuccessful, scan your localhost.

> Use port 53 for UDP scan.

> Read hping3's documentation for more help!

- Using perf, first identify the network-related tracepoints and events being triggered. Then, record a tracing session with perf and analyze both SYN and UDP scans. Select one event and compare both scan methods and explain the difference fully and with details.

## Assignment 2
**MTU (Maximum Transmission Unit)** is the largest size of a data packet that can be transmitted over a network interface, without needing to be fragmented. It is typically measured in bytes. The MTU defines the maximum payload that can be carried in a single network packet for a given network link, including both the data and the headers.

For example, the default MTU for Ethernet networks is typically 1500 bytes. If a packet exceeds the MTU of the network, it may be fragmented into smaller packets, which can affect performance. Adjusting MTU settings can optimize network performance and reduce overhead in specific network configurations.

> Using a tool of your choice (e.g., Ping), send a payload larger than the specified MTU value. The goal is to trigger fragmentation.

> Trace the process with LTTng and visualize the results using TraceCompass.

> Clearly demonstrate how fragmentation appears in the trace.

> Can you also determine the length of the transmitted message in TraceCompass by analyzing the provided tracing events?