#Marcus🗿 was here
import pandas as pd
from collections import defaultdict
import re

def extract_name(agent_str):
    """Extract the name from the agent string in 'voicespin.csv'."""
    if pd.isna(agent_str) or not isinstance(agent_str, str):
        return ''
    
    # Remove leading/trailing whitespace
    agent_str = agent_str.strip()
    
    # Split the string by '-' and take the first part
    parts = agent_str.split('-')
    if len(parts) > 1:
        name = parts[0].strip()
    else:
        name = agent_str
    
    # Remove any trailing numbers and whitespace
    name = re.sub(r'\s*\d+\s*$', '', name)
    
    return name.lower()

def is_valid_agent(agent_str):
    """Check if the agent string is a valid name (not a timestamp or other non-name value)."""
    return isinstance(agent_str, str) and agent_str.strip() != ''

def process_file(df, filename, call_attempts, file_call_attempts, conversion_agents, retention_agents, df_agents):
    """Process each file and update call attempts and agent dictionaries."""
    df.columns = df.columns.str.strip()  # Clean column names

    if filename not in file_call_attempts:
        file_call_attempts[filename] = defaultdict(int)

    if filename in ['voiso summitlife.csv', 'voiso traling.csv', 'voiso 24x.csv']:
        df['Agent_list'] = df['Agent(s)'].apply(lambda x: [name.strip().lower() for name in str(x).split('; ')] if pd.notna(x) else [])
        df = df.explode('Agent_list')
        df = df[df['Agent_list'].apply(is_valid_agent)]

        for agent in df['Agent_list']:
            file_call_attempts[filename][agent] += 1
        
        unique_counts = df.groupby('Agent_list')['DNIS/To'].nunique()
        for agent, unique_count in unique_counts.items():
            file_call_attempts[filename][f"{agent}_unique"] = unique_count

    elif filename in ['coperato traling.csv', 'coperato signix.csv', 'coperato 24x.csv']:
        df['Agent_list'] = df['Name'].apply(lambda x: x.strip().lower() if pd.notna(x) else '')
        df = df[df['Agent_list'].apply(is_valid_agent)]

        for _, row in df.iterrows():
            agent = row['Agent_list']
            attempts = row.get('Call Attempts', 0)
            unique_value = row.get('Unique', 0)
            file_call_attempts[filename][agent] += attempts
            file_call_attempts[filename][f"{agent}_unique"] = unique_value

    elif filename == 'voicespin.csv':
        if 'AGENT' in df.columns:
            df['Agent_list'] = df['AGENT'].apply(extract_name)
        elif 'Agent' in df.columns:
            df['Agent_list'] = df['Agent'].apply(extract_name)
        else:
            print(f"Error: No suitable column found for agent names in {filename}.")
            return
        
        df['Agent_list'] = df['Agent_list'].apply(lambda x: x.lower())
        agent_counts = df['Agent_list'].value_counts()
        for agent, count in agent_counts.items():
            file_call_attempts[filename][agent] = count
        
        df['Unique_CALL_ID'] = df.groupby('Agent_list')['CALL ID'].transform(lambda x: x.nunique())
        unique_counts = df.groupby('Agent_list')['Unique_CALL_ID'].max()
        for agent, unique_count in unique_counts.items():
            file_call_attempts[filename][f"{agent}_unique"] = unique_count

    df_merged = df.merge(df_agents, left_on='Agent_list', right_on='AGENTNAME', how='left')
    unmatched_agents = df_merged[df_merged['AGENTNAME'].isna()]['Agent_list']
    unmatched_agents = unmatched_agents[unmatched_agents.apply(is_valid_agent)].unique()
    
    if filename not in unmatched_agents_by_file:
        unmatched_agents_by_file[filename] = set()
    unmatched_agents_by_file[filename].update(unmatched_agents)

    # Print unmatched agents for the current file
    if unmatched_agents_by_file[filename]:
        print(f"Unmatched agents in {filename}: {', '.join(unmatched_agents_by_file[filename])}")
    else:
        print(f"No unmatched agents in {filename}.")

    for agent, attempts in file_call_attempts[filename].items():
        if not agent.endswith('_unique'):
            call_attempts[agent] += attempts
        else:
            call_attempts[agent] = file_call_attempts[filename].get(agent, 0)

    for _, row in df_merged.iterrows():
        agent = row['Agent_list']
        if row.get('DEPARTMENT') == 1:
            conversion_agents[agent] += file_call_attempts[filename].get(agent, 0)
            conversion_agents[f"{agent}_unique"] += file_call_attempts[filename].get(f"{agent}_unique", 0)
        elif row.get('DEPARTMENT') == 2:
            retention_agents[agent] += file_call_attempts[filename].get(agent, 0)
            retention_agents[f"{agent}_unique"] += file_call_attempts[filename].get(f"{agent}_unique", 0)

    return file_call_attempts


