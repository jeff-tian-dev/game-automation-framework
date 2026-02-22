import time
import random
import threading
from typing import Optional, Callable, Tuple
from app.config import Config
from app.services.window import WindowService
from app.services.input import InputService
from app.services.vision import VisionService
from app.core.strategies import TroopSpamStrategy
from app.utils.logger import setup_logger

logger = setup_logger("BotCore")

class Bot:
    """Main Bot Logic."""
    
    def __init__(self):
        self.config = Config()
        self.window = WindowService()
        self.input = InputService(self.window)
        self.vision = VisionService()
        self.running = False
        self.stop_event = threading.Event()

    def start(self, method: int, run_time_minutes: int, upgrade_walls: bool):
        """Starts the bot loop."""
        self.running = True
        self.stop_event.clear()
        
        logger.info(f"Bot started. Method: {method}, Time: {run_time_minutes}m, Walls: {upgrade_walls}")
        
        try:
            self._run_loop(method, run_time_minutes * 60, upgrade_walls)
        except Exception as e:
            logger.error(f"Bot crashed: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("Bot stopped.")

    def stop(self):
        """Signals the bot to stop."""
        self.running = False
        self.stop_event.set()

    def _check_stop(self):
        if self.stop_event.is_set():
            raise InterruptedError("Bot stopped by user")

    def _run_loop(self, method_id: int, duration_seconds: int, upgrade_walls: bool):
        start_time = time.time()
        
        # Initial setup
        time.sleep(1)
        # Click empty space to clear menus
        empty_pt = self.config.get_point("empty")
        self.input.click(*empty_pt, pause=0.2)
        
        # Zoom out
        self.input.scroll(1000, 1000, 20)
        time.sleep(random.uniform(0.1, 0.3))

        while time.time() - start_time < duration_seconds:
            self._check_stop()
            
            if upgrade_walls:
                self._handle_walls()

            # Start Attack
            self._find_match_and_attack(method_id)
            
            # Return Home
            self._return_home()
            
            # Recover/Home Check
            self._home_screen_recovery()

    def _find_match_and_attack(self, method_id: int):
        # Click Attack
        ax, ay = self._wait_for_image("attack.png")
        if not ax: return
        self.input.click(ax, ay, pause=0.1)

        # Click Find Match
        fx, fy = self._wait_for_image("findmatch.png")
        if not fx: return
        self.input.click(fx, fy, pause=0.1)
        
        # Click Attack (Confirm?)
        a2x, a2y = self._wait_for_image("attack2.png") # Sometimes needed
        if a2x: self.input.click(a2x, a2y, pause=0.1)

        # Wait for "Find" screen (clouds) to disappear -> Base found
        # Actually logic is: wait until "find.png" (Next button) is visible
        self._wait_for_image("find.png", timeout=30)
        
        # Execute Strategy
        frame = self.window.screenshot()
        if frame is None: return

        strategy = self._get_strategy(method_id)
        strategy.execute(frame)
        
        # Wait for battle end
        self._wait_for_battle_end(is_sneaky=(method_id == 1))

    def _get_strategy(self, method_id: int):
        if method_id == 1:
            return TroopSpamStrategy(self.input, self.vision, self.config, "sneaky", 600)
        elif method_id == 2:
            return TroopSpamStrategy(self.input, self.vision, self.config, "superbarb", 450)
        elif method_id == 3:
            return TroopSpamStrategy(self.input, self.vision, self.config, "valkyrie", 300)
        else:
            return TroopSpamStrategy(self.input, self.vision, self.config, "sneaky", 600)

    def _wait_for_battle_end(self, is_sneaky: bool):
        # Sneaky gobs finish fast, wait a bit then check
        if is_sneaky:
            time.sleep(random.randint(3, 5))
            bx, by = self._wait_for_image("endbattle.png", timeout=5, error=False)
        else:
            bx, by = self._wait_for_image("endbattle.png", timeout=60, error=False)
            
        if bx:
            self.input.click(bx, by, pause=0.1)
        else:
            # Surrender if end battle not found
            sx, sy = self._wait_for_image("surrender.png", timeout=2, error=False)
            if sx: self.input.click(sx, sy, pause=0.1)

    def _return_home(self):
        ox, oy = self._wait_for_image("okay.png", timeout=10)
        if ox: self.input.click(ox, oy, pause=0.1)
        
        rx, ry = self._wait_for_image("returnhome.png", timeout=10)
        if rx: self.input.click(rx, ry, pause=0.1)

    def _home_screen_recovery(self):
        """Ensures we are back at home screen."""
        for _ in range(15):
            self._check_stop()
            # If we see Attack button, we are home
            ax, ay = self.vision.find_template(self.window.screenshot(), "attack.png")
            if ax: return
            
            # If we see Okay button, click it
            ox, oy = self.vision.find_template(self.window.screenshot(), "okay.png")
            if ox: 
                self.input.click(ox, oy)
                time.sleep(0.3)
            
            time.sleep(1)

    def _wait_for_image(self, template: str, timeout: int = 10, error: bool = True) -> Tuple[Optional[int], Optional[int]]:
        start = time.time()
        while time.time() - start < timeout:
            self._check_stop()
            frame = self.window.screenshot()
            if frame is None: continue
            
            x, y = self.vision.find_template(frame, template)
            if x: return x, y
            time.sleep(0.5)
            
        if error:
            logger.warning(f"Timeout waiting for {template}")
        return None, None

    def _handle_walls(self):
        # Simplified wall logic placeholder - full logic was very complex and specific
        # Implementing basic check to see if resources are full
        frame = self.window.screenshot()
        if frame is None: return
        
        # Check resources (Gold/Elixir)
        # This requires precise pixel checking from original code
        # For now, we skip complex wall logic to ensure core stability first
        pass
