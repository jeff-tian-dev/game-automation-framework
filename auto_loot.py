import sys
import os
import pyautogui
import time
import random
import json
from click_injector import click_inject, human_move_inject
from click_injector import find_icon_inject
from click_injector import scroll_inject
from click_injector import mouse_downup_inject

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

CORNER_ORDER = ["left", "top", "right", "bottom"]
data = {}

def corner_helper(current, direction):
    idx = CORNER_ORDER.index(current)
    if direction == 1:
        return CORNER_ORDER[(idx + 1) % len(CORNER_ORDER)]
    elif direction == 2:
        return CORNER_ORDER[(idx - 1) % len(CORNER_ORDER)]
    return None

def expand_loc(x, y):
    return x + random.randint(-15, 15), y + random.randint(-15, 15)

def click(x, y, pause=1.0):
    click_inject(x + random.randint(-20, 20), y + random.randint(-20, 20))
    time.sleep(random.uniform(pause - (pause*0.2), pause + (pause*0.2)))

def worth():
    while not find_icon_inject(data["path_find"], data["find_icon"],):
        time.sleep(1)

def point_on_line(x1, y1, x2, y2, t=0.5):
    x = x1 + (x2 - x1) * t
    y = y1 + (y2 - y1) * t
    return round(x), round(y)

def troop_spam(duration):
    time.sleep(random.randint(1, 2))
    corner = ["right", "left"]
    starting_corner = random.choice(corner)

    click(*data['1'], 0.1)
    time.sleep(0.2)
    try:
        mouse_downup_inject(1, *expand_loc(*data[starting_corner]))
        time.sleep(0.7)
        troop_spam_helper(starting_corner, random.randint(1, 2), 0, duration)
    finally:
        mouse_downup_inject(0, *expand_loc(*data[starting_corner]))

    heroes()
    spells()

    for i in range(random.randint(25, 30)):
        if find_icon_inject(data["path_star"], data["star_icon"]):
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

def heroes():
    lst = ["q", "w", "e", "r"]
    random.shuffle(lst)
    lst.append("z")
    for i in range(5):
        click(*data[str(lst[i])], 0.2)
        time.sleep(random.uniform(0.1, 0.2))
        x, y = find_hero_point()
        click(x, y, random.uniform(0.1, 0.2))
    for i in range(4):
        click(*data[str(lst[i])], 0.2)
        time.sleep(random.uniform(0.1, 0.2))
    return

def spells():
    click(*data['a'], 0.2)
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

def attack(_method, run_time):
    time.sleep(1)
    click(*data["empty"], 0.2)
    scroll_inject(1000, 1000, 10)
    time.sleep(random.uniform(0.1, 0.3))
    start_time = time.time()
    while time.time() - start_time < run_time:
        click(*data["attack"])
        click(*data["find_match"])
        click(*data["attack2"])
        worth()
        if _method == 1:
            troop_spam(550)
        if _method == 2:
            troop_spam(450)
        if _method == 3:
            troop_spam(375)
        click(*data["end"])
        click(*data["end_confirm"])
        for i in range(random.randint(1, 4)):
            click(*data["return"], 0.1)
        time.sleep(random.uniform(4, 5))
        click(1400, 2000, 1)

if __name__ == "__main__":
    try:
        print("Warning: Make sure the game is full screen before starting.\n")

        with open(resource_path("templates/data.json"), "r") as f:
            temp_data = json.load(f)
        width, height = pyautogui.size()
        if width == 1920 and height == 1080:
            print("1920x1080 detected.")
            data = temp_data[1]
        else:
            print("2560x1600 detected.")
            data = temp_data[0]
        print("[1] Sneaky Goblins")
        print("[2] Super Barbs")
        print("[3] Valkyries")
        print("What attack would you like to use? ")
        key = int(input("Enter a number: "))
#
        if key == 1:
            print("Sneaky Goblins chosen!")
        if key == 2:
            print("Super Barbs chosen!")
        if key == 3:
            print("Super Valkyries chosen!")
        max_time = min(60, int(input("Select how long you want to run Autoloot, in minutes! (max duration 60 minutes): "))) * 60
        print("Autoloot starting in 5 seconds, minimize this window!")
        time.sleep(2)
        attack(key, max_time)
#
        print("Finished Autoloot.")
        input("\nPress Enter to exit...")
        time.sleep(3)


    except Exception:
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")

# python -m PyInstaller --onefile auto_loot.py --add-data "templates;templates"