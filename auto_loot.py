import os
import pyautogui
import time
import random
import json
import keyboard
from image_cropper import read_all_resources
from pathlib import Path

APPDATA = Path(os.getenv("APPDATA")) / "AutoLootBot"
DATA_FILE = APPDATA / "data.json"
APPDATA.mkdir(parents=True, exist_ok=True)

pyautogui.PAUSE = 0
data = {}

def grab_coords():
    keyboard.wait('w')
    return pyautogui.position()

def human_move_to(x1, y1, x2, y2, duration=400):
    flip = random.randint(250, 500)
    meth = random.randint(0, 1)
    if meth == 1:
        tim = 0.01
    else:
        tim = 0.001
    cx = (x1 + x2) / 2 + random.randint(-50, 50)
    cy = (y1 + y2) / 2 + random.randint(-50, 50)
    steps = duration
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t)**2 * x1 + 2 * (1 - t) * t * cx + t**2 * x2
        y = (1 - t)**2 * y1 + 2 * (1 - t) * t * cy + t**2 * y2
        pyautogui.moveTo(x, y)
        time.sleep(max(0, tim))
        if (i < flip and meth) or (i > flip and not meth):
            tim /= 1.005
        else:
            tim /= 0.995

def expand_loc(x, y):
    return x + random.randint(-30, 30), y + random.randint(-30, 30)

def click(x, y, pause=1):
    pyautogui.click(x, y)
    time.sleep(pause)

def worth():
    counter = 0
    while True:
        time.sleep(1)
        gold, elixir, dark_elixir = read_all_resources()
        if not gold or not elixir or not dark_elixir:
            counter += 1
            if counter >= 5:
                click(*data["next"])
                counter = 0
            continue
        if gold > 350000 or elixir > 350000:
            return
        click(*data["next"])
        counter = 0

def point_on_line(x1, y1, x2, y2, t=random.uniform(0, 1)):
    x = x1 + (x2 - x1) * t
    y = y1 + (y2 - y1) * t
    return x, y


def start_setup():
    _data = {}
    _data["left"] = [None, None, None]
    _data["right"] = [None, None, None]
    _data["top"] = [None, None, None]
    _data["bottom"] = [None, None, None]

    print("SETUP MODE STARTED.")
    print("Move cursor on 'Attack' button and press W.")
    _data["attack"] = grab_coords()
    print("Press attack then move cursor on 'Find a Match' (unranked) button and press W.")
    _data["find_match"] = grab_coords()
    print("Press find a match then move cursor on 'Attack' button and press W.")
    _data["attack2"] = grab_coords()
    print("Before continuing, zoom out all the way on your home village.")
    print("Hop into an attack and do not move your screen at all, if you did, just retry the step")
    print("Move your cursor to the left corner, in the middle of the troop placement area and press W.")
    _data["left"][0] = grab_coords()
    print("Move your cursor to the top corner, in the middle of the troop placement area and press W.")
    _data["top"][0] = grab_coords()
    print("Move your cursor to the right corner, in the middle of the troop placement area and press W.")
    _data["right"][0] = grab_coords()
    print("Move your cursor to the bottom corner, in the middle of the troop placement area and press W")
    print("It doesn't matter if the toolbar is in the way.")
    _data["bottom"][0] = grab_coords()
    print("Move cursor on 'Next' button and press W.")
    _data["next"] = grab_coords()
    print("Move cursor over 'End battle/surrender' button and press W.")
    _data["end"] = grab_coords()
    print("Place anything then press surrender, then move your cursor over the 'Okay' button and press W.")
    _data["end_confirm"] = grab_coords()
    print("Press Okay, and then move your cursor over 'Return Home' button and press W.")
    _data["return"] = grab_coords()
    _data["left"][1] = "top"
    _data["left"][2] = "bottom"
    _data["top"][1] = "right"
    _data["top"][2] = "left"
    _data["right"][1] = "bottom"
    _data["right"][2] = "top"
    _data["bottom"][1] = "left"
    _data["bottom"][2] = "right"
    _data["empty"] = (1350, 1570)
    print("DONE SETUP.\n")
    return _data

def troop_spam(duration):
    time.sleep(random.randint(1, 5))
    corner = ["top", "right", "left"]
    starting_corner = corner[random.randint(0, 2)]

    keyboard.press_and_release('1')
    time.sleep(0.2)
    pyautogui.moveTo(expand_loc(*data[starting_corner][0]))
    pyautogui.mouseDown()
    time.sleep(0.7)
    sneaky_goblins_helper(starting_corner, random.randint(1, 2), 0, duration)
    pyautogui.mouseUp()

    heroes()

    time.sleep(random.randint(25, 35))


def sneaky_goblins_helper(corner, direction, iteration, duration):
    if iteration == 4:
        return
    human_move_to(*expand_loc(*pyautogui.position()), *data[data[corner][direction]][0], duration)
    return sneaky_goblins_helper(data[corner][direction], direction, iteration + 1, duration)

def heroes():
    lst = ["q", "w", "e", "r"]
    corner = ["top", "right", "left"]
    random.shuffle(lst)
    lst.append("z")
    c_name = random.choice(corner)
    c1 = data[c_name][0]
    if c_name == "left" or c_name == "right":
        c2 = data["top"][0]
    else:
        c2 = data[random.choice(["left", "right"])][0]
    for i in range(5):
        keyboard.press_and_release(lst[i])
        time.sleep(0.3)
        click(*point_on_line(*c1, *c2), random.uniform(0.5, 1))
        if i == 4:
            break
        keyboard.press_and_release(lst[i])
        time.sleep(0.3)
    return



def attack(_method):
    time.sleep(3)
    while True:
        click(*data["attack"])
        click(*data["find_match"])
        click(*data["attack2"])
        worth()
        if _method == 1:
            troop_spam(550)
        if _method == 2:
            troop_spam(400)
        click(*data["end"])
        click(*data["end_confirm"])
        click(*data["return"], 4)
        click(*data["empty"])
        click(*data["empty"], 2)

if __name__ == "__main__":
    try:
        print("Warning: Make sure the game is full screen before starting.\n")

        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = start_setup()
            with open(DATA_FILE, "w") as f:
                json.dump(data, f, indent=4)

        print("[1] Sneaky Goblins")
        print("[2] Super Barbs")
        print("What attack would you like to use? ")
        key = input("Enter a number: ")

        if key == "1":
            print("Sneaky Goblins chosen! Farming will begin in 5 seconds, minimize this window.")
            time.sleep(2)
            attack(1)
        if key == "2":
            print("Super Barbs chosen! Farming will begin in 5 seconds, minimize this window.")
            time.sleep(2)
            attack(2)

    except Exception:
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")