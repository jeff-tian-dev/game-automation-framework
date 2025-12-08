import sys
import os
import pyautogui
import time
import random
import json
import traceback
import tkinter as tk
from tkinter import ttk, messagebox
from multiprocessing import Process, freeze_support

from image_cropper import (
    find_icon_img,
    find_all_icon_img, home_resources,
    detect_brightest
)
from click_injector import (
    click_inject,
    human_move_inject,
    scroll_inject,
    mouse_downup_inject,
    move_injector,
    screenshot
)

bot_process = None

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

CORNER_ORDER = ["left", "top", "right", "bottom"]
data = {}

def load_data():
    global data

    with open(resource_path("templates/data.json"), "r") as f:
        temp_data = json.load(f)

    width, height = pyautogui.size()
    if width == 1920 and height == 1080:
        print("1920x1080 detected.")
        data = temp_data[1]
    else:
        print("2560x1600 or other detected.")
        data = temp_data[0]

def corner_helper(current, direction):
    idx = CORNER_ORDER.index(current)
    if direction == 1:
        return CORNER_ORDER[(idx + 1) % len(CORNER_ORDER)]
    elif direction == 2:
        return CORNER_ORDER[(idx - 1) % len(CORNER_ORDER)]
    return None

def expand_loc(x, y):
    return x + random.randint(-15, 15), y + random.randint(-15, 15)

def click(x, y, pause=1.0, rand=True):
    if rand:
        click_inject(x + random.randint(-20, 20), y + random.randint(-20, 20))
    else:
        click_inject(x, y)
    time.sleep(random.uniform(pause - (pause*0.2), pause + (pause*0.2)))

def worth():
    frame = screenshot()
    while find_icon_img(frame, data["path_find"], region=data["find_icon"]) == (None, None):
        time.sleep(1)
        frame = screenshot()

def point_on_line(x1, y1, x2, y2, t=0.5):
    x = x1 + (x2 - x1) * t
    y = y1 + (y2 - y1) * t
    return round(x), round(y)

def troop_spam(duration, method):
    time.sleep(random.randint(1, 2))
    corner = ["right", "left"]
    starting_corner = random.choice(corner)

    frame = screenshot()

    bx, by = find_icon_img(frame, "templates/" + method + ".png")
    click(bx, by, 0.1)
    time.sleep(0.2)
    try:
        mouse_downup_inject(1, *expand_loc(*data[starting_corner]))
        time.sleep(0.7)
        troop_spam_helper(starting_corner, random.randint(1, 2), 0, duration)
    finally:
        mouse_downup_inject(0, *expand_loc(*data[starting_corner]))

    heroes(frame)
    spells(frame)

    for i in range(random.randint(25, 30)):
        frame = screenshot()
        if find_icon_img(frame, data["path_star"], data["star_icon"]) != (None, None):
            break
        time.sleep(1)

def troop_spam_helper(corner, direction, iteration, duration):
    if iteration == 4:
        return
    current_pos = data[corner]
    next_corner = corner_helper(corner, direction)
    target = data[next_corner]

    human_move_inject(*expand_loc(*current_pos), *target, duration)
    return troop_spam_helper(next_corner, direction, iteration + 1, duration)

def find_hero_point():
    corner = ["top", "right", "left"]
    c_name = random.choice(corner)
    c1 = data[c_name]
    if c_name == "left" or c_name == "right":
        c2 = data["top"]
    else:
        c2 = data[random.choice(["left", "right"])]
    hero_point = point_on_line(*c1, *c2, random.uniform(0, 1))
    return hero_point

def heroes(frame):
    lst = ["queen", "warden", "RC", "king", "prince"]
    rep = []
    random.shuffle(lst)
    lst.append("loglauncher")
    for i in range(6):
        bx, by = find_icon_img(frame, "templates/" + lst[i] + ".png")
        if not bx and not by:
            continue
        if lst[i] != "loglauncher":
            rep.append((bx, by))
        hx, hy = find_hero_point()

        click(bx, by, 0.2, rand=False)
        click(hx, hy, 0.2)
    for i in range(len(rep)):
        click(*rep[i], 0.2)
        time.sleep(random.uniform(0.1, 0.2))
    return

