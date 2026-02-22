import ctypes
import time
import random
from app.services.window import WindowService, WM_LBUTTONDOWN, WM_LBUTTONUP, WM_MOUSEMOVE, MK_LBUTTON, WM_MOUSEWHEEL, WHEEL_DELTA
from app.utils.logger import setup_logger

logger = setup_logger("InputService")

class InputService:
    """Handles mouse and keyboard injection."""
    
    def __init__(self, window_service: WindowService):
        self.window_service = window_service
        self.user32 = ctypes.windll.user32

    def _make_lparam(self, x: int, y: int) -> int:
        return (y << 16) | (x & 0xFFFF)

    def click(self, x: int, y: int, pause: float = 1.0, rand: bool = True):
        """Performs a click with optional randomization and delay."""
        if rand:
            x += random.randint(-15, 15)
            y += random.randint(-15, 15)
        
        self._inject_click(x, y)
        
        # Randomized sleep
        sleep_time = random.uniform(pause - (pause * 0.2), pause + (pause * 0.2))
        time.sleep(max(0.1, sleep_time))

    def _inject_click(self, x: int, y: int):
        hwnd = self.window_service.hwnd
        if not hwnd:
            return
            
        lparam = self._make_lparam(int(x), int(y))
        self.user32.SendMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
        self.user32.SendMessageW(hwnd, WM_LBUTTONUP, 0, lparam)

    def mouse_down(self, x: int, y: int):
        hwnd = self.window_service.hwnd
        if not hwnd: return
        self.user32.SendMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, self._make_lparam(x, y))

    def mouse_up(self, x: int, y: int):
        hwnd = self.window_service.hwnd
        if not hwnd: return
        self.user32.SendMessageW(hwnd, WM_LBUTTONUP, 0, self._make_lparam(x, y))

    def move(self, x: int, y: int):
        hwnd = self.window_service.hwnd
        if not hwnd: return
        self.user32.SendMessageW(hwnd, WM_MOUSEMOVE, MK_LBUTTON, self._make_lparam(x, y))

    def human_move(self, x1: int, y1: int, x2: int, y2: int, duration: int = 400):
        """Simulates human-like mouse movement using a Bezier curve-like approach."""
        hwnd = self.window_service.hwnd
        if not hwnd: return

        # Randomize control point for curve
        cx = (x1 + x2) / 2 + random.randint(-30, 30)
        cy = (y1 + y2) / 2 + random.randint(-30, 30)
        
        steps = duration
        # Randomize timing curve
        flip = random.randint(int(steps * 0.3), int(steps * 0.7))
        method = random.randint(0, 1)
        tim = 0.01 if method == 1 else 0.001

        for i in range(steps + 1):
            t = i / steps
            # Quadratic Bezier
            x = (1 - t)**2 * x1 + 2 * (1 - t) * t * cx + t**2 * x2
            y = (1 - t)**2 * y1 + 2 * (1 - t) * t * cy + t**2 * y2
            
            self.move(int(x), int(y))
            
            time.sleep(max(0, tim))
            
            # Accelerate/Decelerate logic
            if (i < flip and method) or (i > flip and not method):
                tim /= 1.005
            else:
                tim /= 0.995

    def scroll(self, x: int, y: int, amount: int):
        hwnd = self.window_service.hwnd
        if not hwnd: return
        
        delta = int(-1 * WHEEL_DELTA)
        wparam = delta << 16
        lparam = self._make_lparam(x, y)
        
        for _ in range(amount):
            self.user32.SendMessageW(hwnd, WM_MOUSEWHEEL, wparam, lparam)
            time.sleep(random.uniform(0.05, 0.2))
