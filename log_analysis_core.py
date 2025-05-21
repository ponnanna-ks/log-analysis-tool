import re
from datetime import datetime
import pandas as pd
import os
from pathlib import Path
import shutil

# Define arrays of keywords for different types of events
PROCESSING_KEYWORDS = [
    'socket onopen', 'parseLogs', 'saveAllLogs', 'welding_system',
    'saveSLogs', 'saveTLogs', 'calculateTiltViewLogs', 'saveTiltViewLogs', 
    'calculateAvgTLogs', 'saveAvgTLogs', 'insertJobNumberToTLogs', 
    'insertJobNumberToAvgTLogs', 'JOB NUMBER to AvgTlogs', 'JOB NUMBER to TLogs'
]
STATUS_KEYWORDS = ['startCalculating', 'checkTLogsExistenceByProjectId', 'setIncompleteFlagTRecords', 'updateSLogsStatusFromTLogsStatus','Rowcount', 'Rows affected', 'updating the status']

def create_output_folder(log_file_path):
    """Create an output folder for the analysis results."""
    # Get the log file name without extension
    log_name = Path(log_file_path).stem
    # Create folder name with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    folder_name = f"{log_name}"
    
    # Create the folder
    os.makedirs(folder_name, exist_ok=True)
    
    # Copy the log file to the new folder
    log_filename = os.path.basename(log_file_path)
    shutil.copy2(log_file_path, os.path.join(folder_name, log_filename))
    
    return folder_name

def parse_time(time_str):
    """Parse time string to datetime object."""
    return datetime.strptime(time_str, '%I:%M:%S %p')

def extract_time_from_log(log_line):
    """Extract time from log line."""
    time_match = re.search(r'(\d{1,2}:\d{2}:\d{2} [AP]M)', log_line)
    if time_match:
        return time_match.group(1)
    return None

def parse_logs(file_path):
    """Parse log file and extract processing and status events."""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Initialize data structures
    processing_events = []
    status_events = []
    current_processing = []
    current_status = []
    total_processing_time = 0
    total_status_time = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Extract time and log content
        time = extract_time_from_log(line)
        if not time:
            continue

        # Processing events
        if any(keyword in line for keyword in PROCESSING_KEYWORDS):
            # Start new processing group on socket onopen
            if 'socket onopen' in line:
                if current_processing:
                    processing_events.append(current_processing)
                    # Calculate total processing time for this group
                    start_time = parse_time(current_processing[0]['time'])
                    end_time = parse_time(current_processing[-1]['time'])
                    total_processing_time += (end_time - start_time).total_seconds()
                current_processing = [{'time': time, 'log': line}]
            # Add to current processing group
            elif current_processing:
                current_processing.append({'time': time, 'log': line})
                # End group on welding_system
                if 'welding_system' in line:
                    processing_events.append(current_processing)
                    # Calculate total processing time for this group
                    start_time = parse_time(current_processing[0]['time'])
                    end_time = parse_time(current_processing[-1]['time'])
                    total_processing_time += (end_time - start_time).total_seconds()
                    current_processing = []
            # Start new log service group on START
            elif 'START' in line:
                current_processing = [{'time': time, 'log': line}]
            # Add to current log service group
            elif current_processing and 'END' in line:
                current_processing.append({'time': time, 'log': line})
                processing_events.append(current_processing)
                # Calculate total processing time for this group
                start_time = parse_time(current_processing[0]['time'])
                end_time = parse_time(current_processing[-1]['time'])
                total_processing_time += (end_time - start_time).total_seconds()
                current_processing = []

        # Status calculation events
        if any(keyword in line for keyword in STATUS_KEYWORDS):
            if 'startCalculating' in line:
                if current_status:
                    status_events.append(current_status)
                    # Calculate total status time for this group
                    start_time = parse_time(current_status[0]['time'])
                    end_time = parse_time(current_status[-1]['time'])
                    total_status_time += (end_time - start_time).total_seconds()
                current_status = [{'time': time, 'log': line}]
            elif current_status:
                current_status.append({'time': time, 'log': line})
                if 'updating the status' in line:
                    status_events.append(current_status)
                    # Calculate total status time for this group
                    start_time = parse_time(current_status[0]['time'])
                    end_time = parse_time(current_status[-1]['time'])
                    total_status_time += (end_time - start_time).total_seconds()
                    current_status = []

    # Add any remaining events
    if current_processing:
        processing_events.append(current_processing)
        # Calculate total processing time for remaining group
        start_time = parse_time(current_processing[0]['time'])
        end_time = parse_time(current_processing[-1]['time'])
        total_processing_time += (end_time - start_time).total_seconds()
    if current_status:
        status_events.append(current_status)
        # Calculate total status time for remaining group
        start_time = parse_time(current_status[0]['time'])
        end_time = parse_time(current_status[-1]['time'])
        total_status_time += (end_time - start_time).total_seconds()

    return processing_events, status_events, total_processing_time, total_status_time

