import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import pandas as pd
import pymysql
from fpdf import FPDF
import os
import traceback

# DB Config
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "annotation_db",
    "port": 3306,
    "charset": "utf8mb4",
    "autocommit": True
}


annotations = []

class AnnotationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multimodal Review Dataset Labeler")
        self.root.state('zoomed')  # Fullscreen on Windows
        self.root.configure(bg="#f8f9fa")

        # Layout frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # LEFT PANEL
        self.left_panel = ttk.Frame(self.main_frame, width=400)
        self.left_panel.pack(side="left", fill="y")
        self.left_panel.pack_propagate(False)

        # RIGHT PANEL
        self.right_panel = ttk.Frame(self.main_frame)
        self.right_panel.pack(side="right", fill="both", expand=True)

        # Scrollable canvas for left controls
        self.canvas = tk.Canvas(self.left_panel, bg="#e9ecef", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.left_panel, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.file_path = tk.StringVar()
        self.label_text = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self.scrollable_frame, text="📘 Multimodal Review Dataset Labeler", font=("Segoe UI", 14, "bold")).pack(pady=(20, 10))

        ttk.Label(self.scrollable_frame, text="📁 Choose File (Text/Image/Audio):", font=("Segoe UI", 10, "bold")).pack(pady=(20, 5))
        ttk.Entry(self.scrollable_frame, textvariable=self.file_path, width=50, font=("Segoe UI", 10)).pack(pady=5)
        ttk.Button(self.scrollable_frame, text="Browse", command=self.browse_file).pack(pady=5)

        ttk.Label(self.scrollable_frame, text="✏️ Label:", font=("Segoe UI", 10, "bold")).pack(pady=(20, 5))
        ttk.Entry(self.scrollable_frame, textvariable=self.label_text, width=30, font=("Segoe UI", 10)).pack(pady=5)

        ttk.Button(self.scrollable_frame, text="☑ Submit Annotation", command=self.submit_annotation).pack(pady=10)
        ttk.Button(self.scrollable_frame, text="👁 View All Annotations", command=self.view_annotations).pack(pady=5)
        ttk.Button(self.scrollable_frame, text="📤 Export to CSV", command=self.export_csv).pack(pady=5)
        ttk.Button(self.scrollable_frame, text="📄 Export to PDF", command=self.export_pdf).pack(pady=5)
        ttk.Button(self.scrollable_frame, text="🗄 Upload to MySQL", command=self.upload_to_mysql).pack(pady=15)

        self.output = tk.Text(self.right_panel, font=("Segoe UI", 10), bg="#ffffff", fg="#212529")
        self.output.pack(padx=10, pady=10, fill="both", expand=True)

    def browse_file(self):
        filetypes = [("All Files", "*.*")]
        filepath = filedialog.askopenfilename(filetypes=filetypes)
        if filepath:
            self.file_path.set(filepath)

    def submit_annotation(self):
        path = self.file_path.get()
        label = self.label_text.get()
        if not path or not label:
            messagebox.showwarning("Missing Info", "File and label are required.")
            return
        annotations.append({"file": path, "label": label})
        self.output.insert(tk.END, f"Labeled: {os.path.basename(path)} as {label}\n")
        self.file_path.set("")
        self.label_text.set("")

    def view_annotations(self):
        if not annotations:
            messagebox.showinfo("No data", "No annotations available.")
            return

        view_win = tk.Toplevel(self.root)
        view_win.title("All Annotations")
        view_win.geometry("600x400")

        tree = ttk.Treeview(view_win, columns=("File", "Label"), show="headings")
        tree.heading("File", text="File")
        tree.heading("Label", text="Label")

        for row in annotations:
            tree.insert("", "end", values=(os.path.basename(row["file"]), row["label"]))

        tree.pack(fill="both", expand=True)

    def export_csv(self):
        if not annotations:
            messagebox.showinfo("No data", "No annotations to export.")
            return
        df = pd.DataFrame(annotations)
        df.to_csv("annotations.csv", index=False)
        messagebox.showinfo("Exported", "Annotations exported to annotations.csv")

    def export_pdf(self):
        if not annotations:
            messagebox.showinfo("No data", "No annotations to export.")
            return
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for row in annotations:
            pdf.cell(200, 10, txt=f"{os.path.basename(row['file'])} - {row['label']}", ln=True)
        pdf.output("annotations.pdf")
        messagebox.showinfo("Exported", "Annotations exported to annotations.pdf")

    def upload_to_mysql(self):
        try:
            import pymysql
            if not annotations:
                messagebox.showwarning("No Data", "No annotations found to upload.")
                return

            print("👀 About to connect using PyMySQL...")
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS annotations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    file VARCHAR(255),
                    label VARCHAR(255),
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            for row in annotations:
                print("Inserting:", row)
                cursor.execute(
                    "INSERT INTO annotations (file, label) VALUES (%s, %s)",
                    (os.path.basename(row.get("file", "missing")), row.get("label", "missing"))
                )

            conn.commit()
            conn.close()
            self.output.insert(tk.END, "✅ Upload successful!\n")
            messagebox.showinfo("Success", "Annotations uploaded to MySQL successfully.")

        except Exception as err:
            traceback.print_exc()
            self.output.insert(tk.END, f"❌ Upload failed: {err}\n")
            messagebox.showerror("Error", f"MySQL Upload Failed:\n{err}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AnnotationApp(root)
    root.mainloop()
