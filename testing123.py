import colorsys

import pyautogui
import keyboard
import time
import ctypes
from ctypes import wintypes
# from app.services.window import WindowService
# from app.services.vision import VisionService


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


def record_hsv_on_w():
    print("Press 'W' to record HSV under cursor, 'Q' to quit.\n")

    try:
        while True:
            if keyboard.is_pressed('w'):
                x, y = pyautogui.position()

                # Screenshot 1x1 pixel at cursor
                r, g, b = pyautogui.screenshot(
                    region=(x, y, 1, 1)
                ).getpixel((0, 0))

                # Convert RGB [0–255] → [0–1]
                r_f, g_f, b_f = r / 255.0, g / 255.0, b / 255.0

                # RGB → HSV
                h, s, v = colorsys.rgb_to_hsv(r_f, g_f, b_f)

                # Optional: scale to common OpenCV-style ranges
                h_deg = int(h * 179)   # OpenCV hue range: 0–179
                s_255 = int(s * 255)
                v_255 = int(v * 255)

                print(f"HSV @ ({x}, {y}): ({h_deg}, {s_255}, {v_255})")

                time.sleep(0.2)  # debounce

            elif keyboard.is_pressed('q'):
                print("Stopped listening.")
                break

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Exited manually.")

#Mouse position: (2064, 57)
#Mouse position: (2524, 99)
#BGR @ (2412, 97): (11, 169, 203)

#Mouse position: (2066, 180)
#Mouse position: (2524, 228)
#BGR @ (2417, 223): (169, 34, 169)

# (1280, 1348)
record_mouse_on_w()

#Mouse position: (1196, 1325)
#Mouse position: (1363, 1361)
