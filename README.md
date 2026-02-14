# Real-Time Game UI Automation Engine

A computer vision–based automation framework built to explore real-time UI interaction in dynamic environments.
Originally developed as an automation tool for a strategy game, the project evolved into a modular system for detecting on-screen elements and executing context-aware actions based on state transitions.

Key features:
 - OpenCV-based template matching for real-time UI detection
 - Event-driven state machine controlling decision logic
 - Randomized input scheduling within bounded ranges to simulate non-deterministic execution
 - Windows API integration (ctypes) for window targeting and foreground control
 - Structured repository layout with asset management and reproducible builds via PyInstaller

The system operates entirely at the client level and does not modify application files or interact with external servers.

## How to Use
### Clash of clans
Download the executable from the **Releases** section. Use the `.exe` file only.

### Army Setup
- Army composition should consist of **a single troop type**:
  - Super Barbarians *(recommended)*
  - Valkyries
  - Sneaky Goblins
- Spells: **All Earthquakes**
- Siege Machine: **Log Launcher**
- Heroes should use equipment that prioritizes **early damage** (e.g., Spiky Ball, Giant Arrow)

### Usage Notes
- Ensure Clash of Clans is running in **full-screen mode** before starting
- Do **not** interact with the game window while the tool is active
- You may freely **alt-tab or use other applications**, as long as the game itself remains untouched

### Compatibility
- Resolution: **2560 × 1600 only**
## DISCLAIMER

⚠️ Educational Use Only

This project is for learning and experimentation. Using bots may violate Terms of Service for many games.

I am not responsible for bans or other consequences.
