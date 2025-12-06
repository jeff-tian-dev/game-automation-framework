import os
import sys
import cv2
import numpy as np
from pathlib import Path
from click_injector import screenshot_window_hwnd

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    # Running as PyInstaller onefile EXE
    BASE_DIR = Path(sys._MEIPASS)
else:
    # Running as plain .py
    BASE_DIR = Path(__file__).resolve().parent

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

APPDATA = Path(os.getenv("APPDATA")) / "AutoLootBot"
SCREENS_DIR = APPDATA / "screens"
SCREENS_DIR.mkdir(parents=True, exist_ok=True)

BLOBS_DIR = APPDATA / "blobs_tmp"
BLOBS_DIR.mkdir(parents=True, exist_ok=True)

def crop_screen(x1, y1, x2, y2, output_name="cropped_screen.png"):
    screenshot_window_hwnd()
    img = cv2.imread(str(SCREENS_DIR / "window_pw.png"))
    cropped = img[y1:y2, x1:x2]
    cv2.imwrite(str(SCREENS_DIR / output_name), cropped)

def _preprocess(img_bgr, debug=None):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 235, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
    th = cv2.dilate(th, kernel, iterations=1)

    # Save debug
    if debug:
        cv2.imwrite(f"{debug}_gray.png", gray)
        cv2.imwrite(f"{debug}_bin.png", th)

    return th

def find_digit_boxes(bin_img, out_dir="blobs"):
    """Return bounding boxes (x, y, w, h) for each digit-like blob."""
    out_dir = BLOBS_DIR  # ignore any custom string dirs

    os.makedirs(out_dir, exist_ok=True)

    # Find connected white components
    n, _, stats, _ = cv2.connectedComponentsWithStats(bin_img, connectivity=8)
    H, W = bin_img.shape

    boxes = []

    for i in range(1, n):  # skip background
        x, y, w, h, area = stats[i]

        # filter small noise
        if w < 3 or h < 3:
            continue

        # filter huge accidental blobs
        if h > int(H * 0.95) and w > int(W * 0.95):
            continue

        boxes.append((x, y, w, h))

    # Sort boxes left → right
    boxes.sort(key=lambda b: b[0])

    # Extract and save each blob
    for idx, (x, y, w, h) in enumerate(boxes):
        roi = bin_img[y:y + h, x:x + w]

        filename = os.path.join(out_dir, f"digit_{idx}.png")
        cv2.imwrite(filename, roi)

    return boxes

THRESH_VAL = 200  # same idea as your _preprocess threshold

def load_templates_binary(template_dir="templates"):
    templates = {}
    tdir = BASE_DIR / template_dir

    for d in range(10):
        path = tdir / f"{d}.png"
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise FileNotFoundError(f"Template missing: {path}")

        # binarize to 0/1
        bin01 = (img >= THRESH_VAL).astype(np.uint8)
        templates[d] = bin01

    return templates

def classify_digit_by_templates(blob_img, templates, min_score=0.7):
    """
    blob_img: single digit cutout (0 or 255, white on black).
    templates: dict {digit: 0/1 template array}.
    Returns (best_digit or None, best_score).
    """

    # ensure 0/1
    blob = blob_img.copy()
    if blob.max() > 1:
        blob = (blob >= THRESH_VAL).astype(np.uint8)

    best_digit = None
    best_score = -1.0

    for digit, tmpl in templates.items():
        th, tw = tmpl.shape

        # resize blob to template size
        resized = cv2.resize(blob, (tw, th), interpolation=cv2.INTER_NEAREST)
        resized = (resized > 0).astype(np.uint8)

        tmpl_fg = tmpl
        ones_in_tmpl = int(tmpl_fg.sum())
        if ones_in_tmpl == 0:
            continue

        # overlap where template expects 1s
        overlap = int((resized & tmpl_fg).sum())
        coverage = overlap / ones_in_tmpl  # how much of template is matched

        # penalty: 1s in blob where template has 0
        extra = int((resized & (1 - tmpl_fg)).sum())
        extra_norm = extra / ones_in_tmpl

        score = coverage - 0.3 * extra_norm  # tweak penalty weight if needed

        if score > best_score:
            best_score = score
            best_digit = digit

    if best_score < min_score:
        return None, best_score
    return best_digit, best_score

def read_number_with_templates(img_name, templates, debug=False):
    for f in BLOBS_DIR.glob("*.png"):
        f.unlink(missing_ok=True)

    img_path = SCREENS_DIR / img_name
    img = cv2.imread(str(img_path))
    if img is None:
        raise FileNotFoundError(img_path)

    # 1) binarize (your function)
    bin_img = _preprocess(img, debug=Path(img_path).stem if debug else None)

    # 2) find digit blobs (your function)
    boxes = find_digit_boxes(bin_img, out_dir="blobs_debug" if debug else "blobs_tmp")

    if debug:
        print(f"[{img_path}] boxes: {boxes}")

    # 3) classify each blob
    digits = []
    for (x, y, w, h) in boxes:
        blob = bin_img[y:y+h, x:x+w]
        d, score = classify_digit_by_templates(blob, templates)
        if debug:
            print(f"  box {(x, y, w, h)} -> {d} (score={score:.3f})")
        if d is not None:
            digits.append(str(d))

    if not digits:
        return None

    return int("".join(digits))

