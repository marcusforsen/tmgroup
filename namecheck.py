import pandas as pd
from fuzzywuzzy import process

# Load datasets
agent_list_df = pd.read_excel(r'C:\Users\marcus.forsen\Desktop\new project\agent-listT.xlsx')
voiso_traling_df = pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\voiso traling.csv')
voiso_summitlife_df = pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\voiso summitlife.csv')
coperato_traling_df = pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\coperato traling.csv')
coperato_signix_df = pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\coperato signix.csv')

# Standardize agent names to title case
def standardize_names(df, column):
    df[column] = df[column].str.strip().str.title()

standardize_names(agent_list_df, 'AGENTNAME')
standardize_names(voiso_traling_df, 'Agent(s)')
standardize_names(voiso_summitlife_df, 'Agent(s)')
standardize_names(coperato_traling_df, 'Name')
standardize_names(coperato_signix_df, 'Name')

# Function to get unmatched names
def find_unmatched_names(df1, df2, col1, col2):
    names_df1 = set(df1[col1].dropna().unique())
    names_df2 = set(df2[col2].dropna().unique())
    
    unmatched_df1 = names_df1 - names_df2
    unmatched_df2 = names_df2 - names_df1

    return {
        'unmatched_in_df1': unmatched_df1,
        'unmatched_in_df2': unmatched_df2
    }

# Find unmatched names between datasets
def check_names_in_datasets():
    unmatched_agent_list_traling = find_unmatched_names(agent_list_df, voiso_traling_df, 'AGENTNAME', 'Agent(s)')
    unmatched_agent_list_summitlife = find_unmatched_names(agent_list_df, voiso_summitlife_df, 'AGENTNAME', 'Agent(s)')
    unmatched_agent_list_traling_coperato = find_unmatched_names(agent_list_df, coperato_traling_df, 'AGENTNAME', 'Name')
    unmatched_agent_list_signix = find_unmatched_names(agent_list_df, coperato_signix_df, 'AGENTNAME', 'Name')
    
    print("Unmatched names in agent-listT vs. voiso_traling:")
    print(unmatched_agent_list_traling)
    
    print("Unmatched names in agent-listT vs. voiso_summitlife:")
    print(unmatched_agent_list_summitlife)
    
    print("Unmatched names in agent-listT vs. coperato_traling:")
    print(unmatched_agent_list_traling_coperato)
    
    print("Unmatched names in agent-listT vs. coperato_signix:")
    print(unmatched_agent_list_signix)

check_names_in_datasets()

# Optional: Further actions based on results
# You might want to merge, clean, or manually review unmatched names.
