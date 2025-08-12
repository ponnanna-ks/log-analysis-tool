import re
from datetime import datetime
import pandas as pd
import os
from pathlib import Path
import shutil

# Define arrays of keywords for different types of events
PROCESSING_KEYWORDS = [
    'socket onopen','welding_system',
]
STATUS_KEYWORDS = ['CalculatingStatusModal  - startCalculating  - Start', 'Rowcount', 'Rows affected', 'InsertsLogStatus - updating the status']
ERROR_KEYWORDS = ['ERROR :']
EXCLUDE_ERROR_KEYWORDS = ['updateAvgStatus', 'wrongData']

def create_output_folder(log_file_path):
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
    return datetime.strptime(time_str, '%I:%M:%S %p')

def extract_time_from_log(log_line):
    time_match = re.search(r'(\d{1,2}:\d{2}:\d{2} [AP]M)', log_line)
    if time_match:
        return time_match.group(1)
    return None

def parse_logs(file_path):
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

        # Error events - Process separately from status events
        if 'ERROR :' in line:
            # Skip excluded error types
            if any(exclude in line for exclude in EXCLUDE_ERROR_KEYWORDS):
                continue
            
            # Create a new status group for this error if we're not in one
            if not current_status:
                current_status = [{'time': time, 'log': line}]
            else:
                # Add to current status group
                current_status.append({'time': time, 'log': line})
                
                # If this is a new error line, create a new status group
                if 'ERROR :' in line:
                    status_events.append(current_status)
                    current_status = [{'time': time, 'log': line}]

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
    # Create Excel writer with path in the output folder
    excel_path = os.path.join(output_folder, 'log_analysis.xlsx')
    writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
    
    # Process events for processing sheet
    processing_data = []
    total_logs_downloaded = 0
    total_processing_time_seconds = 0
    total_status_time_seconds = 0
    processed_errors = set()  # Track processed error messages to avoid duplicates
    
    # Function to format seconds to HH:MM:SS
    def format_duration(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    # Process download events
    for i, event_group in enumerate(processing_events, 1):
        # Initialize session total logs downloaded
        session_logs_downloaded = 0
        
        # Process each event in the group
        for event in event_group:
            current_time = parse_time(event['time'])
            
            # Determine process name
            if 'socket onopen' in event['log']:
                process_name = 'multiple download - acknowledge'
                # Extract logs downloaded count
                match = re.search(r'e.data:\s*(\d+)', event['log'])
                if match:
                    logs_downloaded = int(match.group(1))
                    session_logs_downloaded += logs_downloaded
                    total_logs_downloaded += logs_downloaded
            elif 'welding_system' in event['log']:
                process_name = 'multiple download - saveLogs Completed'
            else:
                process_name = 'Unknown Process'
            
            processing_data.append({
                'id': i,
                'event type': 'download',
                'process name': process_name,
                'log': event['log'].split('|')[-1].strip(),
                'time': event['time'],
                'logs downloaded': logs_downloaded if 'socket onopen' in event['log'] else ''
            })
        
        # Add session totals if we found any download events
        if session_logs_downloaded > 0:
            # Get first and last event times for this session
            first_event = event_group[0]
            last_event = event_group[-1]
            start_time = parse_time(first_event['time'])
            end_time = parse_time(last_event['time'])
            total_duration = (end_time - start_time).total_seconds()
            total_processing_time_seconds += total_duration
            
            # Add total processing time
            processing_data.append({
                'id': i,
                'event type': 'download',
                'process name': 'total processing time',
                'log': f'From {first_event["time"]} to {last_event["time"]}',
                'time': format_duration(total_duration),
                'logs downloaded': ''
            })
            
            # Add total logs downloaded for this session
            processing_data.append({
                'id': i,
                'event type': 'download',
                'process name': 'total log downloaded',
                'log': '',
                'time': '',
                'logs downloaded': session_logs_downloaded
            })
            
            # Add empty row after download session
            processing_data.append({})
    
    # Process status events
    status_id = len(processing_events) + 1
    for i, event_group in enumerate(status_events, 1):
        # Add status calculation events
        start_event = next((e for e in event_group if 'startCalculating' in e['log']), None)
        if start_event:
            processing_data.append({
                'id': status_id,
                'event type': 'status',
                'process name': 'Status calculation start',
                'log': start_event['log'].split('|')[-1].strip(),
                'time': start_event['time'],
                'logs downloaded': ''
            })
        
        # Add status update events
        update_event = next((e for e in event_group if 'updating the status' in e['log']), None)
        if update_event:
            processing_data.append({
                'id': status_id,
                'event type': 'status',
                'process name': 'status update',
                'log': update_event['log'].split('|')[-1].strip(),
                'time': update_event['time'],
                'logs downloaded': ''
            })
        
        # Add error events
        error_events = []
        for event in event_group:
            if 'ERROR :' in event['log'] and not any(exclude in event['log'] for exclude in EXCLUDE_ERROR_KEYWORDS):
                error_events.append(event)
        
        if error_events:
            # Add empty row before errors only if there were status events
            if start_event or update_event:
                processing_data.append({})
            
            # Process each error event
            for error_event in error_events:
                # Extract error components
                error_time = error_event['time']
                error_msg = error_event['log'].split('|')[-1].strip()
                
                # Create a unique identifier using time, service name, operation, and message
                # This helps distinguish between different errors even if they have the same message
                error_parts = error_msg.split(' - ')
                service_name = error_parts[1] if len(error_parts) > 1 else ''
                operation = error_parts[2] if len(error_parts) > 2 else ''
                
                error_id = f"{error_time}_{service_name}_{operation}_{error_msg}"
                
                # If we haven't processed this exact error before
                if error_id not in processed_errors:
                    processed_errors.add(error_id)
                    
                    # If the error message contains JSON, extract just the message part
                    if 'message' in error_msg:
                        try:
                            import json
                            error_dict = json.loads(error_msg)
                            error_msg = error_dict.get('message', error_msg)
                        except json.JSONDecodeError:
                            pass
                    
                    processing_data.append({
                        'id': status_id,
                        'event type': 'error',
                        'process name': 'error occurred',
                        'log': error_msg,
                        'time': error_time,
                        'logs downloaded': ''
                    })
            
            # Add empty row after errors only if there are more events
            if i < len(status_events):
                processing_data.append({})
        
        # Add total status processing time if we have both start and update events
        if start_event and update_event:
            start_time = parse_time(start_event['time'])
            end_time = parse_time(update_event['time'])
            total_duration = (end_time - start_time).total_seconds()
            total_status_time_seconds += total_duration
            
            processing_data.append({
                'id': status_id,
                'event type': 'status',
                'process name': 'total status calculation time',
                'log': f'From {start_event["time"]} to {update_event["time"]}',
                'time': format_duration(total_duration),
                'logs downloaded': ''
            })
            
            # Add empty row only if this isn't the last status session
            if i < len(status_events):
                processing_data.append({})
            status_id += 1
    
    # Add summary section
    if processing_events:
        # Calculate overall processing time from first download to last download
        first_download = processing_events[0][0]
        last_download = processing_events[-1][-1]
        start_time = parse_time(first_download['time'])
        end_time = parse_time(last_download['time'])
        overall_duration = (end_time - start_time).total_seconds()
        
        processing_data.append({})  # Empty row for spacing
        processing_data.append({
            'id': 'Summary',
            'event type': '',
            'process name': 'Total logs downloaded',
            'log': '',
            'time': '',
            'logs downloaded': total_logs_downloaded
        })
        processing_data.append({
            'id': 'Summary',
            'event type': '',
            'process name': 'Total processing time',
            'log': f'From {first_download["time"]} to {last_download["time"]}',
            'time': format_duration(overall_duration),
            'logs downloaded': ''
        })
        processing_data.append({
            'id': 'Summary',
            'event type': '',
            'process name': 'Total status calculation time',
            'log': '',
            'time': format_duration(total_status_time_seconds),
            'logs downloaded': ''
        })
        processing_data.append({
            'id': 'Summary',
            'event type': '',
            'process name': 'Total error count',
            'log': '',
            'time': '',
            'logs downloaded': len(processed_errors)
        })
    
    # Create DataFrame and write to Excel
    df = pd.DataFrame(processing_data)
    df.to_excel(writer, sheet_name='Analysis', index=False)
    
    # Auto-adjust column widths
    worksheet = writer.sheets['Analysis']
    for idx, col in enumerate(df.columns):
        max_length = max(
            df[col].astype(str).apply(len).max(),
            len(col)
        )
        worksheet.set_column(idx, idx, max_length + 2)
    
    writer.close()
    return excel_path

if __name__ == '__main__':
    file_path = 'EventLogs_Jun06-2025.txt'
    
    # Create output folder and copy log file
    output_folder = create_output_folder(file_path)
    print(f"Created output folder: {output_folder}")
    print(f"Copied log file to output folder")
    
    # Process logs and generate output
    processing_events, status_events, total_processing_time, total_status_time = parse_logs(file_path)
    excel_path = format_output(processing_events, status_events, output_folder)
    print(f"Analysis complete. Excel file saved at: {excel_path}")
    print(f"\nTotal Processing Time: {total_processing_time:.2f} seconds")
    print(f"Total Status Calculation Time: {total_status_time:.2f} seconds")