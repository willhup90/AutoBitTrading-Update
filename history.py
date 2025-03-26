import os
import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
import datetime

# ===== PATH DINAMIS =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FOLDER = os.path.join(BASE_DIR, "log-activity")

def run_log_viewer():
    root = tk.Tk()
    root.title("Log Viewer - AutoBitTrading")
    root.geometry("700x550")
    root.configure(bg="white")

    tk.Label(root, text="Pilih Tanggal Log:", bg="white", font=("Segoe UI", 11)).pack(pady=(10, 5))

    date_picker = DateEntry(root, width=12, background='darkblue',
                            foreground='white', borderwidth=2, date_pattern='dd-mm-yyyy')
    date_picker.pack()

    # Search & Copy
    search_frame = tk.Frame(root, bg="white")
    search_frame.pack(pady=(10, 0))

    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var, width=30, font=("Segoe UI", 10))
    search_entry.pack(side="left", padx=(0, 5))

    def search_log():
        log_text.tag_remove("highlight", "1.0", tk.END)
        keyword = search_var.get().strip()
        if keyword:
            start = "1.0"
            while True:
                start = log_text.search(keyword, start, stopindex=tk.END)
                if not start:
                    break
                end = f"{start}+{len(keyword)}c"
                log_text.tag_add("highlight", start, end)
                start = end
            log_text.tag_config("highlight", background="yellow", foreground="black")

    def copy_log():
        content = log_text.get("1.0", tk.END)
        root.clipboard_clear()
        root.clipboard_append(content)
        messagebox.showinfo("📋 Disalin", "Log telah disalin ke clipboard.")

    tk.Button(search_frame, text="🔍 Cari", command=search_log, bg="#2e6cd1", fg="white",
              font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 5))
    tk.Button(search_frame, text="📋 Copy Log", command=copy_log, bg="#63bb4d", fg="white",
              font=("Segoe UI", 9, "bold")).pack(side="left")

    def load_log():
        selected_date = date_picker.get_date()
        filename = selected_date.strftime("%d%m%Y") + ".log"
        filepath = os.path.join(LOG_FOLDER, filename)

        log_text.delete("1.0", tk.END)

        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    tag = ""
                    if "✅" in line:
                        tag = "success"
                    elif "❌" in line:
                        tag = "error"
                    elif "🚀" in line:
                        tag = "start"
                    elif "ℹ️" in line:
                        tag = "info"
                    elif "⏳" in line:
                        tag = "wait"

                    if tag:
                        log_text.insert(tk.END, line, tag)
                    else:
                        log_text.insert(tk.END, line)
        else:
            log_text.insert(tk.END, f"⚠️ Log tidak ditemukan untuk tanggal: {selected_date.strftime('%d-%m-%Y')}")

    tk.Button(root, text="📂 Tampilkan Log", command=load_log, bg="#2e6cd1", fg="white",
            font=("Segoe UI", 10, "bold")).pack(pady=10)

    log_text = tk.Text(root, wrap="word", height=20, font=("Courier New", 10))
    log_text.pack(padx=10, pady=10, fill="both", expand=True)

    log_text.tag_config("success", foreground="green")
    log_text.tag_config("error", foreground="red")
    log_text.tag_config("start", foreground="orange")
    log_text.tag_config("info", foreground="blue")
    log_text.tag_config("wait", foreground="gray")

    scrollbar = tk.Scrollbar(log_text, command=log_text.yview)
    scrollbar.pack(side="right", fill="y")
    log_text.config(yscrollcommand=scrollbar.set)

    today = datetime.date.today()
    date_picker.set_date(today)
    load_log()

    root.mainloop()

if __name__ == "__main__":
    run_log_viewer()
