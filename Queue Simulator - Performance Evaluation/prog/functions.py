import numpy as np
import pandas as pd
import random

"""
eventlist includes the next user entry and the time the current service gets finished.
"""
class eventList:
    def __init__(self, nextEntry, endOfService, EI_index, ST_index):
        self.nextEntry = nextEntry
        self.endOfService = endOfService
        self.EI_index = EI_index
        self.ST_index = ST_index

"""
Used for branch queues.
"""
class branches:
    def __init__(self):
        self.branch2 = []
        self.branch3 = []

"""
Creates the intial dataframe for all statistical Counters/Flags
"""
def make_pd(df_arg):
    df = pd.DataFrame(df_arg)
    return df

"""
snapshotCreate is our main function. It runs the Queue simulation
"""
def snapshotCreate(eventList, entry, serviceTime, statisticalCounters_df, branchQueues, branching, useBranchAsEntry):
    #This Loop section calculates the time every user expects to start getting serviced. This is considered in an ideal scenario
    #where every user will start being serviced the moment they enter the queue.
    #Branching indicates whether we need to branch to other queues or not.
    #useBranchAsEntry indicates whether entry object is passed as an interval time or actual entry time.
    queue = 0
    currentTime = 0

    if useBranchAsEntry == 0:
        running_sum = 0
        EntryTime = []  # can also be called "expectedServiceStart"
        for value in entry:
            running_sum += value
            EntryTime.append(running_sum)
    else:   #if useBranchAsEntry == 1:
        EntryTime = entry   #here, entry is actually not interval anymore. It's the actual Entry times, but passed to the function under this object.

    actualServiceStart = [] #The time each user actually starts getting service.


    """
    The simulation is divided into 3 groups:
    1. Queue is empty and we must wait for an entry.
    2. Queue is not empty and another user is being serviced. But an entry occurs.
    2. Queue is not empty and the previous user's service is finished.
    """
    while not(eventList.nextEntry == float('inf') and eventList.endOfService == float('inf')):
        if eventList.endOfService == float('inf'):

            closestTime = min(eventList.nextEntry, eventList.endOfService)
            timeDifference = closestTime - currentTime
            currentTime = closestTime

            if eventList.EI_index < len(entry):
                eventList.nextEntry = EntryTime[eventList.EI_index]
            else:
                eventList.nextEntry = float('inf')
            eventList.endOfService = serviceTime[eventList.ST_index] + currentTime

            stat_acc = stat_acc_calculation(
                timeDifference, queue, currentTime, serviceBool=1, totalDelayBool=1) #ServiceBool: a new service is started     totalDelayBool: Delay time should be calculated
            statisticalCounters_df = statisticalCountersModify(
                statisticalCounters_df,stat_acc, EntryTime, currentTime)    #modifies statisticalCounters

            actualServiceStart.append(currentTime)

            eventList.EI_index += 1
            eventList.ST_index += 1
            queue +=1

        else:
            closestTime = min(eventList.nextEntry, eventList.endOfService)
            timeDifference = closestTime - currentTime
            currentTime = closestTime
            if queue > 0:
                if currentTime == eventList.nextEntry :
                    stat_acc = stat_acc_calculation(timeDifference, queue, currentTime, serviceBool=0, totalDelayBool=0)
                    statisticalCounters_df = statisticalCountersModify(
                        statisticalCounters_df, stat_acc, EntryTime, currentTime)
                    if eventList.EI_index < len(entry):
                        eventList.nextEntry = EntryTime[eventList.EI_index]
                    else:
                        eventList.nextEntry = float('inf')
                    queue += 1
                    eventList.EI_index += 1


                if currentTime == eventList.endOfService:

                    if branching == 1:
                        branchQueues = nextBranch(branchQueues, currentTime)

                    queue -= 1
                    if queue > 0:   #Queue has user for next service
                        stat_acc = stat_acc_calculation(timeDifference, queue+1, currentTime, serviceBool=1, totalDelayBool=1)
                        statisticalCounters_df = statisticalCountersModify(
                            statisticalCounters_df, stat_acc, EntryTime, currentTime)

                        actualServiceStart.append(currentTime)
                        eventList.endOfService += serviceTime[eventList.ST_index]
                        eventList.ST_index += 1
                    else:           #Queue empty for next service
                        stat_acc = stat_acc_calculation(timeDifference, queue+1, currentTime, serviceBool=0, totalDelayBool=0)
                        statisticalCounters_df = statisticalCountersModify(
                            statisticalCounters_df, stat_acc, EntryTime, currentTime)

                        eventList.endOfService = float('inf')

    return statisticalCounters_df, EntryTime, actualServiceStart, branchQueues

"""
For each snapshot, we add the statistical Counters to the dataframe. it uses "stat_acc" to calculate the stats for the new row.
"""
def statisticalCountersModify(df,stat_acc, EntryTime, currentTime):
    last_row_array = df.iloc[-1].values

    if stat_acc[1] == 1:    #stat_acc[1] refers to totalDelay
        intervalIndex = int(df.iloc[-1]['numberServiced'])
        stat_acc[1] = currentTime - EntryTime[intervalIndex]
    else:
        stat_acc[1] = 0

    stat_acc[0:4] = last_row_array[0:4] + stat_acc[0:4]

    df.loc[len(df.index)] = stat_acc
    return df

"""
It calculates a set of numbers accordingly, in order to update the statisticalCounters dataframe.
returns
"""
def stat_acc_calculation(timeDifference, queue, currentTime, serviceBool, totalDelayBool):
    l = []

    if queue > 0:
        Bt = timeDifference
    else:
        Bt = 0
    if timeDifference != float('inf') :
        Qt = max((queue-1,0)) * timeDifference
    else:
        Qt = 0

    clock = currentTime

    l.extend([serviceBool, totalDelayBool, Qt, Bt, clock])

    return l

def timeGenerate(scale,size):   #Generates time intervals/service time based on an exponential dist
    x = np.random.exponential(scale, size)
    rand_nums = list(map(lambda item: round(item, 1), x)) #Round(number, precision)
    return rand_nums

def performanceEvaluationCalc(df, serviceTime, performanceEvaluation_df, queueNumber):
    WQ = df['totalDelay'] / df['numberServiced']
    LQ = df['Qt'] / df['clock']
    p = df['Bt'] / df['clock']
    L = LQ + p
    ES = sum(serviceTime) / df['numberServiced']
    W = WQ + ES

    new_row = [WQ, LQ, p, L, ES, W, queueNumber]
    performanceEvaluation_df.loc[len(performanceEvaluation_df)] = new_row
    return performanceEvaluation_df

def nextBranch(branches, entry):
    branch_choice = random.choices([1,2], [0.4,0.6], k=1)[0]

    if branch_choice == 1:
        branches.branch2.append(entry)
    else:
        branches.branch3.append(entry)

    return branches