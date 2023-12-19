# STILL IN PROGRESS / NOT COMPLETE

# Description

In this project, my goal is to employ tracing techniques to analyze the functionality of distinct Docker networking modes. Subsequently, I intend to assess and trace each mode using Linux tracing tools.

## Tools

- Ubuntu 20.04 focal

> Both VirtualMachine and Native OS is being used.

> Kernel 5.15.0

- LTTng V2.12

- TraceCompass V9.0.0

- Perf

- Netcat

> The Network is bridged in VM.

## User-Defined Bridge

User-defined bridge mode in Docker allows us to create our own custom bridge networks for container communication. When we create a Docker container, it gets connected to a network by default. Docker uses bridge networking to enable communication between containers on the same host.

The goal is to make a private network and put a container in it that runs the Ubuntu image.

```
sudo docker network create networkName
```

```
sudo docker run -itd --rm --network networkName --name containerName ubuntu
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
sudo perf record -ae 'net:*' --call-graph fp
```

![perf UDB compare stack](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Docker%20Networking%20with%20Kernel%20Tracing/src/UDB/perf_stack%20comparison.png)

> both stacks are in _sending phase_

The highlighted yellow parts are the functions that differ.

In the context of Docker, the **br_forward** function might be involved when Docker containers communicate with the host machine or other containers within the same bridge network.

When a Docker container sends TCP packets to the host, these packets traverse the network stack, including the bridge network created by Docker, to reach their destination. The bridge network allows containers to communicate with each other and with the host. The forwarding destination is determined based on the MAC address. The loopback interface operates internally within the system and does not involve actual physical network hardware. Instead of going through physical network adapters, loopback traffic stays within the operating system itself. Hence, the absence of **br_forward**.

Also, looking at the function graph, we can see the order of function calls:

![function graph UDB compare stack](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Docker%20Networking%20with%20Kernel%20Tracing/src/UDB/UDB_functiongraph.png)

It is also worth mentioning that the _br_forward_ related set of function calls have an extra cumulative time of **3 us** in **docker=>netcat** process . This information would come handy when we compare it with the same scenario in our host loopback tracing; and this is only one tiny part of the added overhead.

## IPVLAN L2

In Docker networking, IPVLAN L2 (Layer 2) mode is a networking configuration where containers share the same MAC address as the host. Containers within an IPVLAN L2 network utilize the same MAC address as the Docker host's interface. This shared MAC addressing scheme means that all the containers within this mode present the same MAC address.

The host acts like a network switch. However, the shared MAC address can lead to increased ARP broadcasts, impacting network performance due to the shared MAC addressing nature of the containers.

The first step is to create an IPVLAN L2 network:

```
sudo docker network create -d ipvlan --subnet x.x.x.0/24 --gateway x.x.x.x -o parent=enp0s3 networkName
```

Followed by setting up a container in this network:

```
sudo docker run -itd --rm --network networkName --ip x.x.x.x --name containerName ubuntu
```

> The given IPs are new and not used in the system.

![IPVLAN L2 docker ps](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Docker%20Networking%20with%20Kernel%20Tracing/src/IPVLAN2/IPVLAN2_Dockerps.jpg)

If we use VM, we are also able to ping our VM container from own computer and demonstrate the shared MAC address:

![vm Mac](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Docker%20Networking%20with%20Kernel%20Tracing/src/IPVLAN2/IPVLAN2_addshMac.png)

![host ping/mac](https://github.com/ShamsAli-fathi/Linux-Kernel-Tracing/blob/main/Docker%20Networking%20with%20Kernel%20Tracing/src/IPVLAN2/IPVLAN2_cmd_ping.png)

Then we proceed to run 2 **ubuntu:20.04** containers in the same network. The goal is to send TCP packets between them and trace the result.

Comparing the perf event count of docker and host in this scenario reveals that sending packets between docker containers completely lack _netif_rx_ but overall, other stats do not differ.

## IPVLAN L3

## Acknowledgments/References

- [Deep Linux](https://www.youtube.com/@deeplinux2248)
- [The Linux Kernel documentation](https://docs.kernel.org/)
- [Configuring IPvlan networking in Docker](<https://4sysops.com/archives/configuring-ipvlan-networking-in-docker/#:~:text=L2%20(or%20Layer%202)%20mode,virtual%20NIC%20for%20each%20container.>)
