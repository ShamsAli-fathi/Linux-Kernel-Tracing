import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def entryPlot(x,y1,y2,queueNumber):
    sns.lineplot(x=x, y=y1, label="Expected Service Start", color='blue')
    sns.lineplot(x=x, y=y2, label="Actual Service Start", color='red')

    plt.xlabel("User #")
    plt.ylabel("Time")
    plt.title("Service Start Comparison for queue number #" + queueNumber)
    plt.legend()

    #for i in range(len(x)):
        #plt.plot([0, x[i]], [y2[i], y2[i], ], linestyle='--', color='orange', linewidth=0.5)

    name = 'entryPlot' + queueNumber
    #plt.savefig(name, dpi=300)
    plt.show()

def statisticalCountersPlot(df, queueNumebr):
    sns.lineplot(x=df['clock'], y=df['Qt'], drawstyle="steps-post", color='black', label='Qt')
    plt.fill_between(x=df['clock'], y1=df['Qt'], step="post", color='orange', alpha=0.5)
    plt.xlabel("Time")
    plt.ylabel("Qt Acumulated Values")
    plt.title("statistical Counters for queue number #"+ queueNumebr)

    name = 'statisticalCountersPlot' + queueNumebr
    #plt.savefig(name, dpi=300)
    plt.show()


def performanceEvaluationPlot(df):
    # Melt the DataFrame to have a 'Category' column for the different statistics
    melted_df = pd.melt(df, id_vars=['QueueNumber'], value_vars=['WQ', 'LQ', 'p', 'L', 'ES', 'W'],
                        var_name='Category', value_name='Values')

    sns.set(style="whitegrid")  # Optional: Set a background style

    ax = sns.barplot(x='QueueNumber', y='Values', hue='Category', data=melted_df)

    ax.set_ylabel('Values')
    ax.set_title('Performance Evaluation for Each Queue')

    #plt.savefig('performanceEvaluationPlot.png', dpi=300)
    plt.show()
