import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, END
import sys
import os
import threading
import traceback
import io

# --- Add Project Root to Python Path ---
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# --- Import Our Analysis Function ---
try:
    from examples.run_analysis_example import run_full_analysis
except ImportError as e:
    # Show error in a popup before main window if import fails
    root = tk.Tk()
    root.withdraw() # Hide the main window
    messagebox.showerror("Import Error", f"Failed to import analysis function: {e}\n"
                       f"Ensure ic50_pkg is installed (pip install -e .) "
                       f"and all dependencies are met.")
    sys.exit(1)
except Exception as e:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Startup Error", f"An unexpected error occurred on startup:\n{e}")
    sys.exit(1)

# --- Class to Redirect Stdout to Tkinter Widget ---
class TextRedirector:
    def __init__(self, widget):
        self.widget = widget

    def write(self, s):
        # Ensure updates happen on the main GUI thread
        self.widget.after(0, self.append_text, s)

    def append_text(self, s):
        self.widget.config(state='normal')
        self.widget.insert(END, s)
        self.widget.see(END) # Auto-scroll
        self.widget.config(state='disabled')

    def flush(self):
        pass # Required for file-like object

# --- GUI Application Class ---
class IC50App:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("PyIC50 Analyzer (Free Edition)")
        self.root.geometry("650x550") # Set initial size

        # --- Variables ---
        self.file_path = tk.StringVar()

        # --- Frames for Layout ---
        top_frame = tk.Frame(self.root, padx=10, pady=10)
        top_frame.pack(fill=tk.X)

        middle_frame = tk.Frame(self.root, padx=10, pady=5)
        middle_frame.pack(fill=tk.BOTH, expand=True)

        bottom_frame = tk.Frame(self.root, padx=10, pady=10)
        bottom_frame.pack(fill=tk.X)

        # --- Top Frame Widgets ---
        tk.Label(top_frame, text="Select Data File (.csv or .xlsx):", font=("Helvetica", 10)).pack(anchor=tk.W)
        
        file_entry_frame = tk.Frame(top_frame)
        tk.Entry(file_entry_frame, textvariable=self.file_path, width=70, state='readonly').pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(file_entry_frame, text="Browse...", command=self.browse_file).pack(side=tk.LEFT)
        file_entry_frame.pack(anchor=tk.W, pady=(5, 15))

        self.analyze_button = tk.Button(top_frame, text="Run Analysis", command=self.start_analysis_thread, width=20, height=2, state=tk.DISABLED, font=("Helvetica", 11, "bold"))
        self.analyze_button.pack()

        # --- Middle Frame Widgets (Output Log) ---
        tk.Label(middle_frame, text="Output Log:", font=("Helvetica", 10)).pack(anchor=tk.W)
        self.output_text = scrolledtext.ScrolledText(middle_frame, wrap=tk.WORD, state='disabled', height=15, font=("Courier New", 9))
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # --- Bottom Frame Widgets (Status Bar) ---
        self.status_label = tk.Label(bottom_frame, text="Ready - Please select a file.", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X)

        # --- Redirect stdout ---
        # Do this *after* the widget exists
        sys.stdout = TextRedirector(self.output_text)
        sys.stderr = TextRedirector(self.output_text)


    def browse_file(self):
        path = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=(("Data Files", "*.csv *.xlsx"), ("All Files", "*.*"))
        )
        if path:
            self.file_path.set(path)
            self.analyze_button.config(state=tk.NORMAL)
            self.status_label.config(text=f"Selected: {os.path.basename(path)}")
        else:
            self.analyze_button.config(state=tk.DISABLED)
            self.status_label.config(text="Ready - Please select a file.")

    def run_analysis_task(self):
        """The actual analysis task to run in a thread."""
        path = self.file_path.get()
        if not path: return

        self.root.after(0, self.analyze_button.config, {'state': tk.DISABLED})
        self.root.after(0, self.status_label.config, {'text': "Analyzing... Please wait."})
        
        # Clear output using the redirector's method
        self.output_text.config(state='normal')
        self.output_text.delete(1.0, END)
        self.output_text.config(state='disabled')

        try:
            print("="*40)
            print(f" Starting Analysis on: {os.path.basename(path)} ")
            print("="*40 + "\n")
            
            # Run the imported function
            run_full_analysis(path) 
            
            print("\n" + "="*40)
            print(" Analysis Finished. ")
            print("="*40)
            self.root.after(0, self.status_label.config, {'text': "Analysis Finished. Plots may be open."})

        except Exception as e:
            print("\n" + "="*40)
            print(" !! AN ERROR OCCURRED !! ")
            print("="*40)
            # Use io.StringIO to capture traceback before printing
            err_io = io.StringIO()
            traceback.print_exc(file=err_io)
            print(err_io.getvalue())
            print("="*40)
            self.root.after(0, messagebox.showerror, "Analysis Error", f"An error occurred:\n{e}")
            self.root.after(0, self.status_label.config, {'text': "Error during analysis - check log."})
        finally:
            self.root.after(0, self.analyze_button.config, {'state': tk.NORMAL}) # Re-enable button

    def start_analysis_thread(self):
        """Starts the analysis in a new thread to avoid freezing the GUI."""
        # Use daemon=True so thread exits if main window closes
        analysis_thread = threading.Thread(target=self.run_analysis_task, daemon=True)
        analysis_thread.start()

# --- Main ---
if __name__ == "__main__":
    main_root = tk.Tk()
    app = IC50App(main_root)
    main_root.mainloop()