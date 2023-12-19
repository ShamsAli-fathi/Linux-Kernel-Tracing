# Description

In these experiments, I will take a close look at the kernel's TCP/IP network stack code. This will involve examining the codebase in detail, including how network protocols, socket handling, packet processing, and network stack optimization work. The aim of these experiments is to gain a deep understanding of the kernel's networking infrastructure.

## Tools

- Ubuntu 20.04 focal

> VirtualMachine is being used.

> Kernel 5.15.0

- LTTng V2.12

- TraceCompass V9.0.0

- Perf

- fTrace

## Experiment 1

The Linux network stack has a few key data structures. **struct sk_buff** and **struct sock** are two of them. By code inspecting these data
structures, we aim to understand how they work and where they are referenced.

### Struct sk_buff

```C
#Linux Source Code

struct sk_buff {
    union {
        struct {
            struct sk_buff *next;
            struct sk_buff *prev;
            union {
                struct net_device *dev;
                unsigned long dev_scratch;
            };
        };
        struct rb_node rbnode;
        struct list_head list;
    };
    union {
        struct sock *sk;
        int ip_defrag_offset;
    };
    union {
        ktime_t tstamp;
        u64 skb_mstamp_ns;
    };
    char cb[48] __aligned(8);
    union {
        struct {
            unsigned long _skb_refdst;
            void (*destructor)(struct sk_buff *skb);
        };
        struct list_head tcp_tsorted_anchor;
    };
};

```

The **struct sk_buff** (socket buffer) is a fundamental data structure in the Linux kernel networking stack. It represents a network packet as it travels through the kernel's network processing code. Each sk_buff carries information about the packet, its source and destination, and various control information. Let's break down the structure and its components:

1. Linked List Pointers (**next** and **prev**):
   These pointers are used to link sk_buff structures in various lists, such as the free list or the list of queued packets waiting for processing.

2. Network Device (**dev**):
   Represents the network device associated with the packet. It points to the device on which the packet was received or is intended to be transmitted.

3. Red-Black Tree Node (**rbnode**):
   Used in specific scenarios, such as network emulation (netem), IPv4 defragmentation, and the TCP stack. It allows efficient insertion and deletion in a sorted order.

4. List Node (list):
   Another way to link sk_buff structures in a list, used in some contexts.

5. Socket (sk):
   Points to the socket associated with the packet. This is used in networking protocols that are tied to sockets, such as TCP.

6. Timestamp (tstamp and skb_mstamp_ns):

   - **tstamp**: Represents the timestamp of when the packet was processed.
   - **skb_mstamp_ns**: Represents the earliest departure time for the packet.

7. Control Buffer (**cb**):
   A space for private variables used by various networking layers. Different layers can use this buffer for their specific needs.

8. Miscellaneous Fields (\_skb_refdst and destructor):
   - **\_skb_refdst**: Used in reference counting mechanisms for destination address references. Using this field, the lifecycle of objects is managed.
   - **destructor**: A function pointer to a destructor function for the sk_buff. It is called when the reference count drops to zero.

#### Struct References:

_sk_buff_ can be passed between layers, and if a layer wants to keep it beyond its current scope, it needs to perform a skb_clone() to create a new reference.

References to struct sk_buff are found throughout the Linux kernel networking stack. Here are a few examples:

- In network device drivers (net/core/dev.c).
- In network protocols like TCP and UDP.
- In packet scheduling and queuing mechanisms.

### Struct Sock

**Struct Sock** is basically a network layer representation of sockets. It contains common fields for all protocols, such as the address family, state, reuse options, and more. Following these common fields, protocol-specific fields and function pointers are included for protocols like TCP and UDP.

#### Fields:

- **skc_family**: Indicates the type of addresses that can be used with the socket.
- **skc_state**: Represents the current state of the socket.
- **skc_reuseport**: Allows multiple sockets to bind to the same port for load balancing or parallel processing.
- **skc_reuse**: Additional reuse option for the socket.
- **skc_incoming_cpu**: Represents the CPU core that owns the socket.
- **skc_bound_dev_if**: Allows binding a socket to a specific network interface.

## Experiment 2

Let's dive into how TCP handles an incoming SYN request, exploring the process step by step.

At first, using _hping3_ package, we start a **SYN flooding**. The purpose behind flooding is to have lots of SYN requests, making our exploration much easier!

```console
hping3 -c 100 -d 120 -S -w 64 -p 80 --flood --rand-source localhost
```

![FuncProfile](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Kernel%20Network%20Stack%20Code%20Inspection/src/Wireshark_SYN.png)