def spells(frame):
    bx, by = find_icon_img(frame,"templates/earthquake.png")
    click(bx, by, 0.2)
    corners = ["left", "top", "right"]
    random.shuffle(corners)
    for i in range(3):
        x, y = data[corners[i]]
        if corners[i] == "left":
            x += round(data["earthquake"] * 1.3)
        elif corners[i] == "top":
            y += data["earthquake"]
        else:
            x -= round(data["earthquake"] * 1.3)
        for j in range(4):
            click(x, y, 0.1)

def walls_helper(g, e):
    click(1206, 80, 0.2)
    walls = None
    for i in range(9):
        frame = screenshot()
        points = find_all_icon_img(frame, resource_path("templates/wall.png"), (800, 200, 400, 800), text=True, threshold=0.7)
        points.reverse()
        if points:
            flag = False
            for j in range(len(points)):
                tx, ty, _ = points[j]
                if g > e:
                    ix, iy = find_icon_img(frame, resource_path("templates/gold.png"), (tx + 200, ty - 30, 500, 60), threshold=0.7)
                else:
                    ix, iy = find_icon_img(frame, resource_path("templates/elixir.png"), (tx + 200, ty - 30, 500, 60), threshold=0.7)
                bri = detect_brightest(frame, ix + 15, iy - 20, ix + 100, iy + 10)
                if bri > 600:
                    flag = True
                    walls = (tx, ty)
                    break
            if flag:
                break
        x, y = 1290, random.randint(700, 900)
        cy = y
        mouse_downup_inject(1, x, y)
        for j in range(50):
            move_injector(1290, round(cy))
            cy += (300 - y) / 50.0
            time.sleep(0.01)
        time.sleep(0.1)
        mouse_downup_inject(0, 1290, 300)
        time.sleep(0.5)
    if walls:
        click(*tuple(map(int, walls)), 1)
        frame = screenshot()
        points = find_all_icon_img(frame, resource_path("templates/upgrade.png"), (1000, 1000, 1000, 500), text=False, threshold=0.7)
        points.sort()
        if g > e:
            click(*points[0][:2], 0.2)
        else:
            click(*points[1][:2], 0.2)
        click(1838, 1406, 2)
        return True
    else:
        return False

def upgrade_walls(g, e):
    while walls_helper(g, e):
        frame = screenshot()
        g, e, _ = home_resources(frame)

def attack(_method, run_time, walls):
    time.sleep(1)
    click(*data["empty"], 0.2)
    scroll_inject(1000, 1000, 20)
    time.sleep(random.uniform(0.1, 0.3))
    start_time = time.time()

    while time.time() - start_time < run_time:
        click(*data["attack"])
        click(*data["find_match"])
        click(*data["attack2"])
        worth()

        if _method == 1:
            troop_spam(550, "sneaky")
        elif _method == 2:
            troop_spam(450, "superbarb")
        elif _method == 3:
            troop_spam(300, "valkyrie")

        click(*data["end"])
        click(*data["end_confirm"])
        for i in range(random.randint(1, 4)):
            click(*data["return"], 0.1)

        time.sleep(random.uniform(4, 5))
        while True:
            click(1400, 2000, 0.5)
            counter = 1
            frame = screenshot()
            g, e, _ = home_resources(frame)
            if g or e or _:
                break
            if counter > 5:
                raise FileNotFoundError
            time.sleep(2)
            counter += 1

        if walls:
            frame = screenshot()
            g, e, _ = home_resources(frame)
            if g > 15000000 or e > 15000000:
                upgrade_walls(g, e)

