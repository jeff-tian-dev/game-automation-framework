import os
import sys
import ctypes
import time
import random
import cv2
import numpy as np
from ctypes import wintypes
from PIL import Image
from pathlib import Path

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    # fallback for older Windows
    ctypes.windll.user32.SetProcessDPIAware()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

APPDATA = Path(os.getenv("APPDATA")) / "AutoLootBot"
SCREENS_DIR = APPDATA / "screens"
SCREENS_DIR.mkdir(parents=True, exist_ok=True)


user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
GetWindowText = user32.GetWindowTextW
GetWindowTextLength = user32.GetWindowTextLengthW
IsWindowVisible = user32.IsWindowVisible

def get_hwnd_partial(name="Clash of Clans") -> int:
    result = {"hwnd": 0}
    def callback(hwnd, lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLength(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                GetWindowText(hwnd, buff, length + 1)
                title = buff.value

                if name.lower() in title.lower():
                    result["hwnd"] = hwnd
                    return False  # stop enumeration

        return True  # keep going

    EnumWindows(EnumWindowsProc(callback), 0)
    return result["hwnd"]

WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP   = 0x0202
WM_MOUSEMOVE   = 0x0200
MK_LBUTTON     = 0x0001
WM_MOUSEWHEEL = 0x020A
WHEEL_DELTA = 120
WM_KEYDOWN = 0x0100
WM_KEYUP   = 0x0101
WM_CHAR    = 0x0102

def move_injector(x, y):
    user32.SendMessageW(hwnd, WM_MOUSEMOVE, MK_LBUTTON, make_lparam(x, y))

def make_lparam(x, y):
    return (y << 16) | (x & 0xFFFF)

FindWindow = user32.FindWindowW
FindWindow.argtypes = (wintypes.LPCWSTR, wintypes.LPCWSTR)
FindWindow.restype = wintypes.HWND

hwnd = get_hwnd_partial(name="Clash of Clans")

def click_inject(x, y):
    lparam = make_lparam(int(x), int(y))
    user32.SendMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
    user32.SendMessageW(hwnd, WM_LBUTTONUP,   0,          lparam)

def human_move_inject(x1, y1, x2, y2, duration=400):
    flip = random.randint(250, 500)
    meth = random.randint(0, 1)
    if meth == 1:
        tim = 0.01
    else:
        tim = 0.001
    cx = (x1 + x2) / 2 + random.randint(-30, 30)
    cy = (y1 + y2) / 2 + random.randint(-30, 30)
    steps = duration
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t)**2 * x1 + 2 * (1 - t) * t * cx + t**2 * x2
        y = (1 - t)**2 * y1 + 2 * (1 - t) * t * cy + t**2 * y2
        user32.SendMessageW(hwnd, WM_MOUSEMOVE, MK_LBUTTON, make_lparam(round(x), round(y)))
        time.sleep(max(0, tim))
        if (i < flip and meth) or (i > flip and not meth):
            tim /= 1.005
        else:
            tim /= 0.995


def mouse_downup_inject(state, x, y):
    if state == 1:
        user32.SendMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, make_lparam(x, y))
    else:
        user32.SendMessageW(hwnd, WM_LBUTTONUP, 0, make_lparam(x, y))

def scroll_inject(x, y, amount):
    delta = int(-1 * WHEEL_DELTA)
    wparam = delta << 16  # high word
    for i in range(amount):
        user32.SendMessageW(hwnd, WM_MOUSEWHEEL, wparam, make_lparam(x, y))
        time.sleep(random.uniform(0.05, 0.2))

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long)]

def screenshot():
    # get window rect
    rect = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    height = rect.bottom - rect.top

    # get window device context
    hwndDC = user32.GetWindowDC(hwnd)
    mfcDC = ctypes.windll.gdi32.CreateCompatibleDC(hwndDC)

    # create a bitmap for the screenshot
    hbitmap = gdi32.CreateCompatibleBitmap(hwndDC, width, height)
    gdi32.SelectObject(mfcDC, hbitmap)

    # PrintWindow: copy window into our bitmap
    PW_RENDERFULLCONTENT = 0x00000002  # works better for some apps, can try 0x0 too
    user32.PrintWindow(hwnd, mfcDC, PW_RENDERFULLCONTENT)

    # create a BITMAPINFOHEADER
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", ctypes.c_long),
            ("biHeight", ctypes.c_long),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", ctypes.c_long),
            ("biYPelsPerMeter", ctypes.c_long),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD)
        ]

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = width
    bmi.biHeight = -height  # negative so origin is top-left
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0  # BI_RGB

    buf_size = width * height * 4
    buffer = (ctypes.c_byte * buf_size)()

    gdi32.GetDIBits(hwndDC, hbitmap, 0, height, ctypes.byref(buffer),
                    ctypes.byref(bmi), 0)

    # turn raw bytes into a PIL image
    img = Image.frombuffer("RGBA", (width, height), bytes(buffer),
                           "raw", "BGRA", 0, 1)

    frame = np.array(img)  # shape (H, W, 4) or (H, W, 3)
    if frame.shape[2] == 4:
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
    else:
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    # cleanup
    gdi32.DeleteObject(hbitmap)
    gdi32.DeleteDC(mfcDC)
    user32.ReleaseDC(hwnd, hwndDC)

    return frame

