# Description

In the scope of this project, I will conduct elementary tracing for two distinct scenarios using the *LTTng tracer* and subsequently scrutinize the resulting trace files within the *Tracecompass* tool. My primary objectives include pinpointing the specific target application within the acquired trace data and mapping out its execution sequence. This analysis will be accompanied by relevant screenshots and logs. Furthermore, I will delve into potential performance bottlenecks and engage in a comprehensive discussion of these findings.

## Tools

* Ubuntu 20.04 focal

> VirtualMachine is being used.

> Kernel 5.15.0

* LTTng V2.12

* TraceCompass V9.0.0

* Perf

* Netcat

## Experiment 1

### Counting events

We use Perf tracing tool to observe the initiated events. Using `sudo perf list`, we determine the related events in order to observe. The *perf list* log can be seen [here](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Kernel%20Net%20Tracing/src/Perf%20List%20log.txt)

**for this experiment, we intend to trace the following events:**

* *sched_switch*
* *sched_waking*
* *sched_wakeup*
* net_*
* skb_*
* irq_*

Prompt | Description | 
--- | --- | 
*sched_switch* | used for context switching | 
*sched_waking* | a task waking up from a sleep/blocked state | 
*sched_wakeup* | a task marked as runnable |
*net* | network-related operations in the kernel | 
*skb* | Socket Buffers | 
*irq* | related to interrupt handling (soft/hard) |

We eventually run **Perf**:

```
sudo perf stat -ae 'net:*,skb:*,irq:*,sched:sched_wak*,sched:sched_switch' -I 1000
```

**The figure below is our trace log without any test Netcat server:**

![Perf Idle](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Kernel%20Net%20Tracing/src/Perf%20idle.gif)

> portion of the logged *sched* and *irq* counts are due to the recording program!

### Run Netcat
Using Ubuntu's built-in Netcat tool, we aim to open a tcp socket and listen on it.

```
nc -l 127.0.0.1 4000
```

Afterwards on a different terminal session, again using Netcat, we create a tcp client and connect to the Netcat server.

```
nc -p 4444 127.0.0.1 4000
```

Prompt | Description | 
--- | --- | 
*-l* | It is to listen for incoming connections |
*-p* | Specifies the port number |
*127.0.0.1* | The binded local IP address | 
*4000* | Port number |

Hence, a connection is established, allowing data to be sent over to the host/client.

![NC typing Gif](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Kernel%20Net%20Tracing/src/NC_type.gif)

I wrote a simple **loop shell script** and piped it with Netcat. It is done with the purpose to have our tracing counts more enganged; leading to a better demonstration!

```shell
#!/bin/bash

counter=0

while true
do
  counter=$((counter+1))
  echo "I made a TCP connetion; Loop = $counter"
  sleep 1  # Optional: Add a delay to control loop speed
done

```

 **Then:**

`sh infLoop.sh | netcat -l 127.0.0.1 4000;`

**Result:**

![NC Loop Gif](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Kernel%20Net%20Tracing/src/NC_loop.gif)

**The figure below is our trace log with Netcat server:**

![Perf NC Gif](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Kernel%20Net%20Tracing/src/NC_Perf_Log.gif)

> I altered *sleep* command in the shell file; completely removing it in order to send more rapid data!

We can clearly see the significant change in trace counts. We can now easily pinpoint the targeted kernel events.

### Creating LTTng tracing session

Having a good understanding of the events we are interested in, we can initiate the LTTng tracing session.

**We also add the following context information:**

* vpid
* vtid
* procname

Prompt | Description | 
--- | --- | 
*vpid* | Virtual Process ID | 
*vtid* | Virtual Thread ID | 
*procname* | Process Name |
*prio* | Priority |

```shell
lttng create $1 --output=/home/User/Desktop/
lttng enable-event -k --syscall --all
lttng enable-event -k sched_switch,sched_wak'*',irq_'*',net_'*',skb_'*'
lttng add-context -k -t vtid -t vpid -t procname -t prio
lttng start
sleep 10
lttng stop
lttng destroy
```

Prompt | Description | 
--- | --- | 
*-k* | Enable kernel events | 
*-t* | Virtual Thread ID | 
*--syscall* | Enable kernel events |
*--all* | All available events |

By running this script, we can trace our kernel with the given events for 10 seconds.

After our tracing is complete, we load the output folder into **TraceCompass**.



![TraceCompass_1](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Kernel%20Net%20Tracing/src/TraceCompass_1.png)

Two proccesses stand out the most: *nc* (Netcat) & *sh* (Shell script execution)

Nc keeps processing data packets rapidly.



![TraceCompass_2](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Kernel%20Net%20Tracing/src/TraceCompass_2.png)

By digging into the events raised by *nc*, we realize that the occurence of them are as the following:

* syscall_entry_poll
* syscall_exit_poll
* syscall_entry_read
* syscall_exit_read
* syscall_entry_write
* syscall_exit_write

