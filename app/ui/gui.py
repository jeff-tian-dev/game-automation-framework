import tkinter as tk
from tkinter import ttk, messagebox
import threading
from app.core.bot import Bot
from app.utils.logger import setup_logger

logger = setup_logger("GUI")

class AutoLootApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Clash AutoLoot Bot")
        self.root.resizable(False, False)
        
        self.bot = Bot()
        self.bot_thread = None

        self._init_ui()

    def _init_ui(self):
        padding = {"padx": 10, "pady": 5}

        # Variables
        self.attack_choice = tk.IntVar(value=1)
        self.minutes_var = tk.StringVar(value="30")
        self.wall_upgrades = tk.BooleanVar(value=False)

        # Attack Method Frame
        frame_attacks = ttk.LabelFrame(self.root, text="Attack Method")
        frame_attacks.grid(row=0, column=0, sticky="ew", **padding)

        ttk.Radiobutton(frame_attacks, text="Sneaky Goblins", variable=self.attack_choice, value=1).grid(row=0, column=0, sticky="w", **padding)
        ttk.Radiobutton(frame_attacks, text="Super Barbs",    variable=self.attack_choice, value=2).grid(row=1, column=0, sticky="w", **padding)
        ttk.Radiobutton(frame_attacks, text="Valkyries",      variable=self.attack_choice, value=3).grid(row=2, column=0, sticky="w", **padding)
        
        ttk.Checkbutton(self.root, text="Auto Upgrade Walls", variable=self.wall_upgrades).grid(row=4, column=0, sticky="w", **padding)

        # Timer Frame
        frame_time = ttk.LabelFrame(self.root, text="Timer")
        frame_time.grid(row=1, column=0, sticky="ew", **padding)

        ttk.Label(frame_time, text="Run for (minutes):").grid(row=0, column=0, sticky="w", **padding)
        entry_time = ttk.Entry(frame_time, textvariable=self.minutes_var, width=10)
        entry_time.grid(row=0, column=1, sticky="w", **padding)

        # Controls
        frame_controls = ttk.Frame(self.root)
        frame_controls.grid(row=2, column=0, sticky="ew", **padding)

        self.btn_start = ttk.Button(frame_controls, text="Start", command=self.start_bot)
        self.btn_start.grid(row=0, column=0, **padding)

        self.btn_stop = ttk.Button(frame_controls, text="Stop", command=self.stop_bot, state="disabled")
        self.btn_stop.grid(row=0, column=1, **padding)

        # Status
        self.status_label = ttk.Label(self.root, text="Ready")
        self.status_label.grid(row=3, column=0, **padding)

    def start_bot(self):
        if self.bot_thread and self.bot_thread.is_alive():
            return

        try:
            mins = int(self.minutes_var.get())
            if mins <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Invalid time duration.")
            return

        method = self.attack_choice.get()
        walls = self.wall_upgrades.get()

        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.status_label.config(text="Running...")

        self.bot_thread = threading.Thread(
            target=self._run_bot_thread,
            args=(method, mins, walls),
            daemon=True
        )
        self.bot_thread.start()

    def _run_bot_thread(self, method, mins, walls):
        self.bot.start(method, mins, walls)
        # When finished
        self.root.after(0, self._on_bot_finished)

    def stop_bot(self):
        self.bot.stop()
        self.status_label.config(text="Stopping...")

    def _on_bot_finished(self):
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.status_label.config(text="Stopped")
        messagebox.showinfo("Bot", "Bot execution finished.")

def run_gui():
    root = tk.Tk()
    app = AutoLootApp(root)
    root.mainloop()
