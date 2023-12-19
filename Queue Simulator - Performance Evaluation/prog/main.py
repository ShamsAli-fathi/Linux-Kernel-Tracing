import numpy as np
import pandas as pd
import functions
import plotting

if __name__ == '__main__':
    print("Sim Start...")

    number_of_users = 1000
    entryInterval = functions.timeGenerate(1,number_of_users)

    serviceTimeSum = 0

    performanceEvaluation = {
        'WQ':[],
        'LQ':[],
        'p':  [],
        'L': [],
        'ES': [],
        'W': [],
        'QueueNumber': []
    }

    statisticalCounters = {
        'numberServiced':[0],     #or being serviced.
        'totalDelay':[0],
        'Qt':  [0],
        'Bt': [0],
        'clock': [0]
    }


    performanceEvaluation_df = functions.make_pd(performanceEvaluation)

    branchQueues = functions.branches()

    """
    The following section is for the first Queue.
    """
    print("Queue #1 Processing...")
    currentTime = 0

    serviceTime = functions.timeGenerate(2, number_of_users)

    #used for all users' avg service time
    serviceTimeSum += sum(serviceTime)

    statisticalCounters_df1 = functions.make_pd(statisticalCounters)

    #first snapshot
    eventList = functions.eventList(
        nextEntry = entryInterval[0],
        endOfService = float('inf'),
        EI_index = 1,
        ST_index = 0)

    #QueueSim for 'first' Queue
    statisticalCounters_df1, expectedServiceStart, actualServiceStart, branchQueues = functions.snapshotCreate(eventList,
        entryInterval, serviceTime, statisticalCounters_df1, branchQueues, branching = 1, useBranchAsEntry=0)

    plotting.entryPlot(list(range(1, len(actualServiceStart)+1)), expectedServiceStart, actualServiceStart, '1')
    plotting.statisticalCountersPlot(statisticalCounters_df1, '1')


    performanceEvaluation_df = functions.performanceEvaluationCalc(
        statisticalCounters_df1.iloc[-1], serviceTime, performanceEvaluation_df, 1) #We only pass the last row

    """
    The following section is for the second Queue.
    """
    print("Queue #2 Processing...")
    serviceTime = functions.timeGenerate(4, len(branchQueues.branch2))
    serviceTimeSum += sum(serviceTime)

    statisticalCounters_df2 = functions.make_pd(statisticalCounters)

    # first snapshot/ Eventlist Reset
    eventList = functions.eventList(
        nextEntry = branchQueues.branch2[0],
        endOfService=float('inf'),
        EI_index=1,
        ST_index=0)

    # QueueSim for 'second' Queue
    statisticalCounters_df2, expectedServiceStart, actualServiceStart, _ = functions.snapshotCreate(
        eventList, branchQueues.branch2, serviceTime, statisticalCounters_df2, [], branching=0, useBranchAsEntry=1)

    plotting.entryPlot(list(range(1, len(actualServiceStart) + 1)), expectedServiceStart, actualServiceStart, '2')
    plotting.statisticalCountersPlot(statisticalCounters_df2, '2')

    performanceEvaluation_df = functions.performanceEvaluationCalc(
        statisticalCounters_df2.iloc[-1], serviceTime, performanceEvaluation_df, 2)  # We only pass the last row

    """
        The following section is for the third Queue.
    """
    print("Queue #3 Processing...")
    serviceTime = functions.timeGenerate(3, len(branchQueues.branch3))
    serviceTimeSum += sum(serviceTime)

    statisticalCounters_df3 = functions.make_pd(statisticalCounters)

    # first snapshot/ Eventlist Reset
    eventList = functions.eventList(
        nextEntry=branchQueues.branch3[0],
        endOfService=float('inf'),
        EI_index=1,
        ST_index=0)

    # QueueSim for 'third' Queue
    statisticalCounters_df3, expectedServiceStart, actualServiceStart, _ = functions.snapshotCreate(
        eventList, branchQueues.branch3, serviceTime, statisticalCounters_df3, [], branching=0, useBranchAsEntry=1)

    plotting.entryPlot(list(range(1, len(actualServiceStart) + 1)), expectedServiceStart, actualServiceStart, '3')
    plotting.statisticalCountersPlot(statisticalCounters_df3, '3')

    performanceEvaluation_df = functions.performanceEvaluationCalc(
        statisticalCounters_df3.iloc[-1], serviceTime, performanceEvaluation_df, '3')  # We only pass the last row

    #######################################

    plotting.performanceEvaluationPlot(performanceEvaluation_df)

    print()
    with pd.option_context('display.max_rows', None,
                           'display.max_columns', None,
                           'display.precision', 5,
                           ):
        print(performanceEvaluation_df)

    print("Avg of service time for users: " + str(sum(performanceEvaluation_df['L'].to_list())))
    print("Avg of users in the system (N): " + str(sum(performanceEvaluation_df['W'].to_list())))

    print("Done!")

