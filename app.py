import pandas as pd
import re
from collections import defaultdict

def extract_name(agent_str):
    """Extract the name from the agent string in 'voicespin.csv'."""
    if pd.isna(agent_str) or not isinstance(agent_str, str):
        return ''
    
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

def convert_to_seconds(duration_str, is_voicespin=False):
    """
    Converts a duration string to total seconds. Handles formats of HH:MM:SS, MM:SS, and cases with unexpected extra parts.
    For voicespin data, formats like MM:SS should be handled correctly, and extra trailing zeros should be removed.
    """
    if pd.isna(duration_str) or not isinstance(duration_str, str):
        print(f"Warning: Invalid duration value detected: {duration_str}")
        return 0  # Default to 0 if duration_str is NaN or not a string

    duration_str = duration_str.strip()
    
    if not duration_str:
        print(f"Warning: Empty duration value detected: '{duration_str}'")
        return 0  # Return 0 if the duration string is empty

    try:
        if is_voicespin:
            # Handle MM:SS and HH:MM:SS formats with trailing zeros
            parts = duration_str.split(':')
            if len(parts) > 2:
                # If there are more than two parts, it's likely HH:MM:SS with trailing zeros
                if len(parts) == 3 and parts[-1] == '00':
                    # Remove the trailing '00' for HH:MM:SS
                    parts.pop()
                # Rejoin the remaining parts
                duration_str = ':'.join(parts)
            parts = duration_str.split(':')
            if len(parts) == 2:  # MM:SS
                minutes, seconds = map(int, parts)
                total_seconds = minutes * 60 + seconds
            elif len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, parts)
                total_seconds = (hours * 3600) + (minutes * 60) + seconds
            else:
                print(f"Warning: Unexpected duration format for voicespin: '{duration_str}'")
                return 0
        else:
            # Handle HH:MM:SS or MM:SS format
            parts = duration_str.split(':')
            if len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, parts)
                total_seconds = (hours * 3600) + (minutes * 60) + seconds
            elif len(parts) == 2:  # MM:SS
                minutes, seconds = map(int, parts)
                total_seconds = (minutes * 60) + seconds
            else:
                print(f"Warning: Unexpected duration format: '{duration_str}'")
                return 0
        
        return total_seconds
    except ValueError as e:
        print(f"Error converting duration '{duration_str}': {e}")
        return 0  # Default to 0 in case of an error

