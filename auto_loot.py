import pyautogui
import time
import random
import json
import keyboard
from image_cropper import read_all_resources

pyautogui.PAUSE = 0
data = {}

def record_mouse_on_w():
    print("Press 'W' to record mouse position, 'Q' to quit.\n")
    try:
        while True:
            if keyboard.is_pressed('w'):
                x, y = pyautogui.position()
                print(f"Mouse position: ({x}, {y})")
                time.sleep(0.2)  # prevents multiple triggers per press
            elif keyboard.is_pressed('q'):
                print("Stopped listening.")
                break
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("Exited manually.")

def grab_coords():
    keyboard.wait('w')
    return pyautogui.position()

def human_move_to(x1, y1, x2, y2, duration=0.5):
    cx = (x1 + x2) / 2 + random.randint(-50, 50)
    cy = (y1 + y2) / 2 + random.randint(-50, 50)
    steps = int(duration * 120)
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t)**2 * x1 + 2 * (1 - t) * t * cx + t**2 * x2
        y = (1 - t)**2 * y1 + 2 * (1 - t) * t * cy + t**2 * y2
        pyautogui.moveTo(x, y)
        time.sleep(random.uniform(0.0015, 0.0035))

def expand_loc(x, y):
    return x + random.randint(-30, 30), y + random.randint(-30, 30)

def click(x, y, pause=0.5):
    pyautogui.click(x, y)
    time.sleep(pause)

def worth():
    while True:
        time.sleep(random.uniform(5, 8))
        gold, elixir, dark_elixir = read_all_resources()
        if (gold > 750000 or elixir > 750000) and dark_elixir > 7000:
            return
        click(*data["next"])

def start_setup():
    _data = {}
    _data["left"] = [None, None, None]
    _data["right"] = [None, None, None]
    _data["top"] = [None, None, None]
    _data["bottom"] = [None, None, None]

    print("Move cursor on 'Attack' button and press W.")
    _data["attack"] = grab_coords()
    print("Move cursor on 'Find a Match' (unranked) button and press W.")
    _data["find_match"] = grab_coords()
    print("Before continuing, zoom out all the way on your home village.")
    print("In the attack, do not move your screen at all, if you did, just retry the step")
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
    print("Done setup.\n")
    return _data

def sneaky_goblins():
    time.sleep(random.randint(1, 5))
    corner = ["top", "right", "left"]
    starting_corner = corner[random.randint(0, 2)]

    keyboard.press_and_release('1')
    time.sleep(0.2)
    pyautogui.moveTo(expand_loc(*data[starting_corner][0]))
    pyautogui.mouseDown()
    time.sleep(0.7)
    sneaky_goblins_helper(starting_corner, random.randint(1, 2), 0)
    pyautogui.mouseUp()

    time.sleep(random.randint(5, 15))


def sneaky_goblins_helper(corner, direction, iteration):
    if iteration == 4:
        return
    human_move_to(*expand_loc(*pyautogui.position()), *data[data[corner][direction]][0], random.randint(5, 10))
    return sneaky_goblins_helper(data[corner][direction], direction, iteration + 1)

def attack(_method):
    time.sleep(5)
    while True:
        click(*data["attack"])
        click(*data["find_match"])
        worth()
        if _method == 1:
            sneaky_goblins()
        click(*data["end"])
        click(*data["end_confirm"])
        click(*data["return"], 5)

if __name__ == "__main__":
    print("Warning: Make sure the game is full screen before starting.\n")
    try:
        with open("data.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = start_setup()
        with open("data.json", "w") as f:
            json.dump(data, f, indent=4)

    print("[1] Sneaky Goblins")
    print("What attack would you like to use? ")
    key = input("Enter a number: ")

    if key == "1":
        print("Sneaky Goblins chosen! Farming will begin in 5 seconds, minimize this window.")
        time.sleep(2)
        attack(1)
