def run_bot(method, run_time, walls):
    load_data()
    attack(method, run_time, walls)  # stop_event defaults to None

def main():
    try:
        # ====== GUI SETUP ======
        root = tk.Tk()
        root.title("Autoloot Control Panel")

        # Make window a bit compact
        root.resizable(False, False)

        # Shared state
        attack_choice = tk.IntVar(value=1)  # default: Sneaky Goblins
        minutes_var = tk.StringVar(value="30")  # default 30 minutes
        wall_upgrades = tk.BooleanVar(value=False)

        # --- Callbacks ---

        def start_attack_gui():
            global bot_process

            # If a bot is already running, don't start another
            if bot_process is not None and bot_process.is_alive():
                messagebox.showinfo("Autoloot", "Autoloot is already running.")
                return

            key = attack_choice.get()
            walls_enabled = wall_upgrades.get()

            # Validate time
            try:
                mins = int(minutes_var.get())
                if mins <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Time", "Please enter a positive integer number of minutes.")
                return

            # Cap at 60 like before
            mins = min(60, mins)
            run_time = mins * 60

            # Launch bot in a separate process
            bot_process = Process(target=run_bot, args=(key, run_time, walls_enabled))
            bot_process.start()
            messagebox.showinfo("Autoloot", "Autoloot started. You can minimize this window.")


        def stop_attack_gui():
            global bot_process

            if bot_process is not None and bot_process.is_alive():
                bot_process.terminate()  # HARD STOP (like Ctrl-C)
                bot_process.join()
                bot_process = None
                messagebox.showinfo("Autoloot", "Autoloot process stopped.")
            else:
                messagebox.showinfo("Autoloot", "No autoloot is currently running.")

        # --- Layout ---

        padding = {"padx": 10, "pady": 5}

        # Attack selection frame
        frame_attacks = ttk.LabelFrame(root, text="Attack Method")
        frame_attacks.grid(row=0, column=0, sticky="ew", **padding)

        ttk.Radiobutton(frame_attacks, text="Sneaky Goblins", variable=attack_choice, value=1).grid(row=0, column=0, sticky="w", **padding)
        ttk.Radiobutton(frame_attacks, text="Super Barbs",    variable=attack_choice, value=2).grid(row=1, column=0, sticky="w", **padding)
        ttk.Radiobutton(frame_attacks, text="Valkyries",      variable=attack_choice, value=3).grid(row=2, column=0, sticky="w", **padding)
        ttk.Checkbutton(root, text="Auto Upgrade Walls" , variable=wall_upgrades).grid(row=4, column=0, padx=10, pady=5, sticky="w")

        # Time frame
        frame_time = ttk.LabelFrame(root, text="Timer")
        frame_time.grid(row=1, column=0, sticky="ew", **padding)

        ttk.Label(frame_time, text="Run for (minutes):").grid(row=0, column=0, sticky="w", **padding)
        entry_time = ttk.Entry(frame_time, textvariable=minutes_var, width=10)
        entry_time.grid(row=0, column=1, sticky="w", **padding)

        # Start/Stop buttons
        frame_controls = ttk.Frame(root)
        frame_controls.grid(row=2, column=0, sticky="ew", **padding)

        btn_start = ttk.Button(frame_controls, text="Start", command=start_attack_gui)
        btn_start.grid(row=0, column=0, **padding)

        btn_stop = ttk.Button(frame_controls, text="Stop", command=stop_attack_gui)
        btn_stop.grid(row=0, column=1, **padding)

        ttk.Label(root, text="Make sure the game is full screen, then press Start.\nYou can minimize this window after starting.").grid(
            row=3, column=0, **padding
        )

        root.mainloop()

    except Exception:
        with open("error.log", "w") as f:
            traceback.print_exc(file=f)

if __name__ == "__main__":
    freeze_support()
    main()

# python -m PyInstaller -F -w auto_loot.py --add-data "templates;templates"