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

EnumChildWindows = user32.EnumChildWindows
EnumChildWindows.argtypes = [
    wintypes.HWND,
    EnumWindowsProc,
    wintypes.LPARAM,
]
EnumChildWindows.restype = wintypes.BOOL

WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP   = 0x0202
WM_MOUSEMOVE   = 0x0200
MK_LBUTTON     = 0x0001
WM_MOUSEWHEEL = 0x020A
WHEEL_DELTA = 120
WM_KEYDOWN = 0x0100
WM_KEYUP   = 0x0101
WM_CHAR    = 0x0102

def get_hwnd_partial(name="Clash of Clans", child_class="CROSVM_1") -> int:
    """
    Returns the child HWND (e.g. CROSVM_1) under the top-level window whose title
    contains `name`. Falls back to the top-level HWND if the child isn't found.
    """
    result = {"hwnd": 0}

    # --- helpers ---
    def get_class(hwnd) -> str:
        buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buf, 256)
        return buf.value

    def find_descendant_by_class(root_hwnd, target_class) -> int:
        found = {"hwnd": 0}

        def enum_child_cb(child_hwnd, lParam):
            # check this child
            if get_class(child_hwnd) == target_class:
                found["hwnd"] = child_hwnd
                return False  # stop enumeration

            # recurse into grandchildren
            EnumChildWindows(child_hwnd, EnumWindowsProc(enum_child_cb), 0)
            return True

        EnumChildWindows(root_hwnd, EnumWindowsProc(enum_child_cb), 0)
        return found["hwnd"]

    # --- find the top-level window by title, then return the desired child ---
    def enum_top_cb(hwnd, lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLength(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                GetWindowText(hwnd, buff, length + 1)
                title = buff.value

                if name.lower() in title.lower():
                    # found top-level; now find child render window
                    child = find_descendant_by_class(hwnd, child_class)
                    result["hwnd"] = child if child else hwnd
                    return False  # stop enumeration

        return True

    EnumWindows(EnumWindowsProc(enum_top_cb), 0)
    return result["hwnd"]

FindWindow = user32.FindWindowW
FindWindow.argtypes = (wintypes.LPCWSTR, wintypes.LPCWSTR)
FindWindow.restype = wintypes.HWND

hwnd = get_hwnd_partial(name="Clash of Clans")


def move_injector(x, y):
    user32.SendMessageW(hwnd, WM_MOUSEMOVE, MK_LBUTTON, make_lparam(x, y))

def make_lparam(x, y):
    return (y << 16) | (x & 0xFFFF)

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

#
#
#
# GetClassNameW = user32.GetClassNameW
# GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
# GetClassNameW.restype = ctypes.c_int
#
# GetClientRect = user32.GetClientRect
# GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
# GetClientRect.restype = wintypes.BOOL
#
# GetWindowRect = user32.GetWindowRect
# GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
# GetWindowRect.restype = wintypes.BOOL
#
# IsWindowVisible = user32.IsWindowVisible
# IsWindowVisible.argtypes = [wintypes.HWND]
# IsWindowVisible.restype = wintypes.BOOL
#
# IsWindowEnabled = user32.IsWindowEnabled
# IsWindowEnabled.argtypes = [wintypes.HWND]
# IsWindowEnabled.restype = wintypes.BOOL
# user32 = ctypes.windll.user32
#
# # constants
# GWL_STYLE   = -16
# GWL_EXSTYLE = -20
#
# # pick the right function for pointer size
# if ctypes.sizeof(ctypes.c_void_p) == 8:
#     GetWindowLongPtr = user32.GetWindowLongPtrW
#     GetWindowLongPtr.argtypes = [wintypes.HWND, ctypes.c_int]
#     GetWindowLongPtr.restype = ctypes.c_longlong
# else:
#     GetWindowLongPtr = user32.GetWindowLongW
#     GetWindowLongPtr.argtypes = [wintypes.HWND, ctypes.c_int]
#     GetWindowLongPtr.restype = ctypes.c_long
#
#
# def build_hwnd_tree(root_hwnd):
#     """
#     Returns a recursive tree of all HWNDs under root_hwnd.
#
#     {
#         "hwnd": int,
#         "children": [ ... ]
#     }
#     """
#
#     def build_node(hwndd):
#         node = {
#             "hwnd": hwndd,
#             "children": []
#         }
#
#         def enum_child_callback(child_hwnd, lParam):
#             node["children"].append(build_node(child_hwnd))
#             return True
#
#         EnumChildWindows(hwndd, EnumWindowsProc(enum_child_callback), 0)
#         return node
#
#     return build_node(root_hwnd)
#
# def dump_hwnd_tree(tree):
#     from ctypes import wintypes
#
#     GetClassNameW = user32.GetClassNameW
#     GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
#
#     GetWindowRect = user32.GetWindowRect
#     GetClientRect = user32.GetClientRect
#
#     GetWindowThreadProcessId = user32.GetWindowThreadProcessId
#
#     def walk(node, depth=0, parent=None):
#         hwnd = node["hwnd"]
#
#         # title
#         title = ""
#         length = GetWindowTextLength(hwnd)
#         if length > 0:
#             buf = ctypes.create_unicode_buffer(length + 1)
#             GetWindowText(hwnd, buf, length + 1)
#             title = buf.value
#
#         # class
#         cls_buf = ctypes.create_unicode_buffer(256)
#         GetClassNameW(hwnd, cls_buf, 256)
#         cls = cls_buf.value
#
#         # rects
#         wr = wintypes.RECT()
#         cr = wintypes.RECT()
#         GetWindowRect(hwnd, ctypes.byref(wr))
#         GetClientRect(hwnd, ctypes.byref(cr))
#
#         cw = cr.right - cr.left
#         ch = cr.bottom - cr.top
#
#         # styles
#         style = GetWindowLongPtr(hwnd, GWL_STYLE)
#         exstyle = GetWindowLongPtr(hwnd, GWL_EXSTYLE)
#
#         # proc / thread
#         pid = wintypes.DWORD()
#         tid = GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
#
#         indent = "  " * depth
#         print(f"""{indent}HWND: {hex(hwnd)}
# {indent}  parent: {hex(parent) if parent else None}
# {indent}  class: {cls}
# {indent}  title: {title}
# {indent}  visible: {bool(IsWindowVisible(hwnd))}  enabled: {bool(IsWindowEnabled(hwnd))}
# {indent}  window_rect: ({wr.left},{wr.top},{wr.right},{wr.bottom})
# {indent}  client_size: {cw}x{ch}
# {indent}  style: 0x{style:08X}  exstyle: 0x{exstyle:08X}
# {indent}  pid: {pid.value}  tid: {tid}
# """)
#
#         for c in node["children"]:
#             walk(c, depth + 1, hwnd)
#
#     walk(tree)
#
# root = get_hwnd_partial("Clash of Clans")
# tree = build_hwnd_tree(root)
#
# dump_hwnd_tree(tree)
#
# class POINT(ctypes.Structure):
#     _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]
#
# WindowFromPoint = user32.WindowFromPoint
# WindowFromPoint.argtypes = [POINT]
# WindowFromPoint.restype = wintypes.HWND
#
# def hwnd_under_cursor(delay=2.0):
#     time.sleep(delay)  # give you time to move the mouse
#     pt = POINT()
#     user32.GetCursorPos(ctypes.byref(pt))
#     return WindowFromPoint(pt), (pt.x, pt.y)
#
# hw, (x, y) = hwnd_under_cursor()
# print("under cursor:", hex(hw), "at", x, y)