def format_output(processing_events, status_events, output_folder):
    """Format the analysis results into an Excel file."""
    # Create Excel writer with path in the output folder
    excel_path = os.path.join(output_folder, 'log_analysis.xlsx')
    writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
    
    # Process events for processing sheet
    processing_data = []
    for i, event_group in enumerate(processing_events, 1):
        start_time = parse_time(event_group[0]['time'])
        end_time = parse_time(event_group[-1]['time'])
        total_duration = end_time - start_time
        
        # Add each step with its duration
        for j, event in enumerate(event_group):
            current_time = parse_time(event['time'])
            if j > 0:
                prev_time = parse_time(event_group[j-1]['time'])
                step_duration = current_time - prev_time
            else:
                step_duration = None
            
            processing_data.append({
                'timestamp': current_time,
                'id': i if j == 0 else '',
                'log': event['log'].split('|')[-1].strip(),
                'time': event['time'],
                'step duration': str(step_duration) if step_duration else ''
            })
        
        # Add total duration
        processing_data.append({
            'timestamp': end_time,
            'id': '',
            'log': 'Total processing time',
            'time': str(total_duration),
            'step duration': ''
        })
        processing_data.append({
            'timestamp': end_time,
            'id': '',
            'log': '',
            'time': '',
            'step duration': ''
        })

    # Process status events
    status_data = []
    for i, event_group in enumerate(status_events, 1):
        start_time = parse_time(event_group[0]['time'])
        end_time = parse_time(event_group[-1]['time'])
        duration = end_time - start_time
        
        for j, event in enumerate(event_group):
            current_time = parse_time(event['time'])
            if j > 0:
                prev_time = parse_time(event_group[j-1]['time'])
                step_duration = current_time - prev_time
            else:
                step_duration = None
            
            status_data.append({
                'timestamp': current_time,
                'id': i if j == 0 else '',
                'log': event['log'].split('|')[-1].strip(),
                'time': event['time'],
                'step duration': str(step_duration) if step_duration else ''
            })
        
        # Add duration
        status_data.append({
            'timestamp': end_time,
            'id': '',
            'log': 'Total status calculation time',
            'time': str(duration),
            'step duration': ''
        })
        status_data.append({
            'timestamp': end_time,
            'id': '',
            'log': '',
            'time': '',
            'step duration': ''
        })

    # Create DataFrames
    processing_df = pd.DataFrame(processing_data)
    status_df = pd.DataFrame(status_data)

    # Write to Excel
    processing_df.to_excel(writer, sheet_name='Processing Events', index=False)
    status_df.to_excel(writer, sheet_name='Status Events', index=False)

    # Auto-adjust columns width
    for sheet_name in writer.sheets:
        worksheet = writer.sheets[sheet_name]
        df = processing_df if sheet_name == 'Processing Events' else status_df
        
        for idx, col in enumerate(df.columns):
            # Get the maximum length of the column
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            )
            # Set the column width
            worksheet.set_column(idx, idx, max_length + 2)

    writer.close()
    return excel_path

def analyze_log_file(file_path):
    """Main function to analyze a log file."""
    try:
        # Create output folder
        output_folder = create_output_folder(file_path)
        
        # Parse logs
        processing_events, status_events, total_processing_time, total_status_time = parse_logs(file_path)
        
        # Format output
        excel_path = format_output(processing_events, status_events, output_folder)
        
        return {
            'success': True,
            'output_folder': output_folder,
            'excel_path': excel_path,
            'total_processing_time': total_processing_time,
            'total_status_time': total_status_time
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        } 