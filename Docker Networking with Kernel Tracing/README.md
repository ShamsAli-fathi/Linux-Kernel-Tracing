# STILL IN PROGRESS / NOT COMPLETE

# Description

In this project, my goal is to employ tracing techniques to analyze the functionality of distinct Docker networking modes. Subsequently, I intend to assess and trace each mode using Linux tracing tools.

## Tools

- Ubuntu 20.04 focal

  > Kernel 5.15.0

- Ubuntu 22.04 Jammy
  > Kernel 6.2.0

> Both VirtualMachine and Native OS is being used.

- bpftrace

- Perf

- Netcat

- ftrace

## User-Defined Bridge

User-defined bridge mode in Docker allows us to create our own custom bridge networks for container communication. When we create a Docker container, it gets connected to a network by default. Docker uses bridge networking to enable communication between containers on the same host.

The goal is to make a private network and put a container in it that runs the Ubuntu image.

```
docker network create networkName
```

```
docker run -itd --rm --network networkName --name containerName ubuntu
```

Our goal is to establish a connection between the host machine and a container. We'll accomplish this by sending TCP packets using netcat and then examining the outcomes. To begin, we'll initiate netcat to send TCP packets within the host's loopback interface (its internal communication mechanism). Next, we'll contrast this setup with our Docker scenario, observing how TCP packets behave when sent between the host and a container. This comparison will help us understand and evaluate the differences in network communication between these two setups.

> Netcat is explained thoroughly in repo's _Kernel Net Tracing_ project.

The host loopback tracing is as followed:

![host base perf count](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Docker%20Networking%20with%20Kernel%20Tracing/src/Base/nc%20perf%20count.png)

Moreover, the Docker tracing:

![UDB perf count](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Docker%20Networking%20with%20Kernel%20Tracing/src/UDB/ncscript_perf_udb.png)

We can see that there is no significant difference between the two. But let's delve into one of the events; _netif_rx_.

Using perf, we record the related stack of both.

```
perf record -ae 'net:*' --call-graph fp
```

![perf UDB compare stack](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Docker%20Networking%20with%20Kernel%20Tracing/src/UDB/perf_stack%20comparison.png)

> both stacks are in _sending phase_

The highlighted yellow parts are the functions that differ.

In the context of Docker, the **br_forward** function might be involved when Docker containers communicate with the host machine or other containers within the same bridge network.

When a Docker container sends TCP packets to the host, these packets traverse the network stack, including the bridge network created by Docker, to reach their destination. The bridge network allows containers to communicate with each other and with the host. The forwarding destination is determined based on the MAC address. The loopback interface operates internally within the system and does not involve actual physical network hardware. Instead of going through physical network adapters, loopback traffic stays within the operating system itself. Hence, the absence of **br_forward**.

Also, looking at the function graph, we can see the order of function calls:

![function graph UDB compare stack](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Docker%20Networking%20with%20Kernel%20Tracing/src/UDB/UDB_functiongraph.png)

It is also worth mentioning that the _br_forward_ related set of function calls have an extra cumulative time of **20 us** in **docker=>netcat** process . This information would come handy when we compare it with the same scenario in our host loopback tracing; and this is only one tiny part of the added overhead.

## IPVLAN L2

In Docker networking, IPVLAN L2 (Layer 2) mode is a networking configuration where containers share the same MAC address as the host. Containers within an IPVLAN L2 network utilize the same MAC address as the Docker host's interface. This shared MAC addressing scheme means that all the containers within this mode present the same MAC address.

The host acts like a network switch. However, the shared MAC address can lead to increased ARP broadcasts, impacting network performance due to the shared MAC addressing nature of the containers.

The first step is to create an IPVLAN L2 network:

```
docker network create -d ipvlan --subnet x.x.x.0/24 --gateway x.x.x.x -o parent=enp0s3 networkName
```

Followed by setting up a container in this network:

```
docker run -itd --rm --network networkName --ip x.x.x.x --name containerName ubuntu
```

> The given IPs are new and not used in the system.

![IPVLAN L2 docker ps](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Docker%20Networking%20with%20Kernel%20Tracing/src/IPVLAN2/IPVLAN2_Dockerps.jpg)

If we use VM, we are also able to ping our VM container from own computer and demonstrate the shared MAC address:

![vm Mac](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Docker%20Networking%20with%20Kernel%20Tracing/src/IPVLAN2/IPVLAN2_addshMac.png)

![host ping/mac](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Docker%20Networking%20with%20Kernel%20Tracing/src/IPVLAN2/IPVLAN2_cmd_ping.png)

