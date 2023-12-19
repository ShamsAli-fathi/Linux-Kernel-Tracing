# Description

Consider a queuing network composed of three queues, with the time distribution between entering the first queue and the service time for all queues determined by their unique exponential rates. The goal is to write a simulation program that, after the model reaches a steady state, calculates its performance metrics.

![Queue Figure](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Queue%20Simulator%20-%20Performance%20Evaluation/src/QueueFigure.png)

> The scripts are located in ["prog" folder](https://github.com/ShamsAli-fathi/SideProjects/tree/main/Queue%20Simulator%20-%20Performance%20Evaluation/prog)

> A set of plots from a test run are shown [here](https://github.com/ShamsAli-fathi/SideProjects/tree/main/Queue%20Simulator%20-%20Performance%20Evaluation/src)

## Tools

- Python 3.11
- Pandas 2.1.2
- Numpy 1.26.1
- Matplotlib 3.8.1
- Seaborn 0.13.0

## Simulation

The code is divided into 3 scripts: **main**, **functions** and **plotting**; and as their name suggest, they are responsible for the main execution, the classes and functions, and creating plots respectively.

### Main script

![Main1](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Queue%20Simulator%20-%20Performance%20Evaluation/src/Main1.png)

_Number of users_ is given as a variable. There is no limit to the amount of users. The time durations either for _service time_ or _user entry intervals_. Two dictionaries are created in order to be used for dataframe creation. \*\* is zeroed initially because it is directly the first row in its dataframe.

All time intervals and service times are generated ahead of time for this simulation accordingly.

_Statistical Counter_ dataframe is created 3 different times, referring to our 3 different queues; each having their own dataframe. but _Performance Evaluation_ is only created once; for we only need 3 rows for our queues.

The _main_ script is divided into 3 sections, which all 3 are similar in terms of function calling and initializing.

![Main2](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Queue%20Simulator%20-%20Performance%20Evaluation/src/Main2.png)

In each section, an _eventList_ is constructed, the snapshot creating function is called and the required plots are drawn. For this simulation, it is needed to make the first snapshot manually. Then it is passed to _snapshotCreate_ function to generate the rest of the snapshots.

Also, all users' average service time is also handled in the main script.

> Snapshots refer to the state of our simulation in each point of interest/change in time.

### Function script

![Function1](https://github.com/ShamsAli-fathi/SideProjects/blob/main/Queue%20Simulator%20-%20Performance%20Evaluation/src/Function1.png)

Two classes are defined; **eventList** and **branches**.

_eventList_ consists of 2 indicators. One shows the next timestamp where a new user enters our queue. The other one shows the time the current service gets done and finished. We also add 2 variables to hold their index numbers.

_branches_ have the responsibility to hold the time intervals for second and third queue.

**snapshotCreate** is where the magic happens! This Loop calculates the time every user expects to start getting serviced. This is considered in an ideal scenario where every user will start being serviced the moment they enter the queue. _Branching_ argument indicates whether we need to branch to other queues or not.

The function is divided into 3 groups:

- Queue is empty and we must wait for an entry.
- Queue is not empty and another user is being serviced. But an entry occurs.
- Queue is not empty and the previous user's service is finished.

First, the minimum between the next user entry and the next service finish time is calculated and assigned as _currentTime_, showing the timestamp we should proceed to for our next snapshot.

_infinity_ is also assigned to our eventList whenever the appropriate number should not be selected. For example, if the queue is empty and the next entry is yet to happen in future timestamps, we do not add a service time to our eventList. Hence, assigning infinity.

In order to know the state we are in the mentioned groups, we check to see if the _currentTime_ overlaps our entry time or service time. If _endOfService_ is an infinity, we must proceed to our next entry time. Whenever an entry occurs, our queue is added by 1.

In terms of Statistical Counters, we also calculate the accumulated values to modify our dataframe; adding a new row to it. The values needed for the next snapshot are calculated in _stat_acc_calculation_ and then they are added to the dataframe in _statisticalCountersModify_.

The index number are also iteration based on the state we are at.

After the end of each user's service, based on a certain probability, it is decided whether the user should go to queue 2 or queue 3.

### Plotting script

_entryPlot_ and _statisticalCountersPlot_ are created for each queue. A _performanceEvaluationPlot_ is also created showing a bar plot for all three queues.

The y-axis in Q(t) plot shows the value of Q(t) in each snapshot/timestamp. So it is the accumulated value.

> A set of plots from a test run are shown [here](https://github.com/ShamsAli-fathi/SideProjects/tree/main/Queue%20Simulator%20-%20Performance%20Evaluation/src)

## Acknowledgments/References

- [Pandas](https://pandas.pydata.org)
- [Seaborn](https://seaborn.pydata.org)
- [PECS Courses - Mohammad Abdollahi Azgomi](http://webpages.iust.ac.ir/azgomi)