```
echo 'net* tcp*' > set_ftrace_filter
echo 0 > function_profile_enabled
echo 1 > function_profile_enabled
echo 0 > function_profile_enabled
cd trace_stat
cat function*
```

![FuncProfile](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Kernel%20Network%20Stack%20Code%20Inspection/src/tcp_ftrace_funcProfile.png)

It is obvious that a couple of functions are called a significant number of times during the flooding process; which indicate the raise of related TCP functions.

- tcp_v4_rcv
- tcp_v4_send_reset
- tcp_v4_fill_cb

![FuncGraph](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Kernel%20Network%20Stack%20Code%20Inspection/src/FuncGraph_tcp.png)

**tcp_v4_rcv** is the main entry point for delivery of datagrams from the IP layer. It processes TCP packet received by the kernel.
After looking up an established TCP connection based on the packet's source and destination information and generating a hash value for it, we listen for incoming connections.

in **tcp_v4_fill_cb**, we populate the the fields in socket buffer with appropriate values taken from TCP packet.

Finally, in **tcp_v4_send_reset**, the invalid incoming packet is dropped and TCP reset packet is sent.

Also after using _Lttng_ to trace the events and exporting them in _TraceComapass_, we have the following report.

![TC TCP](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Kernel%20Network%20Stack%20Code%20Inspection/src/TC_TCP.png)

The packet is transmitted and processed from the buffer and later on, the buffer is cleared.

| Prompt              | Description                                                                                                                                                  |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| _netif_receive_skb_ | the main receive data processing function. It always succeeds. The buffer may be dropped during processing for congestion control or by the protocol layers. |
| _skb_kfree_         | Release anything attached to the buffer. Clean the state.                                                                                                    |

![netIf](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Kernel%20Network%20Stack%20Code%20Inspection/src/Netif_rcv_SC.png)

## Experiment 3

In the Linux kernel networking stack, communication between different layers is facilitated through a set of APIs (Application Programming Interfaces) that allow for the seamless transfer of data and control information. Our goal here is to trace and find these APIs between tcp layers.

### Link Layer (L2) to Network Layer (L3) API:

We could make use of a simple prediction. Prior to tracing itself, we could think of what to expect for each API. For link layer and network layer, we think that it might have to do something with transmitting and receiving frames and then, socket buffering and receiving packets. Hence the following filters for **ftrace**:

```
echo 'net*' > set_graph_function
echo 'skb*' >> set_graph_function
echo 'ip*' >> set_graph_function
echo 'sock*' >> set_graph_function
```

![Skb_push](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Kernel%20Network%20Stack%20Code%20Inspection/src/skb_push.png)

**skb_push** adds data to an sk_buff. Later on, **dev_queue_xmit** is called; which is responsible for transmitting frames onto the network. It is used to enqueue frames for transmission.

**netif_receive_skb** is part of the function calls in this layer, which was thoroughly explained previously.

### Network Layer (L3) to Transport Layer (L4) API:

![ip_rcv](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Kernel%20Network%20Stack%20Code%20Inspection/src/ip_rcv.png)

A set of **ip\_** functions are called. **ip_rcv** is the key function and is responsible for handling incoming IP packets. it performs tasks such as packet validation, routing, and handing over the packet to the appropriate transport layer protocol.

### Transport Layer (L4) to Application Layer API:

The Transport Layer is responsible for providing reliable and connection-oriented communication (TCP) or unreliable and connectionless communication (UDP). The primary API for interaction with the Transport Layer is the Socket API. It provides a set of functions and data structures for creating, configuring, and managing network sockets.

![sock_poll](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Kernel%20Network%20Stack%20Code%20Inspection/src/Sock_poll.png)

The Socket API includes functions and data structures for managing network sockets. Sockets are used to represent endpoints for communication between applications over a network. Sockets abstract the details of the underlying transport protocol, allowing applications to communicate without needing to know the intricacies of the transport layer.

By looking at the trace, we can see that **sock_poll** is called many times. The _sock_poll_ function is part of the Linux kernel's socket API, and it is used for polling on a socket to check its status or readiness for certain operations. This function allows applications or kernel components to wait for specific events on a socket without actively blocking the execution of the program.

Also, after socket polling is finished, another function call is due: **sockfd_lookup_light**:

_sockfd_lookup_light_ has a lower load compared to _sockfd_lookup_. It basically goes from a file number to its socket slot

![sock2](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Kernel%20Network%20Stack%20Code%20Inspection/src/sock2.png)