def read_all_resources(template_dir="templates", debug=False):
    templates = load_templates_binary(template_dir)

    crop_screen(115, 175, 350, 230, "gold.png")
    crop_screen(115, 250, 350, 300, "elixir.png")
    crop_screen(115, 320, 275, 370, "dark_elixir.png")

    result = [
        read_number_with_templates("gold.png",        templates, debug=debug),
        read_number_with_templates("elixir.png",      templates, debug=debug),
        read_number_with_templates("dark_elixir.png", templates, debug=debug),
    ]
    return result

def home_resources(template_dir="templates", debug=False):
    templates = load_templates_binary(template_dir)

    crop_screen(2150, 57, 2420, 101, "home_gold.png")
    crop_screen(2150, 183, 2420, 227, "home_elixir.png")
    crop_screen(2240, 303, 2420, 351, "home_dark_elixir.png")

    result = [
        read_number_with_templates("home_gold.png", templates, debug=debug),
        read_number_with_templates("home_elixir.png", templates, debug=debug),
        read_number_with_templates("home_dark_elixir.png", templates, debug=debug),
    ]
    return result

def detect_brightest(x1, y1, x2, y2):
    img_path = SCREENS_DIR / "window_pw.png"
    img = cv2.imread(str(img_path))

    crop = img[y1:y2, x1:x2]

    # Sum BGR values for each pixel → approximate brightness
    brightness = crop.sum(axis=2)  # shape (h,w), values ~0–765

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(brightness)

    return int(max_val)

def find_icon_img(template_path, region, threshold=0.85, filename="window_pw.png", screenshot=True):
    if screenshot:
        screenshot_window_hwnd()
    img_path = SCREENS_DIR / filename
    img = cv2.imread(str(img_path))
    template = cv2.imread(str(resource_path(template_path)))

    # Crop region
    x, y, w, h = region
    cropped = img[y:y + h, x:x + w]

    # Template match
    result = cv2.matchTemplate(cropped, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    # If match too weak → return None
    if max_val < threshold:
        return None

    # Convert local coords → global screen coords
    template_h, template_w = template.shape[:2]
    match_x = x + max_loc[0] + template_w // 2
    match_y = y + max_loc[1] + template_h // 2

    # Return center of detected icon + confidence
    return match_x, match_y

def find_all_icon_img(template_path, region, text=False, threshold=0.85, filename="window_pw.png", screenshot=True):
    if screenshot:
        screenshot_window_hwnd()
    img_path = SCREENS_DIR / filename
    img = cv2.imread(str(img_path))
    template = cv2.imread(str(resource_path(template_path)))

    # Region crop
    x, y, w, h = region
    cropped = img[y:y + h, x:x + w]
    if text:
        # Convert to grayscale
        cropped_gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        # Threshold: pixels > 200 -> 255 (white), else 0 (black)
        # 200 is your brightness cutoff – change this to tweak sensitivity.
        _, cropped_bin = cv2.threshold(cropped_gray, 200, 255, cv2.THRESH_BINARY)
        _, template_bin = cv2.threshold(template_gray, 200, 255, cv2.THRESH_BINARY)

        # cv2.imwrite("debug_cropped_gray.png", cropped_gray)
        # cv2.imwrite("debug_template_gray.png", template_gray)
        # cv2.imwrite("debug_cropped_bin.png", cropped_bin)
        # cv2.imwrite("debug_template_bin.png", template_bin)

        # Template match on binarized images
        result = cv2.matchTemplate(cropped_bin, template_bin, cv2.TM_SQDIFF_NORMED)
        yloc, xloc = (1.0 - result >= threshold).nonzero()
    else:
        # Normal template matching on color images
        result = cv2.matchTemplate(cropped, template, cv2.TM_CCOEFF_NORMED)
        yloc, xloc = (result >= threshold).nonzero()

    th, tw = template.shape[:2]

    points = []


    for (px, py) in zip(xloc, yloc):
        cx = px + tw // 2
        cy = py + th // 2

        screen_x = x + cx
        screen_y = y + cy
        conf = float(result[py, px])
        if text:
            conf = 1.0 - conf

        points.append((screen_x, screen_y, conf))

    filtered = []
    radius = min(tw, th) // 2  # distance threshold

    for pt in points:
        if all(((pt[0] - f[0])**2 + (pt[1] - f[1])**2)**0.5 > radius for f in filtered):
            filtered.append(pt)

    return filtered

# print(find_all_icon_img("templates/wall.png",(800, 200, 400, 800), text=True, threshold=0.70))

# print(find_all_icon_img(resource_path("templates/testing.png"), (1000, 1000, 1000, 500), text=False, threshold=0.85))

# print(detect_by_saturation(1523, 792, 1628, 813))
# print(home_resources())

# print(detect_brightest(1393, 496, 1456, 530))
# print(detect_brightest(1405, 422, 1465, 456))