Prompt | Description | 
--- | --- | 
*syscall_entry_poll* | used for monitoring multiple file descriptors for I/O events, such as whether they are ready for reading or writing **without blocking** | 
*syscall_entry_read* | used to read data from a file or file descriptor | 
*syscall_entry_write* | used to write data to a file or file descriptor |

We can see that *syscall_exit_poll* returns a value of **2**. Any returned number bigger than zero, refers to the number of returned file descriptors; in this case, 2.

On the other hand, the return value in *syscall_exit_read* refers to the number of bytes which were read successfully.


![TraceCompass_3](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Kernel%20Net%20Tracing/src/TraceCompass_3.jpg)

In the given picture, we can see that in the highlighted timestamp, *sched_waking* is occured and after a few cycles, it is followed by
*sched_wakeup* and a *sched_switch*. The moment *sched_switch* occurs, the resources are taken from nc process (12089). Similar **context switching** will also
occur when nc once more takes the resources.

> Arrows can be displayed that follow the execution of each CPU across processes. The arrows indicate when the scheduler switches from one process to another for a given CPU. The CPU being followed is indicated on the state tooltip. When the scheduler switches to and from the idle process, the arrow skips to the next process which executes on the CPU after the idle process.-Trace Compass Doc



Prompt | Description | 
--- | --- | 
*sched_waking* | a task is marked as "waking up" and is **about to become runnable** and **ready to run**. | 
*sched_wakeup* | a task is awakened from a sleep state and **becomes runnable** and **eligible for execution**.| 
*sched_switch* | Linux kernel switches from running one task (process or thread) to another (Context Switch). |

## Experiment 2

Next, we utilize Telnet to establish a connection with *www.google.com* and execute an HTTP GET request in the subsequent manner.

As in the previous experiment, once again we use Perf.
We will execute and analyze the traces to compare the differences. In the second experiment, increased activity involving the Wi-Fi or Ethernet interface and drivers is expected.

First, we establish the Telnet with *google* :

```console
telnet www.google.com 80
```

After our connection is successfully set, we send a simple GET message

```console
GET /search?q=hello+world
```

> This performs a simple google search

Simultaneously, we run Perf:

![Telnet Perf](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Kernel%20Net%20Tracing/src/Telnet_Perf.gif)

Now let's compare the Perf logs in Experiment 1 & 2.

We could easily see that:

* *netif_rx* is present in netcat log and absent in Telnet log.
* *napi_gro_receive_entry is present in Telnet log and absent in netcat log.



Prompt | Description | 
--- | --- | 
*netif_rx* | This function receives a packet from a device driver and queues it for the upper (protocol) levels to process. It always succeeds. | 
*napi_gro_* | a mechanism to improve the efficiency of network packet processing by aggregating multiple small packets into a single larger packet, reducing the overhead of processing individual packets. | 

## Experiment 3

This time, we redo the previous experiments, but this time, we use pinging.

First, we specify a custom packet size of 25000 bytes and we ping the default gateway:

```console
ping -s 25000 default_gateway
```

![ping fragmentation](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Kernel%20Net%20Tracing/src/Ping_Fragment.png)

Looking at *Soft_irq Network RX* in CPU5, it is obvious that fragmentation has occurred. The packet length in transmit events is *1514bytes*; which is due to MTU (14 bytes for ethernet header).


Next, we continue our experiment as we initiate a **flood ping** to our default gateway.

```console
sudo ping -f default_gateway
```

![flood ping Gateway](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Kernel%20Net%20Tracing/src/Flood_ping_gateway.png)


We can conclude that the result is the same as *Telnet* experiment. Because default gateway engages with our Network Adapter.

**irq_handler_** events refer to hardware interruptions.

In contrast, If we intend to use *localhost* instead of *default gateway*, we will not be having any forms of *hard_irq*; hence not engaging with Network Adapter. Pinging our default gateway results in more **soft_irq** and low to none **hard_irq** :

![localhost perf](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Kernel%20Net%20Tracing/src/Flood_ping_localhost.png)


> The large numbers are due to the higher ping rate for loopback address.


We could even take a look at the pie chart generated by Lttng/TraceCompass:

**Default Gateway**
![default gateway stats](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Kernel%20Net%20Tracing/src/Gateway_Stats.png)

**Localhost**
![localhost Stats](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Kernel%20Net%20Tracing/src/Localhost_stats.png)


## Acknowledgments/References

* [Deep Linux](https://www.youtube.com/@deeplinux2248)
* [Digital Ocean NetCat Tutorial](https://www.digitalocean.com/community/tutorials/how-to-use-netcat-to-establish-and-test-tcp-and-udp-connections)
* [Ubidots Netcat Tutorial](https://ubidots.com/blog/how-to-simulate-a-tcpudp-client-using-netcat/)
* [The Linux Kernel documentation](https://docs.kernel.org/)
* [Trace Compass documentation](https://archive.eclipse.org/tracecompass/doc/stable/org.eclipse.tracecompass.doc.user/LTTng-Kernel-Analysis.html)