import os
import sys
import time
import cv2
import pyautogui
import numpy as np
from pathlib import Path
from click_injector import screenshot

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return str(os.path.join(base_path, "templates/" + relative_path))

APPDATA = Path(os.getenv("APPDATA")) / "AutoLootBot"
screenx, screeny = pyautogui.size()

def crop_screen(img, x1, y1, x2, y2):
    return img[y1:y2, x1:x2]

def find_icon_img(img, template_path, region=(0, 0, int(screenx), int(screeny)), threshold=0.8):
    template = cv2.imread(resource_path(template_path))

    # Crop region
    x, y, w, h = region
    cropped = img[y:y + h, x:x + w]
    # cv2.imwrite("debug_cropped.png", cropped)

    # Template match
    result = cv2.matchTemplate(cropped, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    # print(max_val)

    # If match too weak → return None
    if max_val < threshold:
        return None, None

    # Convert local coords → global screen coords
    template_h, template_w = template.shape[:2]
    match_x = x + max_loc[0] + template_w // 2
    match_y = y + max_loc[1] + template_h // 2

    # Return center of detected icon + confidence
    return match_x, match_y

def find_all_icon_img(img, template_path, region=(0, 0, screenx, screeny), text=False, threshold=0.85):
    template = cv2.imread(resource_path(template_path))

    # Region crop
    x, y, w, h = region
    cropped = img[y:y + h, x:x + w]
    if text:
        cropped_gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))

        cropped_processed = cv2.morphologyEx(cropped_gray, cv2.MORPH_TOPHAT, kernel)
        template_processed = cv2.morphologyEx(template_gray, cv2.MORPH_TOPHAT, kernel)

        cropped_processed = cv2.GaussianBlur(cropped_processed, (3, 3), 0)
        template_processed = cv2.GaussianBlur(template_processed, (3, 3), 0)
        # cv2.imwrite("debug_cropped_tophat.png", cropped_processed)
        # cv2.imwrite("debug_template_tophat.png", template_processed)

        result = cv2.matchTemplate(cropped_processed, template_processed, cv2.TM_CCOEFF_NORMED)
        yloc, xloc = (result >= threshold).nonzero()
    else:
        # Normal template matching on color images
        result = cv2.matchTemplate(cropped, template, cv2.TM_CCOEFF_NORMED)
        yloc, xloc = (result >= threshold).nonzero()

    th, tw = template.shape[:2]

    points = []
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    # print(max_val)

    for (px, py) in zip(xloc, yloc):
        cx = px + tw // 2
        cy = py + th // 2

        screen_x = x + cx
        screen_y = y + cy

        points.append((screen_x, screen_y))

    filtered = []
    radius = min(tw, th) // 2  # distance threshold

    for pt in points:
        if all(((pt[0] - f[0])**2 + (pt[1] - f[1])**2)**0.5 > radius for f in filtered):
            filtered.append(pt)

    return filtered


def exact_color_fraction(img, target_hsv, tolerance=5, save=False):
    if img is None:
        raise ValueError("Could not load image")

        # Convert the image to HSV
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 1. Extract just the Hue (H) from the target tuple
    target_hue = target_hsv[0]

    # 2. Define the range
    # Hue: target +/- tolerance (clipped to 0-179)
    # Saturation & Value: Hardcoded to 100-255 (ignores gamma/lighting shifts)
    h_min = max(0, target_hue - tolerance)
    h_max = min(179, target_hue + tolerance)

    lower = np.array([h_min, 100, 100], dtype=np.uint8)
    upper = np.array([h_max, 255, 255], dtype=np.uint8)

    # 3. Create Mask
    mask = cv2.inRange(hsv_img, lower, upper)

    if save:
        debug_img = img.copy()
        # Highlight matched pixels with Neon Magenta
        debug_img[mask > 0] = (255, 0, 255)

        # Check Hue to guess if it is Gold (Yellow/Orange) or Elixir (Purple)
        # Gold/Orange is usually Hue 15-30. Purple is 140-160.
        if target_hue < 50:
            cv2.imwrite("golddd.png", debug_img)
        else:
            cv2.imwrite("elixirrr.png", debug_img)

    matched_pixels = cv2.countNonZero(mask)
    total_pixels = img.shape[0] * img.shape[1]

    if total_pixels < 5:
        return 0.0

    return matched_pixels / total_pixels

def find_leftmost_pixel(img, target_hsv, tolerance=5, save=False):
    if img is None:
        return None
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    target_hue = target_hsv[0]

    h_min = max(0, target_hue - tolerance)
    h_max = min(179, target_hue + tolerance)

    lower = np.array([h_min, 100, 100], dtype=np.uint8)
    upper = np.array([h_max, 255, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv_img, lower, upper)

    ys, xs = np.nonzero(mask)

    if save:
        debug_img = img.copy()
        # Apply highlight where mask is white (255)
        debug_img[mask > 0] = (255, 0, 255)
        if target_hsv == (24, 241, 203):
            cv2.imwrite("golddd.png", debug_img)
        else:
            cv2.imwrite("elixirrr.png", debug_img)

    if len(xs) == 0:
        return None, None

    min_idx = np.argmin(xs)
    return int(xs[min_idx]), int(ys[min_idx])


# print(find_all_icon_img("templates/wall.png",(800, 200, 400, 800), text=True, threshold=0.70))

# print(find_all_icon_img(resource_path("templates/testing.png"), (1000, 1000, 1000, 500), text=False, threshold=0.85))

# print(detect_by_saturation(1523, 792, 1628, 813))

# print(find_all_icon_img(screenshot(), "wall.png", (700, 200, 600, 800), text=True, threshold=0.9))

# print(find_icon_img(screenshot(), "addwall.png"))

# frame = screenshot()

# print(exact_color_fraction(frame[95:105, 2060:2420], target_bgr=(11, 169, 203), tolerance=0))
# print(exact_color_fraction(frame[220:230, 2060:2420], target_bgr=(169, 34, 169), tolerance=0))

# frame = screenshot()
# print(find_leftmost_pixel(frame[95:105, 2060:2420], target_hsv=(24, 241, 203), tolerance=5, save=True))
# print(find_leftmost_pixel(frame[220:230, 2060:2420], target_hsv=(149, 203, 169), tolerance=5, save=True))
#
