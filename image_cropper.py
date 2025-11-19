import os
import sys
import cv2
import numpy as np
from pathlib import Path
from PIL import ImageGrab

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    # Running as PyInstaller onefile EXE
    BASE_DIR = Path(sys._MEIPASS)
else:
    # Running as plain .py
    BASE_DIR = Path(__file__).resolve().parent

APPDATA = Path(os.getenv("APPDATA")) / "AutoLootBot"
SCREENS_DIR = APPDATA / "screens"
SCREENS_DIR.mkdir(parents=True, exist_ok=True)

BLOBS_DIR = APPDATA / "blobs_tmp"
BLOBS_DIR.mkdir(parents=True, exist_ok=True)

def crop_screen(x1, y1, x2, y2, output_name="cropped_screen.png"):
    output_path = SCREENS_DIR / output_name
    try:
        screenshot = ImageGrab.grab()

        crop_box = (x1, y1, x2, y2)
        cropped = screenshot.crop(crop_box)
        cropped.save(output_path)

        return output_path
    except Exception as e:
        print(f"Error while capturing screen: {e}")
        return None

def _preprocess(img_bgr, debug=None):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    otsu_val, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    strict_val = otsu_val + 75
    _, th = cv2.threshold(gray, strict_val, 255, cv2.THRESH_BINARY)

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
    """
    Returns a dict like:
    {'gold': 408201, 'elixir': 290665, 'dark_elixir': 6119}
    """
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

# print(read_all_resources())

