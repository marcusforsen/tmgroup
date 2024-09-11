import pandas as pd
import re
from collections import defaultdict

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
    # Clean column names by stripping extra spaces
    df.columns = df.columns.str.strip()

    # Initialize file-specific call attempts
    if filename not in file_call_attempts:
        file_call_attempts[filename] = defaultdict(int)

    if filename in ['voiso summitlife.csv', 'voiso traling.csv']:
        df['Agent_list'] = df['Agent(s)'].apply(lambda x: [name.strip().lower() for name in str(x).split('; ')] if pd.notna(x) else [])
        df = df.explode('Agent_list')
        df = df[df['Agent_list'].apply(is_valid_agent)]  # Filter valid agents
        for agent in df['Agent_list']:
            file_call_attempts[filename][agent] += 1

    elif filename in ['coperato traling.csv', 'coperato Signix.csv']:
        df['Agent_list'] = df['Name'].apply(lambda x: x.strip().lower() if pd.notna(x) else '')
        df = df[df['Agent_list'].apply(is_valid_agent)]  # Filter valid agents
        for _, row in df.iterrows():
            agent = row['Agent_list']
            attempts = row['Call Attempts'] if 'Call Attempts' in df.columns else 0
            file_call_attempts[filename][agent] += attempts

    elif filename == 'voicespin.csv':
        # Try to identify the correct column for agent names
        if 'AGENT' in df.columns:
            df['Agent_list'] = df['AGENT'].apply(extract_name)
        elif 'Agent' in df.columns:  # Check for alternative column name
            df['Agent_list'] = df['Agent'].apply(extract_name)
        else:
            print(f"Error: No suitable column found for agent names in {filename}.")
            return
        
        # Count occurrences of each agent
        agent_counts = df['Agent_list'].value_counts()
        
        # Update file_call_attempts
        for agent, count in agent_counts.items():
            file_call_attempts[filename][agent] = count

    # Merge with agent information to separate Conversion and Retention agents
    df_merged = df.merge(df_agents, left_on='Agent_list', right_on='AGENTNAME', how='left')

    # Collect unmatched agents
    unmatched_agents = df_merged[df_merged['AGENTNAME'].isna()]['Agent_list']
    unmatched_agents = unmatched_agents[unmatched_agents.apply(is_valid_agent)].unique()
    if filename not in unmatched_agents_by_file:
        unmatched_agents_by_file[filename] = set()
    unmatched_agents_by_file[filename].update(unmatched_agents)

    # Update overall call attempts
    for agent, attempts in file_call_attempts[filename].items():
        call_attempts[agent] += attempts

    # Aggregate call attempts for Conversion and Retention departments
    for _, row in df_merged.iterrows():
        agent = row['Agent_list']
        if row.get('DEPARTMENT') == 1:  # Conversion
            conversion_agents[agent] += file_call_attempts[filename].get(agent, 0)
        elif row.get('DEPARTMENT') == 2:  # Retention
            retention_agents[agent] += file_call_attempts[filename].get(agent, 0)

    return file_call_attempts