Then we proceed to run 2 **ubuntu:20.04** containers in the same network on a **Native Ubuntu OS**. The goal is to send TCP packets between them and trace the result.

Comparing the perf event count of docker and host in this scenario reveals that sending packets between docker containers completely lack _netif_rx_ but overall, other stats do not differ.

## Overlay

The overlay network driver creates a distributed network among multiple Docker daemon hosts. This network sits on top of (overlays) the host-specific networks, allowing containers connected to it (including swarm service containers) to communicate securely when encryption is enabled. Docker transparently handles routing of each packet to and from the correct Docker daemon host and the correct destination container.

> Official Docker Documentation

The goal is to have 2 different machines with Native Ubuntu OS communicate with eachother through this network and moreover, trace and understand how overlaying in docker works. More importantly, we will assess the overhead using _bpftrace_.

First we connect our machines to a shared local network. Then we create a cluster using **Docker Swarm**; swarm mode is an advanced feature for managing a cluster of Docker daemons. We initialize the swarm in our _manager node_. These nodes are responsible for controlling the swarm and scheduling services:

```
docker swarm init --data-path-addr [NetworkInterface or IP]
```

This command gives us a token, enabling worker nodes to join the swarm. _Worker nodes_ execute the tasks assigned to them by the manager nodes. They run the containers that make up the services in the swarm:

```
docker swarm join --token [GeneratedToken]
```

Enabling this mode automatically creates 2 new networks:

| Prompt          | Description                                                                              |
| --------------- | ---------------------------------------------------------------------------------------- |
| ingress         | it handles the control and data traffic related to swarm services                        |
| docker_gwbridge | it connects the individual Docker daemon to the other daemons participating in the swarm |

To create an **overlay** network for use with swarm services:

```
docker network create -d overlay NetworkName
```

When run in manager node, this network will be created on both machines.

Next we set up our containers:

```
docker service create --name ServiceName --network NetworkName --replicas 2 alpine sleep 1d
```

From this point on, we have 2 containers on 2 machines deployed in an overlay network.

We run 2 experiments: one being an **intra-host ping** and the other being and **intra-container ping**. In the former experiment we simply ping one machine from the other one since they are connected to o local network. In the latter, we ping one container from another container and it is possible due to both docker containers being deployed in an overlay network.

In order to analyze and compare these two experiments, we record a **perf stack**:

![overlay stack compare](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Docker%20Networking%20with%20Kernel%20Tracing/src/Overlay/overlay_base_docker_stack_compare_startxmit.png)

We can now see how overlay network works. Based on this comparison and considering the number of calls to the **br_nf_forward** method and its purpose, we realize that despite the apparent connection of all containers on different Docker hosts to a common bridge and the communication between them being purely Layer 2 through a shared ARP table, the implementation of this method is different.

Initially, the network card of the system acting as the creator of the swarm manages the bridges of other Docker containers. It looks as if it plays the role of the main bridge, but in reality, all bridges of related Docker containers are pairwise connected to each other, forming a full mesh. Each Docker container's MAC address is subjected to NAT (Network Address Translation) with the MAC address of the Docker installed on it. As a result, packets first reach their Docker bridge, where they are directed to the desired bridge based on the destination MAC address. As both broadcast communication between all containers and NAT-ed packets within each bridge are feasible, addressing and communication between containers are made possible.

In simpler terms, despite the appearance of all containers being connected to a shared bridge, the setup actually involves a full mesh of bridges between related Docker containers. Each container's MAC address undergoes NAT translation with the Docker's MAC address it runs on, allowing communication through the respective bridges.

### Bpftrace overhead evaluation

By writing a simple **Bpftrace**, we can now attach _kprobes_ to our function calls:

In our own scenario, by comparing the exported perf stack and using ftrace function graph, we decide our function kprobes.

During a 20-second intra-contrainer pinging, we can at last export a time histogram; calculating the time it takes to send one ping message.

## Acknowledgments/References

- [Deep Linux](https://www.youtube.com/@deeplinux2248)
- [The Linux Kernel documentation](https://docs.kernel.org/)
- [Configuring IPvlan networking in Docker](<https://4sysops.com/archives/configuring-ipvlan-networking-in-docker/#:~:text=L2%20(or%20Layer%202)%20mode,virtual%20NIC%20for%20each%20container.>)
- [Docker Doc](https://docs.docker.com)

- Lots of thanks to AmirHossein Ghaffari
  [AmirHossein's Github](https://github.com/Amirhghaffari)