def convert_to_hours_minutes_seconds(seconds):
    """Convert seconds to hours, minutes, and seconds, returning them as a formatted string."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    if hours > 0:
        return f"{hours} h {minutes} m {remaining_seconds} s"
    elif minutes > 0:
        return f"{minutes} m {remaining_seconds} s"
    else:
        return f"{remaining_seconds} s"

def preprocess_data(df, duration_column):
    """Replace NaN values with '0:00' in the duration column."""
    df[duration_column] = df[duration_column].fillna('0:00')
    return df

def process_duration_file(df, filename, duration_column, is_voicespin=False):
    """Process a file to calculate total duration in seconds."""
    print(f"Processing file: {filename}")
    print(f"Duration column: {duration_column}")
    
    # Replace NaN values with '0:00'
    df = preprocess_data(df, duration_column)
    
    # Convert column to string to handle any mixed data types
    df[duration_column] = df[duration_column].astype(str)
    
    # Print some example values from the duration column
    print("Example duration values:")
    print(df[duration_column].head())
    
    df.loc[:, 'Duration_seconds'] = df[duration_column].apply(lambda x: convert_to_seconds(x, is_voicespin))
    total_seconds = df['Duration_seconds'].sum()
    
    print(f"Total seconds for {filename}: {total_seconds}")
    return total_seconds

def extract_agent_names(df, filename):
    """Extract and normalize agent names from different columns."""
    if filename in ['voiso summitlife.csv', 'voiso traling.csv']:
        df.loc[:, 'Agent_list'] = df['Agent(s)'].apply(lambda x: [name.strip().lower() for name in str(x).split('; ')] if pd.notna(x) else [])
    elif filename in ['coperato traling.csv', 'coperato Signix.csv']:
        df.loc[:, 'Agent_list'] = df['Name'].apply(lambda x: x.strip().lower() if pd.notna(x) else '')
    elif filename == 'voicespin.csv':
        df.loc[:, 'Agent_list'] = df['AGENT'].apply(extract_name)
    
    return df

def process_files(df_files, df_agents):
    """Process all files and return results categorized by agent type."""
    file_durations = defaultdict(lambda: defaultdict(int))
    unmatched_agents = defaultdict(set)
    
    known_agents = set(df_agents['AGENTNAME'].str.strip().str.lower())
    
    for df, filename in df_files:
        if filename in ['voiso summitlife.csv', 'voiso traling.csv']:
            duration_column = 'Duration'
            is_voicespin = False
        elif filename in ['coperato traling.csv', 'coperato Signix.csv']:
            duration_column = 'Duration'
            is_voicespin = False
        elif filename == 'voicespin.csv':
            duration_column = 'BILLSEC'
            is_voicespin = True
        else:
            continue
        
        df = extract_agent_names(df, filename)
        total_seconds = process_duration_file(df, filename, duration_column, is_voicespin)
        
        for _, row in df.iterrows():
            agents = row['Agent_list']
            if isinstance(agents, list):
                for a in agents:
                    file_durations[a][filename] += row['Duration_seconds']
                    if a not in known_agents:
                        unmatched_agents[filename].add(a)
            else:
                file_durations[agents][filename] += row['Duration_seconds']
                if agents not in known_agents:
                    unmatched_agents[filename].add(agents)
    
    conversion_agents = {}
    retention_agents = {}
    
    for _, row in df_agents.iterrows():
        agent = row['AGENTNAME'].strip().lower()
        desk = row['DESK'].strip()
        if row['DEPARTMENT'] == 1:
            conversion_agents[agent] = {
                'desk': desk,
                'total_seconds': 0,
                'sources': defaultdict(int)
            }
        elif row['DEPARTMENT'] == 2:
            retention_agents[agent] = {
                'desk': desk,
                'total_seconds': 0,
                'sources': defaultdict(int)
            }
    
    for agent, files in file_durations.items():
        total_seconds = sum(files.values())
        if agent in conversion_agents:
            conversion_agents[agent]['total_seconds'] += total_seconds
            for filename, seconds in files.items():
                conversion_agents[agent]['sources'][filename] += seconds
        elif agent in retention_agents:
            retention_agents[agent]['total_seconds'] += total_seconds
            for filename, seconds in files.items():
                retention_agents[agent]['sources'][filename] += seconds
    
    return conversion_agents, retention_agents, file_durations, unmatched_agents

def calculate_target_percentage(seconds):
    """Calculate the percentage of the target achieved."""
    target_seconds = 2 * 3600  # 2 hours in seconds
    return (seconds / target_seconds) * 100

def get_max_lengths(agents):
    """Get maximum lengths of columns based on the data."""
    max_lengths = {
        'Agent Name': len('Agent Name'),
        'Desk': len('Desk'),
        'Total Time': len('Total Time'),
        'Target': len('Target'),
        'Target Percentage': len('Target Percentage'),
        'Sources': len('Sources')
    }
    
    for agent, info in agents.items():
        total_time_length = len(convert_to_hours_minutes_seconds(info['total_seconds']))
        max_lengths['Agent Name'] = max(max_lengths['Agent Name'], len(agent.title()))
        max_lengths['Desk'] = max(max_lengths['Desk'], len(info['desk']))
        max_lengths['Total Time'] = max(max_lengths['Total Time'], total_time_length)
        max_lengths['Target'] = max(max_lengths['Target'], len(convert_to_hours_minutes_seconds(7200)))
        max_lengths['Target Percentage'] = max(max_lengths['Target Percentage'], len(f"{calculate_target_percentage(info['total_seconds']):.2f}%"))
        
        if info['sources']:
            max_lengths['Sources'] = max(max_lengths['Sources'], max(len(f"{filename}: {convert_to_hours_minutes_seconds(seconds)}") for filename, seconds in info['sources'].items()))
        else:
            max_lengths['Sources'] = max(max_lengths['Sources'], len('No sources'))
    
    return max_lengths

def format_row(agent, info, max_lengths):
    """Format a single row for printing."""
    total_seconds = info['total_seconds']
    total_time = convert_to_hours_minutes_seconds(total_seconds)
    target_time = convert_to_hours_minutes_seconds(7200)  # 2 hours in seconds
    target_percentage = calculate_target_percentage(total_seconds)
    file_sources = ', '.join(f"{filename}: {convert_to_hours_minutes_seconds(seconds)}"
                             for filename, seconds in info['sources'].items())
    return (f"{agent.title():<{max_lengths['Agent Name']}} | "
            f"{info['desk']:<{max_lengths['Desk']}} | "
            f"{total_time:<{max_lengths['Total Time']}} | "
            f"{target_time:<{max_lengths['Target']}} | "
            f"{target_percentage:>{max_lengths['Target Percentage']}.2f}% | "
            f"{file_sources:<{max_lengths['Sources']}}")

def print_results(conversion_agents, retention_agents, file_durations, unmatched_agents):
    """Print results for Conversion and Retention agents with alignment and unmatched agents."""
    max_conversion_lengths = get_max_lengths(conversion_agents)
    max_retention_lengths = get_max_lengths(retention_agents)

    # Print results for Conversion agents
    print("\nConversion Agents:")
    print("=" * (sum(max_conversion_lengths.values()) + 50))
    print(f"{'Agent Name':<{max_conversion_lengths['Agent Name']}} | "
          f"{'Desk':<{max_conversion_lengths['Desk']}} | "
          f"{'Total Time':<{max_conversion_lengths['Total Time']}} | "
          f"{'Target':<{max_conversion_lengths['Target']}} | "
          f"{'Target Percentage':<{max_conversion_lengths['Target Percentage']}} | "
          f"{'Sources':<{max_conversion_lengths['Sources']}}")
    print("-" * (sum(max_conversion_lengths.values()) + 50))
    
    sorted_conversion_agents = sorted(conversion_agents.items(), key=lambda x: x[1]['total_seconds'], reverse=True)
    for agent, info in sorted_conversion_agents:
        print(format_row(agent, info, max_conversion_lengths))
    
    # Print results for Retention agents
    print("\nRetention Agents:")
    print("=" * (sum(max_retention_lengths.values()) + 50))
    print(f"{'Agent Name':<{max_retention_lengths['Agent Name']}} | "
          f"{'Desk':<{max_retention_lengths['Desk']}} | "
          f"{'Total Time':<{max_retention_lengths['Total Time']}} | "
          f"{'Target':<{max_retention_lengths['Target']}} | "
          f"{'Target Percentage':<{max_retention_lengths['Target Percentage']}} | "
          f"{'Sources':<{max_retention_lengths['Sources']}}")
    print("-" * (sum(max_retention_lengths.values()) + 50))
    
    sorted_retention_agents = sorted(retention_agents.items(), key=lambda x: x[1]['total_seconds'], reverse=True)
    for agent, info in sorted_retention_agents:
        print(format_row(agent, info, max_retention_lengths))
    
    # Print Unmatched Agents
    print("\nUnmatched Agents:")
    print("=" * 90)
    for filename, agents in unmatched_agents.items():
        print(f"File: {filename}")
        print("-" * 90)
        for agent in sorted(agents):
            print(f"{agent.title():<20}")
        print("-" * 90)

# Example usage, assuming you have the necessary data loaded
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

# Process the files and get conversion and retention agents
conversion_agents, retention_agents, file_durations, unmatched_agents = process_files(df_files, df_agents)

# Print the results
print_results(conversion_agents, retention_agents, file_durations, unmatched_agents)
