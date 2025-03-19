# Description

In this Lab, we aim to practice the effective use of Linux Source code reading. Reading the Linux source code helps in tracing the Linux kernel because it provides insight into how the kernel functions internally. By understanding the code, you can follow the flow of execution, identify key components like system calls.

## Assignment 1
**`struct net_device`** is a central data structure in the Linux kernel's networking subsystem. It represents a network device and contains information about the device's state, operations, and associated resources. Understanding this structure is essential for comprehending how the kernel manages network interfaces and facilitates communication between user-space applications and hardware.

The goal is to gain a comprehensive understanding of the **`struct net_device`** structure, its role in the Linux networking stack, and how it interfaces with other components. By reading Linux Source Code, do the following:

- Locate the struct net_device Definition
- Examine the struct net_device Structure
- Understand Device Operations (`netdev_ops`)
- monitor the nested function calls related to struct net_device

**HINT**: The task requires *perf* or *ftrace*. *ftrace* is recommended. 

## Assignment 2
The goal is to measure and analyze the latency involved in **packet processing** within the Linux kernel using LTTng; the time between *packet transmission* and *reception*

- There are certain tracing events that are related to packet processing. Find them and explain what they do. Be aware that such events and system calls are many; finding at least two events/system calls is enough.
- Use LTTng to perform tracing. But initially, you must generate traffic flow. Tools like ping, hping3, nc, or others can be used for this purpose.
- Analyze the trace data to measure the time between packet transmission and reception, identifying any latency in the network stack.