Before heading to application layer, it finally creates sockets and binds them to specific addresses and ports.

The aforementioned **tcp_v4_rcv** processes the incoming TCP segments and the data is passed up to the Application Layer for further processing by the application.

## Experiment 4

In networking and operating system design, interrupts play a crucial role in handling the reception of packets. When a network interface card (NIC) receives a new packet, it triggers an interrupt to notify the operating system kernel that data is available for processing.

For instance, the actual interrupt handler is within a **irq_enter_rcu** and **irq_exit_rcu** pair.

![irq pair](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Kernel%20Network%20Stack%20Code%20Inspection/src/irq_pair.png)=

_irq_enter_rcu_ updates the preemption count. (Preemption refers to the ability of the kernel to be interrupted while running a task, allowing another task of equal priority to be scheduled. The preemption count is a counter that helps maintain the integrity of this preemption mechanism.)

_irq_exit_rcu_ on the other hand, undoes the preemption count update and manages soft interrupts.

## Experiment 5

**Memory allocation** for an arriving packet in the Linux kernel typically involves several stages. The precise details can vary depending on the networking stack, the type of packet, and the specific subsystems involved.

We know that in terms of allocation, socket buffer is of essence; for it is the very first thing that requires allocation in the memory. Then let's loop up the Kernel source code to find what we should delve into.

Anything related to memory allocation in kernel has mostly the keyword _alloc_ in its function name. Memory for the _sk_buff_ is allocated dynamically. The allocation may involve calling functions like _alloc_skb_

```C
struct sk_buff *__alloc_skb(unsigned int size, gfp_t gfp_mask,
			    int flags, int node)
{
	struct kmem_cache *cache;
	struct skb_shared_info *shinfo;
	struct sk_buff *skb;
	u8 *data;
	bool pfmemalloc;

	cache = (flags & SKB_ALLOC_FCLONE)
		? skbuff_fclone_cache : skbuff_head_cache;

	if (sk_memalloc_socks() && (flags & SKB_ALLOC_RX))
		gfp_mask |= __GFP_MEMALLOC;

	skb = kmem_cache_alloc_node(cache, gfp_mask & ~__GFP_DMA, node);
	if (!skb)
		goto out;
	prefetchw(skb);

	size = SKB_DATA_ALIGN(size);
	size += SKB_DATA_ALIGN(sizeof(struct skb_shared_info));
	data = kmalloc_reserve(size, gfp_mask, node, &pfmemalloc);
	if (!data)
		goto nodata;

	size = SKB_WITH_OVERHEAD(ksize(data));
	prefetchw(data + size);

	memset(skb, 0, offsetof(struct sk_buff, tail));

	skb->truesize = SKB_TRUESIZE(size);
	skb->pfmemalloc = pfmemalloc;
	refcount_set(&skb->users, 1);
	skb->head = data;
	skb->data = data;
	skb_reset_tail_pointer(skb);
	skb->end = skb->tail + size;
	skb->mac_header = (typeof(skb->mac_header))~0U;
	skb->transport_header = (typeof(skb->transport_header))~0U;

	shinfo = skb_shinfo(skb);
	memset(shinfo, 0, offsetof(struct skb_shared_info, dataref));
	atomic_set(&shinfo->dataref, 1);

	if (flags & SKB_ALLOC_FCLONE) {
		struct sk_buff_fclones *fclones;

		fclones = container_of(skb, struct sk_buff_fclones, skb1);

		skb->fclone = SKB_FCLONE_ORIG;
		refcount_set(&fclones->fclone_ref, 1);

		fclones->skb2.fclone = SKB_FCLONE_CLONE;
	}
out:
	return skb;
nodata:
	kmem_cache_free(cache, skb);
	skb = NULL;
	goto out;
}
EXPORT_SYMBOL(__alloc_skb);

```

This function returns a pointer to the allocated _sk_buff_ on success and returns NULL on failure. Also, the memory allocation priority/behavior is specified with **gfp_t** parameter.

In networking, **GFP_ATOMIC** is a crucial flag, where processing packets often are not allowed to sleep or get blocked.

![skballoc](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Kernel%20Network%20Stack%20Code%20Inspection/src/memoryAlloc.png)

# Acknowledgments/References

- [Deep Linux](https://www.youtube.com/@deeplinux2248)
- [Firewall.cx](https://www.firewall.cx/tools-tips-reviews/network-protocol-analyzers/performing-tcp-syn-flood-attack-and-detecting-it-with-wireshark.html)
