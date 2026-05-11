from pathlib import Path
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd

from app.export_utils import save_summary_outputs
from app.parsers.intra_v2 import analyse_file as analyse_intra
from app.parsers.intra_supported_v2 import analyse_file as analyse_intra_supported
from app.parsers.intersent_v2 import analyse_file as analyse_intersent
from app.parsers.interpara_v2 import analyse_file as analyse_interpara


PARSERS = {
    "intra": analyse_intra,
    "intra_supported": analyse_intra_supported,
    "intersent": analyse_intersent,
    "interpara": analyse_interpara,
}

LEVEL_LABELS = {
    "Intra-sentential — Supported": "intra_supported",
    "Inter-sentential": "intersent",
    "Inter-paragraph": "interpara",
}

SINGLE_FILE_MODE = "Single .txt file"
FOLDER_MODE = "Folder of .txt files"


class ConjuncToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ConjuncTool V2")
        self.root.geometry("900x560")

        self.input_mode = tk.StringVar(value=SINGLE_FILE_MODE)
        self.input_file = tk.StringVar()
        self.analysis_level = tk.StringVar(value="Intra-sentential — Supported")
        self.output_file = tk.StringVar()

        self.build_ui()

    def build_ui(self):
        title = tk.Label(
            self.root,
            text="ConjuncTool V2",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=15)

        subtitle = tk.Label(
            self.root,
            text="Halliday-based conjunction parser: intra-sentential, inter-sentential, and inter-paragraph",
            font=("Arial", 11)
        )
        subtitle.pack(pady=5)


        frame = tk.Frame(self.root)
        frame.pack(fill="x", padx=30, pady=15)

        tk.Label(frame, text="Input mode:").grid(row=0, column=0, sticky="w")
        mode_box = ttk.Combobox(
            frame,
            textvariable=self.input_mode,
            values=[SINGLE_FILE_MODE, FOLDER_MODE],
            state="readonly",
            width=42
        )
        mode_box.grid(row=1, column=0, sticky="w", pady=5)
        mode_box.bind("<<ComboboxSelected>>", self.update_input_mode)

        self.input_label = tk.Label(frame, text="Input .txt file:")
        self.input_label.grid(row=2, column=0, sticky="w", pady=(15, 0))
        tk.Entry(frame, textvariable=self.input_file, width=65).grid(row=3, column=0, padx=(0, 10), pady=5)
        self.browse_button = tk.Button(frame, text="Browse", command=self.choose_input)
        self.browse_button.grid(row=3, column=1)

        tk.Label(frame, text="Analysis level:").grid(row=4, column=0, sticky="w", pady=(15, 0))

        level_box = ttk.Combobox(
            frame,
            textvariable=self.analysis_level,
            values=list(LEVEL_LABELS.keys()),
            state="readonly",
            width=42
        )
        level_box.grid(row=5, column=0, sticky="w", pady=5)
        level_box.bind("<<ComboboxSelected>>", self.update_default_output_file)
        self.output_label = tk.Label(frame, text="Output CSV file:")
        self.output_label.grid(row=6, column=0, sticky="w", pady=(15, 0))
        tk.Entry(frame, textvariable=self.output_file, width=65).grid(row=7, column=0, padx=(0, 10), pady=5)
        self.output_button = tk.Button(frame, text="Save as", command=self.choose_output)
        self.output_button.grid(row=7, column=1)

        run_button = tk.Button(
            self.root,
            text="Run analysis",
            command=self.run_analysis,
            font=("Arial", 13, "bold"),
            width=18
        )
        run_button.pack(pady=15)

        open_button = tk.Button(
            self.root,
            text="Open output file",
            command=self.open_output_file,
            font=("Arial", 12),
            width=18
        )
        open_button.pack(pady=5)

        open_folder_button = tk.Button(
            self.root,
            text="Open output folder",
            command=self.open_output_folder,
            font=("Arial", 12),
            width=18
        )
        open_folder_button.pack(pady=5)

        self.status = tk.Text(self.root, height=10, width=95)
        self.status.pack(padx=30, pady=10)
        self.status.insert("end", "Ready.\n")

    def update_input_mode(self, event=None):
        self.input_file.set("")
        self.output_file.set("")
        if self.is_folder_mode():
            self.input_label.config(text="Input folder:")
            self.output_label.config(text="Output folder:")
        else:
            self.input_label.config(text="Input .txt file:")
            self.output_label.config(text="Output CSV file:")

    def is_folder_mode(self):
        return self.input_mode.get() == FOLDER_MODE

    def choose_input(self):
        if self.is_folder_mode():
            self.choose_input_folder()
        else:
            self.choose_input_file()

    def choose_input_file(self):
        file_path = filedialog.askopenfilename(
            title="Select a text file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if file_path:
            if Path(file_path).suffix.lower() != ".txt":
                messagebox.showwarning(
                    "Plain text file recommended",
                    "Please select a plain .txt file. CSV files should be converted to text files before analysis."
                )
            self.input_file.set(file_path)
            self.update_default_output_file()

    def choose_input_folder(self):
        folder_path = filedialog.askdirectory(
            title="Select a folder of text files"
        )

        if folder_path:
            self.input_file.set(folder_path)
            self.update_default_output_file()

    def update_default_output_file(self, event=None):
        input_path = self.input_file.get().strip()
        if not input_path:
            return

        selected_label = self.analysis_level.get()
        level_key = LEVEL_LABELS.get(selected_label, selected_label)

        output_dir = Path.home() / "ConjuncTool_outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        input_file = Path(input_path)
        if self.is_folder_mode():
            default_output = output_dir / f"{input_file.name}_{level_key}_batch_outputs"
        else:
            default_output = output_dir / f"{input_file.stem}_{level_key}_results.csv"
        self.output_file.set(str(default_output))

    def choose_output(self):
        if self.is_folder_mode():
            self.choose_output_folder()
        else:
            self.choose_output_file()

    def choose_output_file(self):
        file_path = filedialog.asksaveasfilename(
            title="Save output CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if file_path:
            self.output_file.set(file_path)

    def choose_output_folder(self):
        folder_path = filedialog.askdirectory(
            title="Select output folder"
        )

        if folder_path:
            self.output_file.set(folder_path)

    def open_output_file(self):
        output_path = self.output_file.get().strip()
        if not output_path:
            messagebox.showerror("Missing output", "No output file selected yet.")
            return
        path = Path(output_path)
        if not path.exists():
            messagebox.showerror("File not found", f"Output file not found:\n{path}")
            return
        subprocess.run(["open", str(path)])

    def open_output_folder(self):
        output_path = self.output_file.get().strip()
        if output_path and self.is_folder_mode():
            folder = Path(output_path)
        elif output_path:
            folder = Path(output_path).parent
        else:
            folder = Path.home() / "ConjuncTool_outputs"
        if not folder.exists():
            messagebox.showerror("Folder not found", f"Output folder not found:\n{folder}")
            return
        subprocess.run(["open", str(folder)])

    def run_analysis(self):
        if self.is_folder_mode():
            self.run_batch_analysis()
        else:
            self.run_single_analysis()

    def run_single_analysis(self):
        input_path = self.input_file.get().strip()
        level_label = self.analysis_level.get().strip()
        level = LEVEL_LABELS.get(level_label, "intra_supported")
        output_path = self.output_file.get().strip()

        if not input_path:
            messagebox.showerror("Missing input", "Please select an input .txt file.")
            return

        input_file = Path(input_path)

        if not output_path:
            output_dir = Path.home() / "ConjuncTool_outputs"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{input_file.stem}_{level}_results.csv"
            self.output_file.set(str(output_path))
        else:
            output_path_obj = Path(output_path)
            if output_path_obj.exists() and output_path_obj.is_dir():
                output_path_obj = output_path_obj / f"{input_file.stem}_{level}_results.csv"
                output_path = str(output_path_obj)
                self.output_file.set(output_path)
            elif output_path_obj.suffix.lower() != ".csv":
                output_path_obj.mkdir(parents=True, exist_ok=True)
                output_path_obj = output_path_obj / f"{input_file.stem}_{level}_results.csv"
                output_path = str(output_path_obj)
                self.output_file.set(output_path)

        try:
            parser = PARSERS[level]
            df = parser(input_path, output_path)
            summary_files = save_summary_outputs(df, output_path)

            self.status.delete("1.0", "end")
            self.status.insert("end", "ConjuncTool analysis complete\n")
            self.status.insert("end", "=" * 40 + "\n")
            self.status.insert("end", f"Input: {input_path}\n")
            self.status.insert("end", f"Level: {level_label}\n")
            self.status.insert("end", f"Detected cases: {len(df)}\n")
            self.status.insert("end", f"Output: {output_path}\n")
            self.status.insert("end", "\nSummary files:\n")
            for label, path in summary_files.items():
                if path:
                    self.status.insert("end", f"- {label}: {path}\n")

            if df.empty:
                self.status.insert("end", "\nNo cases detected.\n")
            else:
                self.status.insert("end", "\nTop detected items:\n")
                counts = df["detected_item"].str.lower().value_counts().head(8)
                for item, count in counts.items():
                    self.status.insert("end", f"- {item}: {count}\n")

            messagebox.showinfo("Done", f"Analysis complete.\nDetected cases: {len(df)}")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def run_batch_analysis(self):
        input_path = self.input_file.get().strip()
        level_label = self.analysis_level.get().strip()
        level = LEVEL_LABELS.get(level_label, "intra_supported")
        output_path = self.output_file.get().strip()

        if not input_path:
            messagebox.showerror("Missing input", "Please select a folder of .txt files.")
            return

        input_folder = Path(input_path)
        if not input_folder.exists() or not input_folder.is_dir():
            messagebox.showerror("Invalid input", f"Input folder not found:\n{input_folder}")
            return

        txt_files = sorted(
            path for path in input_folder.iterdir()
            if path.is_file() and path.suffix.lower() == ".txt"
        )
        if not txt_files:
            messagebox.showerror("No text files", "No .txt files were found in the selected folder.")
            return

        if output_path:
            output_dir = Path(output_path)
        else:
            output_dir = Path.home() / "ConjuncTool_outputs" / f"{input_folder.name}_{level}_batch_outputs"
            self.output_file.set(str(output_dir))
        output_dir.mkdir(parents=True, exist_ok=True)

        batch_stem = f"batch_{level}"
        results_path = output_dir / f"{batch_stem}_results.csv"
        summary_base_path = output_dir / f"{batch_stem}.csv"

        try:
            parser = PARSERS[level]
            frames = [parser(txt_file) for txt_file in txt_files]
            frames = [df for df in frames if df is not None and not df.empty]
            if frames:
                df = pd.concat(frames, ignore_index=True)
            else:
                df = pd.DataFrame()

            df.to_csv(results_path, index=False)
            summary_files = save_summary_outputs(df, summary_base_path, group_by_text=True)

            self.status.delete("1.0", "end")
            self.status.insert("end", "ConjuncTool batch analysis complete\n")
            self.status.insert("end", "=" * 40 + "\n")
            self.status.insert("end", f"Input folder: {input_folder}\n")
            self.status.insert("end", f"Level: {level_label}\n")
            self.status.insert("end", f"Text files processed: {len(txt_files)}\n")
            self.status.insert("end", f"Detected cases: {len(df)}\n")
            self.status.insert("end", f"Output folder: {output_dir}\n")
            self.status.insert("end", f"Results: {results_path}\n")
            self.status.insert("end", "\nSummary files:\n")
            for label, path in summary_files.items():
                if path:
                    self.status.insert("end", f"- {label}: {path}\n")

            if df.empty:
                self.status.insert("end", "\nNo cases detected.\n")
            else:
                self.status.insert("end", "\nTop detected items:\n")
                counts = df["detected_item"].str.lower().value_counts().head(8)
                for item, count in counts.items():
                    self.status.insert("end", f"- {item}: {count}\n")

            messagebox.showinfo(
                "Done",
                f"Batch analysis complete.\nText files processed: {len(txt_files)}\nDetected cases: {len(df)}"
            )

        except Exception as e:
            messagebox.showerror("Error", str(e))


def main():
    root = tk.Tk()
    app = ConjuncToolGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
