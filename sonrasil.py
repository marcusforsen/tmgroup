import pandas as pd

# Load the CSV files
voiso_summitlife_df = pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\voiso summitlife.csv')
voiso_traling_df = pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\voiso traling.csv')
coperato_traling_df = pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\coperato traling.csv')
coperato_signix_df = pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\coperato Signix.csv')
voicespin_df = pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\voicespin.csv')

# Strip any extra whitespace from column names
voiso_summitlife_df.columns = voiso_summitlife_df.columns.str.strip()
voiso_traling_df.columns = voiso_traling_df.columns.str.strip()
coperato_traling_df.columns = coperato_traling_df.columns.str.strip()
coperato_signix_df.columns = coperato_signix_df.columns.str.strip()
voicespin_df.columns = voicespin_df.columns.str.strip()

# Function to get unique counts from DataFrame
def get_unique_counts(df, column_name, agent_column):
    return df.groupby(agent_column)[column_name].nunique()

# Get unique counts for each file
unique_counts_voiso_summitlife = get_unique_counts(voiso_summitlife_df, 'DNIS/To', 'Agent(s)')
unique_counts_voiso_traling = get_unique_counts(voiso_traling_df, 'DNIS/To', 'Agent(s)')
unique_counts_coperato_traling = coperato_traling_df.groupby('Agent(s)')['Unique'].sum()
unique_counts_coperato_signix = coperato_signix_df.groupby('Agent(s)')['Unique'].sum()
unique_counts_voicespin = get_unique_counts(voicespin_df, 'CALL ID', 'Agent(s)')

# Function to print the first 10 agents with their unique call counts
def print_unique_counts(agent_list, unique_counts, source_name):
    print(f"\nUnique Call Counts from {source_name}:")
    for agent in agent_list:
        if agent in unique_counts:
            print(f"Agent: {agent}, Unique Calls: {unique_counts[agent]}")
        else:
            print(f"Agent: {agent} not found in unique counts.")

# Get the first 10 agents from each source
def get_first_10_agents(unique_counts):
    return unique_counts.head(10)

first_10_agents_voiso_summitlife = get_first_10_agents(unique_counts_voiso_summitlife)
first_10_agents_voiso_traling = get_first_10_agents(unique_counts_voiso_traling)
first_10_agents_coperato_traling = get_first_10_agents(unique_counts_coperato_traling)
first_10_agents_coperato_signix = get_first_10_agents(unique_counts_coperato_signix)
first_10_agents_voicespin = get_first_10_agents(unique_counts_voicespin)

# Print unique counts for the first 10 agents from each source
print_unique_counts(first_10_agents_voiso_summitlife.index, unique_counts_voiso_summitlife, 'voiso summitlife')
print_unique_counts(first_10_agents_voiso_traling.index, unique_counts_voiso_traling, 'voiso traling')
print_unique_counts(first_10_agents_coperato_traling.index, unique_counts_coperato_traling, 'coperato traling')
print_unique_counts(first_10_agents_coperato_signix.index, unique_counts_coperato_signix, 'coperato Signix')
print_unique_counts(first_10_agents_voicespin.index, unique_counts_voicespin, 'voicespin')
