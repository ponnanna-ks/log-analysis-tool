import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
from log_analysis_core import analyze_log_file

class LogAnalysisUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Log Analysis Tool")
        self.root.geometry("600x400")
        
        # Configure style
        style = ttk.Style()
        style.configure('TButton', padding=5)
        style.configure('TLabel', padding=5)
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Log Analysis Tool", font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=20)
        
        # File selection
        self.file_path = tk.StringVar()
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        file_label = ttk.Label(file_frame, text="Log File:")
        file_label.pack(side=tk.LEFT, padx=5)
        
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path, width=50)
        file_entry.pack(side=tk.LEFT, padx=5)
        
        # Add browse options
        browse_frame = ttk.Frame(file_frame)
        browse_frame.pack(side=tk.LEFT, padx=5)
        
        self.browse_type = tk.StringVar(value="project")
        project_radio = ttk.Radiobutton(browse_frame, text="Project", variable=self.browse_type, value="project")
        project_radio.pack(side=tk.LEFT)
        
        system_radio = ttk.Radiobutton(browse_frame, text="System", variable=self.browse_type, value="system")
        system_radio.pack(side=tk.LEFT)
        
        browse_button = ttk.Button(browse_frame, text="Browse", command=self.browse_file)
        browse_button.pack(side=tk.LEFT, padx=5)
        
        # Analysis button
        analyze_button = ttk.Button(main_frame, text="Analyze Log", command=self.analyze_log)
        analyze_button.grid(row=2, column=0, columnspan=2, pady=20)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Analysis Results", padding="10")
        results_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        self.processing_time_label = ttk.Label(results_frame, text="Total Processing Time: --")
        self.processing_time_label.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.status_time_label = ttk.Label(results_frame, text="Total Status Time: --")
        self.status_time_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Open folder button
        self.open_folder_button = ttk.Button(main_frame, text="Open Output Folder", 
                                           command=self.open_output_folder, state='disabled')
        self.open_folder_button.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        self.current_output_folder = None

    def browse_file(self):
        if self.browse_type.get() == "project":
            # Get the project directory (where the script is located)
            project_dir = os.path.dirname(os.path.abspath(__file__))
            filename = filedialog.askopenfilename(
                title="Select Log File from Project",
                initialdir=project_dir,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
        else:
            filename = filedialog.askopenfilename(
                title="Select Log File",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
        if filename:
            self.file_path.set(filename)

    def analyze_log(self):
        file_path = self.file_path.get()
        if not file_path:
            messagebox.showerror("Error", "Please select a log file first")
            return
        
        try:
            # Update status
            self.status_label.config(text="Analyzing log file...")
            self.root.update()
            
            # Use core functionality to analyze the log file
            result = analyze_log_file(file_path)
            
            if not result['success']:
                raise Exception(result['error'])
            
            # Update results
            self.processing_time_label.config(text=f"Total Processing Time: {result['total_processing_time']:.2f} seconds")
            self.status_time_label.config(text=f"Total Status Time: {result['total_status_time']:.2f} seconds")
            
            # Store output folder path and enable open folder button
            self.current_output_folder = result['output_folder']
            self.open_folder_button.config(state='normal')
            
            # Update status
            self.status_label.config(text="Analysis complete!")
            
            # Try to open Excel file
            self.open_excel_file(result['excel_path'])
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_label.config(text="Analysis failed!")

    def open_excel_file(self, excel_path):
        try:
            if os.name == 'nt':  # Windows
                os.startfile(excel_path)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open', excel_path] if os.name == 'darwin' else ['xdg-open', excel_path])
        except Exception:
            # Just update the status label with the file path
            self.status_label.config(text=f"Analysis complete! Excel file location: {excel_path}")

    def open_output_folder(self):
        if self.current_output_folder and os.path.exists(self.current_output_folder):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(self.current_output_folder)
                elif os.name == 'posix':  # macOS and Linux
                    subprocess.run(['open', self.current_output_folder] if os.name == 'darwin' else ['xdg-open', self.current_output_folder])
            except Exception as e:
                messagebox.showwarning("Warning", f"Could not open folder: {str(e)}")

def main():
    root = tk.Tk()
    app = LogAnalysisUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 