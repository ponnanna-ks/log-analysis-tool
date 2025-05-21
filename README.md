# Log Analysis Tool

A tool for analyzing log files and generating detailed reports in Excel format.

## Features

- Analyze log files for processing and status events
- Calculate total processing and status calculation times
- Generate detailed Excel reports with event timelines
- User-friendly GUI interface
- Cross-platform support (Windows, macOS, Linux)

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python log_analysis_ui.py
```

2. In the GUI:
   - Click "Browse" to select a log file
   - Click "Analyze Log" to process the file
   - View the results in the UI
   - Use "Open Output Folder" to access the generated Excel report

## Output

The tool generates:
- An Excel file with detailed analysis in the output folder
- Processing and status calculation time summaries
- Separate sheets for processing events and status events

## Requirements

- Python 3.8 or higher
- Dependencies listed in requirements.txt 