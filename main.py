import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import json
import threading
import time
import subprocess
import os

CONFIG_PATH = "D:/wildan/config-json/config.json"
SCRIPT_PATH = "D:/wildan/asyncio-autobit-stockbit.py"
VERSION = "v1.2.5"

def save_config(method, value, exec_time):
    data = {
        "method": method,
        "value": value,
        "execution_time": exec_time
    }
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)

def run_script():
    # Buka script utama di terminal baru
    subprocess.Popen(["start", "cmd", "/k", f"python {SCRIPT_PATH}"], shell=True)

def start_countdown(target_time, countdown_label, root):
    def update_countdown():
        while True:
            now = datetime.now()
            remaining = target_time - now
            if remaining.total_seconds() <= 0:
                countdown_label.config(text="⏰ Time's up!")
                print("⏳ Countdown selesai! Menjalankan script trading...")
                run_script()
                root.destroy()
                break

            days = remaining.days
            hours, remainder = divmod(remaining.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            countdown_text = f"{days:02d} Days | {hours:02d} Hours | {minutes:02d} Minutes | {seconds:02d} Seconds"
            countdown_label.config(text=countdown_text)
            time.sleep(1)

    threading.Thread(target=update_countdown, daemon=True).start()

def build_gui():
    root = tk.Tk()
    root.title("Konfigurasi Trading Auto Buy")
    root.geometry("500x500")

    # Splash screen versi
    splash = tk.Toplevel()
    splash.overrideredirect(True)
    splash.geometry("300x100+600+300")
    splash_label = tk.Label(splash, text=f"Auto Buy Trading\nVersi {VERSION}", font=("Helvetica", 16, "bold"), bg="white")
    splash_label.pack(expand=True, fill="both")
    root.withdraw()
    splash.after(2000, lambda: (splash.destroy(), root.deiconify()))

    header = tk.Label(root, text="KONFIGURASI AUTO BUY", font=("Helvetica", 16, "bold"))
    header.pack(pady=10)

    # Frame 1 - Metode
    frame1 = tk.LabelFrame(root, text="1. Pilih Metode Trading Buy Order Lot:", padx=10, pady=10)
    frame1.pack(fill="x", padx=10)

    method_var = tk.StringVar(value="Target-Amount")
    rb1 = tk.Radiobutton(frame1, text="A. Target Amount", variable=method_var, value="Target-Amount")
    rb2 = tk.Radiobutton(frame1, text="B. Jumlah LOT", variable=method_var, value="Jumlah-LOT")
    rb1.pack(anchor="w")
    rb2.pack(anchor="w")

    value_label = tk.Label(frame1, text="Masukan Jumlah Target (contoh: 10.000.000)")
    value_label.pack(anchor="w")
    value_entry = tk.Entry(frame1)
    value_entry.pack(fill="x")

    def update_label(*args):
        if method_var.get() == "Jumlah-LOT":
            value_label.config(text="Masukan Jumlah Lot (Contoh 2)")
        else:
            value_label.config(text="Masukan Jumlah Target (contoh: 10.000.000)")
    method_var.trace("w", update_label)

    # Frame 2 - Tanggal
    frame2 = tk.LabelFrame(root, text="2. Pilih Tanggal Eksekusi", padx=10, pady=10)
    frame2.pack(fill="x", padx=10)
    date_entry = DateEntry(frame2, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
    date_entry.pack()

    # Frame 3 - Jam Eksekusi
    frame3 = tk.LabelFrame(root, text="3. Pilih Jam Eksekusi", padx=10, pady=10)
    frame3.pack(fill="x", padx=10)

    hour_var = tk.StringVar(value="00")
    minute_var = tk.StringVar(value="00")
    second_var = tk.StringVar(value="00")

    hour_menu = ttk.Combobox(frame3, textvariable=hour_var, values=[f"{i:02d}" for i in range(24)], width=5)
    minute_menu = ttk.Combobox(frame3, textvariable=minute_var, values=[f"{i:02d}" for i in range(60)], width=5)
    second_menu = ttk.Combobox(frame3, textvariable=second_var, values=[f"{i:02d}" for i in range(60)], width=5)
    hour_menu.pack(side="left", padx=(5, 2))
    minute_menu.pack(side="left", padx=2)
    second_menu.pack(side="left", padx=2)

    # Frame 4 - Countdown
    frame4 = tk.LabelFrame(root, text="4. Countdown Eksekusi", padx=10, pady=10)
    frame4.pack(fill="x", padx=10)
    countdown_label = tk.Label(frame4, text="⏳ Belum dimulai", font=("Courier", 14), fg="red")
    countdown_label.pack()

    # Buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    def on_save():
        try:
            method = method_var.get()
            value = value_entry.get().strip()
            date = date_entry.get()
            hour = int(hour_var.get())
            minute = int(minute_var.get())
            second = int(second_var.get())

            execution_time = f"{date} {hour:02d}:{minute:02d}:{second:02d}"
            exec_datetime = datetime.strptime(execution_time, "%Y-%m-%d %H:%M:%S")
            if exec_datetime <= datetime.now():
                messagebox.showerror("Error", "Execution time must be di masa depan.")
                return

            save_config(method, value, execution_time)
            countdown_label.config(text="⏳ Countdown dimulai...")
            messagebox.showinfo("✅ Berhasil", "Konfigurasi berhasil disimpan.")
            root.after(1000, lambda: start_countdown(exec_datetime, countdown_label, root))
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan konfigurasi: {e}")

    save_btn = tk.Button(button_frame, text="🗂️ Simpan Config", command=on_save)
    reset_btn = tk.Button(button_frame, text="🔄 Reset", command=lambda: root.destroy())
    save_btn.grid(row=0, column=0, padx=10)
    reset_btn.grid(row=0, column=1, padx=10)

    root.mainloop()

if __name__ == "__main__":
    build_gui()