def print_results(call_attempts, file_call_attempts, conversion_agents, retention_agents):
    """Print results for call attempts, conversion, and retention."""
    target = 250

    # Collect results for conversion agents
    conversion_results = []
    for agent in conversion_agents:
        attempts = sum(file_call_attempts.get(filename, {}).get(agent, 0) for filename in file_call_attempts)
        target_percentage = (attempts / target) * 100
        sources = ', '.join(f"{filename}: {file_call_attempts.get(filename, {}).get(agent, 0)}" for filename in file_call_attempts if file_call_attempts.get(filename, {}).get(agent, 0) > 0)
        desk = df_agents[df_agents['AGENTNAME'] == agent]['DESK'].values[0] if agent in df_agents['AGENTNAME'].values else 'Unknown'
        conversion_results.append(('Conversion', desk, agent, attempts, target, target_percentage, sources))

    # Collect results for retention agents
    retention_results = []
    for agent in retention_agents:
        attempts = sum(file_call_attempts.get(filename, {}).get(agent, 0) for filename in file_call_attempts)
        target_percentage = (attempts / target) * 100
        sources = ', '.join(f"{filename}: {file_call_attempts.get(filename, {}).get(agent, 0)}" for filename in file_call_attempts if file_call_attempts.get(filename, {}).get(agent, 0) > 0)
        desk = df_agents[df_agents['AGENTNAME'] == agent]['DESK'].values[0] if agent in df_agents['AGENTNAME'].values else 'Unknown'
        retention_results.append(('Retention', desk, agent, attempts, target, target_percentage, sources))

    # Sort results by target percentage in descending order
    conversion_results.sort(key=lambda x: x[5], reverse=True)
    retention_results.sort(key=lambda x: x[5], reverse=True)

    # Define headers
    headers = {
        'Type': 'Type',
        'Desk': 'Desk',
        'Agent Name': 'Agent Name',
        'Call Attempts': 'Call Attempts',
        'Target': 'Target',
        '% of Target': '% of Target',
        'Source Files': 'Source Files'
    }

    # Calculate maximum lengths for each column considering headers and data
    max_lengths = {key: max(len(headers[key]), max(len(str(result[i])) for result in conversion_results + retention_results))
                   for i, key in enumerate(headers)}

    # Print results for Conversion agents
    print("\nConversion Results Sorted by Target Percentage:")
    header = (f"{headers['Type']:<{max_lengths['Type']}} | "
              f"{headers['Desk']:<{max_lengths['Desk']}} | "
              f"{headers['Agent Name']:<{max_lengths['Agent Name']}} | "
              f"{headers['Call Attempts']:<{max_lengths['Call Attempts']}} | "
              f"{headers['Target']:<{max_lengths['Target']}} | "
              f"{headers['% of Target']:<{max_lengths['% of Target']}} | "
              f"{headers['Source Files']:<{max_lengths['Source Files']}}")
    print(header)
    print("-" * (sum(max_lengths.values()) + len(headers) * 3))  # Adjust for separators

    for result in conversion_results:
        type_, desk, agent, attempts, target, target_percentage, sources = result
        print(f"{type_:<{max_lengths['Type']}} | "
              f"{desk:<{max_lengths['Desk']}} | "
              f"{agent.title():<{max_lengths['Agent Name']}} | "
              f"{attempts:<{max_lengths['Call Attempts']}} | "
              f"{target:<{max_lengths['Target']}} | "
              f"{target_percentage:>{max_lengths['% of Target']}.2f}% | "
              f"{sources:<{max_lengths['Source Files']}}")

    # Print results for Retention agents
    print("\nRetention Results Sorted by Target Percentage:")
    header = (f"{headers['Type']:<{max_lengths['Type']}} | "
              f"{headers['Desk']:<{max_lengths['Desk']}} | "
              f"{headers['Agent Name']:<{max_lengths['Agent Name']}} | "
              f"{headers['Call Attempts']:<{max_lengths['Call Attempts']}} | "
              f"{headers['Target']:<{max_lengths['Target']}} | "
              f"{headers['% of Target']:<{max_lengths['% of Target']}} | "
              f"{headers['Source Files']:<{max_lengths['Source Files']}}")
    print(header)
    print("-" * (sum(max_lengths.values()) + len(headers) * 3))  # Adjust for separators

    for result in retention_results:
        type_, desk, agent, attempts, target, target_percentage, sources = result
        print(f"{type_:<{max_lengths['Type']}} | "
              f"{desk:<{max_lengths['Desk']}} | "
              f"{agent.title():<{max_lengths['Agent Name']}} | "
              f"{attempts:<{max_lengths['Call Attempts']}} | "
              f"{target:<{max_lengths['Target']}} | "
              f"{target_percentage:>{max_lengths['% of Target']}.2f}% | "
              f"{sources:<{max_lengths['Source Files']}}")

    # Print unmatched agents by file
    print("\nUnmatched Agents by File:")
    print("-" * 32)
    for filename, agents in unmatched_agents_by_file.items():
        if agents:
            print(f"\nFile: {filename}")
            for agent in sorted(agents):
                print(f"Unmatched Agent: {agent}")

# Example usage with loaded data
# Load the agent information from Excel and clean the AGENTNAME
df_agents = pd.read_excel(r'C:\Users\marcus.forsen\Desktop\new project\agent-listT.xlsx')
df_agents['AGENTNAME'] = df_agents['AGENTNAME'].str.strip().str.lower()
df_agents['DESK'] = df_agents['DESK'].str.strip()

# Load the call logs from CSV files with filenames
df_files = [
    (pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\voiso summitlife.csv'), 'voiso summitlife.csv'),
    (pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\voiso traling.csv'), 'voiso traling.csv'),
    (pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\coperato traling.csv'), 'coperato traling.csv'),
    (pd.read_csv(r'C:\Users\marcus.forsen\Desktop\new project\coperato Signix.csv'), 'coperato Signix.csv'),
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

# Print the results with call attempts, target, and source file info
print_results(call_attempts, file_call_attempts, conversion_agents, retention_agents)