def export_call_attempts_to_excel(conversion_agents, retention_agents, file_call_attempts, df_agents, filename='Agent_Call_Results.xlsx'):
    """Export the call attempt results to an Excel file with accurate 'Sources' and 'Unique' columns in separate sheets."""
    
    # Define targets for conversion and retention
    target_conversion_unique = 300
    target_retention_unique = 20
    
    # Prepare data for conversion agents
    conversion_data = []
    for agent, attempts in conversion_agents.items():
        if not agent.endswith('_unique'):
            desk = df_agents[df_agents['AGENTNAME'] == agent]['DESK'].values[0] if agent in df_agents['AGENTNAME'].values else 'Unknown'
            
            total_attempts = sum(file_call_attempts[fname].get(agent, 0) for fname in file_call_attempts)
            total_unique = sum(file_call_attempts[fname].get(f"{agent}_unique", 0) for fname in file_call_attempts)
            target_percentage = (total_unique / target_conversion_unique) * 100
            
            unique_sources = []
            for fname in file_call_attempts:
                unique_count = file_call_attempts[fname].get(f"{agent}_unique", 0)
                if unique_count > 0:
                    unique_sources.append(f"{fname}:{unique_count}")
            
            sources_info = ", ".join(unique_sources) if unique_sources else 'No sources'
            conversion_data.append({
                'Group': 'Conversion',
                'Agent Name': agent.title(),
                'Desk': desk,
                'Call Attempts': total_attempts,
                'Unique': total_unique,
                'Target': target_conversion_unique,
                'Target Percentage': f"{target_percentage:.2f}%",
                'Sources': sources_info
            })

    # Prepare data for retention agents
    retention_data = []
    for agent, attempts in retention_agents.items():
        if not agent.endswith('_unique'):
            desk = df_agents[df_agents['AGENTNAME'] == agent]['DESK'].values[0] if agent in df_agents['AGENTNAME'].values else 'Unknown'
            
            total_attempts = sum(file_call_attempts[fname].get(agent, 0) for fname in file_call_attempts)
            total_unique = sum(file_call_attempts[fname].get(f"{agent}_unique", 0) for fname in file_call_attempts)
            target_percentage = (total_unique / target_retention_unique) * 100
            
            unique_sources = []
            for fname in file_call_attempts:
                unique_count = file_call_attempts[fname].get(f"{agent}_unique", 0)
                if unique_count > 0:
                    unique_sources.append(f"{fname}:{unique_count}")
            
            sources_info = ", ".join(unique_sources) if unique_sources else 'No sources'
            retention_data.append({
                'Group': 'Retention',
                'Agent Name': agent.title(),
                'Desk': desk,
                'Call Attempts': total_attempts,
                'Unique': total_unique,
                'Target': target_retention_unique,
                'Target Percentage': f"{target_percentage:.2f}%",
                'Sources': sources_info
            })
    
    # Create a DataFrame from the collected data
    conversion_df = pd.DataFrame(conversion_data)
    retention_df = pd.DataFrame(retention_data)

    # Export to Excel with multiple sheets
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        conversion_df.to_excel(writer, sheet_name='Conversion Agents', index=False)
        retention_df.to_excel(writer, sheet_name='Retention Agents', index=False)

    print("Results have been exported to Agent_Call_Results.xlsx")

# Load agent data
df_agents = pd.read_excel(r'C:\Users\marcus.forsen\Desktop\new project\agents.xlsx')
df_agents['AGENTNAME'] = df_agents['AGENTNAME'].str.strip().str.lower()
df_agents['DESK'] = df_agents['DESK'].str.strip()

# Load the call logs from CSV files with filenames
df_files = [
    (pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\voiso summitlife.csv'), 'voiso summitlife.csv'),
    (pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\voiso traling.csv'), 'voiso traling.csv'),
    (pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\voiso 24x.csv'), 'voiso 24x.csv'),
    (pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\coperato traling.csv'), 'coperato traling.csv'),
    (pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\coperato signix.csv'), 'coperato signix.csv'),
    (pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\coperato 24x.csv'), 'coperato 24x.csv'),
    (pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\voicespin.csv'), 'voicespin.csv')
]

# Initialize dictionaries to store call attempts by agent and department
call_attempts = defaultdict(int)
conversion_agents = defaultdict(int)
retention_agents = defaultdict(int)

# Initialize dictionary to store unmatched agents by file
unmatched_agents_by_file = {}

# Initialize dictionary to store call attempts by file
file_call_attempts = defaultdict(lambda: defaultdict(int))

# Process each file and keep track of call attempts per file
for df, filename in df_files:
    file_call_attempts = process_file(df, filename, call_attempts, file_call_attempts, conversion_agents, retention_agents, df_agents)

# Export results to Excel
export_call_attempts_to_excel(conversion_agents, retention_agents, file_call_attempts, df_agents)
