import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from zipfile import ZipFile

# Third-party module for native drag and drop capabilities (Mirrored from style guide)
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    pass


class FileSplitterApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Customer File Splitter & Zipper")
        self.root.geometry("500x360")  # Mirrored from reference layout
        self.root.resizable(False, False)

        # Color Theme Definitions (Strictly mirrored from style guide)
        self.bg_base = "#1F232A"
        self.bg_surface = "#2D3139"
        self.text_primary = "#E2E8F0"
        self.text_secondary = "#8E8E93"
        self.ios_blue = "#0A84FF"
        self.ios_green = "#30D158"
        self.ios_red = "#FF453A"

        self.root.configure(bg=self.bg_base)

        # Apply Windows dark window border styling (Mirrored from reference layout)
        try:
            from ctypes import byref, c_int, sizeof, windll

            HWND = windll.user32.GetParent(self.root.winfo_id())
            windll.dwmapi.DwmSetWindowAttribute(
                HWND, 20, byref(c_int(1)), sizeof(c_int)
            )
        except Exception:
            pass

        self.input_file_path = ""
        self.file_content = ""
        self.font_family = (
            "-apple-system",
            "SF Pro Text",
            "Helvetica Neue",
            "Segoe UI",
            "Arial",
        )

        # Style Engine Configuration
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure("TFrame", background=self.bg_base)
        self.style.configure("Surface.TFrame", background=self.bg_surface)
        self.style.configure(
            "TLabel", background=self.bg_base, foreground=self.text_primary
        )
        self.style.configure(
            "Surface.TLabel",
            background=self.bg_surface,
            foreground=self.text_primary,
        )

        self.style.configure(
            "IOS.TButton",
            background=self.bg_surface,
            foreground=self.ios_blue,
            font=(self.font_family, 10, "bold"),
            borderwidth=1,
            bordercolor=self.ios_blue,
            padding=(10, 4),
        )
        self.style.map(
            "IOS.TButton",
            background=[("active", "#3A3F4B")],
            foreground=[("active", "#64B5FF")],
        )

        self.create_widgets()
        self.setup_drag_and_drop()

    def create_widgets(self):
        # Main Frame setup
        main_frame = ttk.Frame(self.root, padding="24")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header Title
        title_lbl = ttk.Label(
            main_frame,
            text="Customer File Splitter & Zipper",
            font=(self.font_family, 16, "bold"),
        )
        title_lbl.pack(pady=(0, 15), anchor="w")

        # ----------------------------------------------------
        # VISUAL DROP ZONE BOX WITH OUTLINE (Mirrored Layout)
        # ----------------------------------------------------
        self.drop_canvas = tk.Canvas(
            main_frame, bg=self.bg_surface, highlightthickness=0, height=130
        )
        self.drop_canvas.pack(fill=tk.X, pady=5)

        # Draw dotted target outline inside canvas box area
        self.drop_canvas.create_rectangle(
            4, 4, 448, 126, outline="#48484A", dash=(4, 4), width=2
        )

        # Primary prompt string inside canvas box area
        self.file_label = tk.Label(
            self.drop_canvas,
            text="Drag & Drop Text File Here",
            font=(self.font_family, 11, "bold"),
            bg=self.bg_surface,
            fg=self.text_primary,
            justify="center",
        )
        self.drop_canvas.create_window(
            226, 32, window=self.file_label, anchor="center"
        )

        # Subtle alternative fallback text inside canvas box area
        self.or_lbl = tk.Label(
            self.drop_canvas,
            text="— or —",
            font=(self.font_family, 9),
            bg=self.bg_surface,
            fg=self.text_secondary,
        )
        self.drop_canvas.create_window(
            226, 65, window=self.or_lbl, anchor="center"
        )

        # Browse fallback button layered inside the canvas container
        self.upload_btn = ttk.Button(
            self.drop_canvas,
            text="Browse Files",
            style="IOS.TButton",
            command=self.load_file,
        )
        self.drop_canvas.create_window(
            226, 98, window=self.upload_btn, anchor="center"
        )

        # Status field below the visual drop box
        self.status_lbl = ttk.Label(
            main_frame,
            text="Waiting for .txt file...",
            font=(self.font_family, 10),
            foreground=self.text_secondary,
            wraplength=440,
            justify="center",
        )
        self.status_lbl.pack(pady=12, anchor="center")

        # Main Process/Action Execution Button (Bottom Stacked Layout)
        self.save_btn = tk.Button(
            main_frame,
            text="Split and Save as ZIP",
            font=(self.font_family, 11, "bold"),
            bg="#2C2C2E",
            fg="#48484A",
            state=tk.DISABLED,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            bd=0,
            command=self.process_and_zip,
            cursor="arrow",
        )
        self.save_btn.pack(fill=tk.X, ipady=10, pady=(5, 0))

    def setup_drag_and_drop(self):
        try:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self.handle_dropped_file)

            self.drop_canvas.drop_target_register(DND_FILES)
            self.drop_canvas.dnd_bind("<<Drop>>", self.handle_dropped_file)
        except NameError:
            pass

    def handle_dropped_file(self, event):
        file_path = event.data
        if file_path.startswith("{") and file_path.endswith("}"):
            file_path = file_path[1:-1]
        if file_path:
            self.process_and_validate_file(file_path)

    def load_file(self):
        file_path = filedialog.askopenfilename(
            title="Open Input File", filetypes=[("Text Files", "*.txt")]
        )
        if file_path:
            self.process_and_validate_file(file_path)

    def validate_format(self, content):
        """Validates that lines resemble the sample structure loosely."""
        lines = [line.strip() for line in content.splitlines()]
        clean_lines = [line for line in lines if line]

        if not clean_lines:
            return False, "The selected file contains no data."

        name_pattern = re.compile(r"\b\d+_\d+\b")

        for index, line in enumerate(clean_lines, start=1):
            pipe_count = line.count("|")
            if pipe_count < 15:
                return (
                    False,
                    f"Line {index} doesn't match expected file structure.\nOnly found {pipe_count} pipe delimiters.",
                )

            if not name_pattern.search(line):
                return (
                    False,
                    f"Line {index} target naming key error.\nCould not locate 'XXXX_XXXXX' signature.",
                )

        return True, ""

    def process_and_validate_file(self, file_path):
        try:
            self.status_lbl.config(
                text="Reading and inspecting file data structural mapping...",
                foreground=self.ios_blue,
            )
            self.root.update_idletasks()

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            is_valid, error_message = self.validate_format(content)
            if not is_valid:
                self.status_lbl.config(
                    text=f"Validation error: {error_message}",
                    foreground=self.ios_red,
                )
                # Reset button state to disabled if validation fails
                self.save_btn.config(
                    state=tk.DISABLED, bg="#2C2C2E", fg="#48484A"
                )
                return

            self.input_file_path = file_path
            self.file_content = content
            loaded_filename = os.path.basename(file_path)

            self.file_label.config(text=f"Loaded: {loaded_filename}", fg=self.ios_green)
            self.status_lbl.config(
                text="Validation passed. Ready to split.",
                foreground=self.ios_green,
            )

            # Style change to unlock the processing action button
            self.save_btn.config(
                state=tk.NORMAL,
                bg=self.ios_blue,
                fg="white",
                activebackground="#0070E6",
                activeforeground="white",
                cursor="hand2",
            )
        except Exception as e:
            self.status_lbl.config(
                text=f"Parsing failure: {str(e)}", foreground=self.ios_red
            )

    def process_and_zip(self):
        if not self.file_content:
            return

        zip_output_path = filedialog.asksaveasfilename(
            title="Save ZIP File As",
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip")],
            initialfile="split_customers.zip",
        )
        if not zip_output_path:
            return

        try:
            self.status_lbl.config(
                text="Assembling segment data and writing compression archive...",
                foreground=self.ios_blue,
            )
            self.root.update_idletasks()

            customer_blocks = self.file_content.split(";")
            name_pattern = re.compile(r"\b\d+_\d+\b")
            file_name_counters = {}

            with ZipFile(zip_output_path, "w") as zipf:
                for block in customer_blocks:
                    lines = [line.strip() for line in block.splitlines()]
                    clean_lines = [line for line in lines if line]

                    if not clean_lines:
                        continue

                    block_content = "\n".join(clean_lines)
                    match = name_pattern.search(block_content)
                    base_name = (
                        match.group(0) if match else "unknown_customer"
                    )

                    if base_name in file_name_counters:
                        file_name_counters[base_name] += 1
                        final_filename = (
                            f"{base_name}_{file_name_counters[base_name]}.txt"
                        )
                    else:
                        file_name_counters[base_name] = 1
                        final_filename = f"{base_name}.txt"

                    zipf.writestr(final_filename, block_content)

            self.status_lbl.config(
                text=f"Archive saved successfully to: {os.path.basename(zip_output_path)}",
                foreground=self.ios_green,
            )
            messagebox.showinfo(
                "Success", f"Successfully created archive:\n{zip_output_path}"
            )

        except Exception as e:
            self.status_lbl.config(
                text=f"Export failed: {str(e)}", foreground=self.ios_red
            )


if __name__ == "__main__":
    try:
        window = TkinterDnD.Tk()
    except NameError:
        window = tk.Tk()

    app = FileSplitterApp(window)
    window.mainloop()