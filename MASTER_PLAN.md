# Master Plan: Jarvis "Computer Use" Agent (Final Edition)

## 1. Project Overview
The goal is to build an autonomous AI agent named **Jarvis**. It will interact with the Windows OS using mouse/keyboard controls and high-level reasoning powered by **Google Gemini API**. 

## 2. Technology Stack & Bootstrapping
* **Language:** Python 3.11+
* **Environment:** Automatic VENV creation via `run_jarvis.bat`.
* **AI Engine:** `google-genai` (Unified SDK).
* **Vision/Computer Use:** `mss`, `PyAutoGUI`, `Pillow`.
* **GUI:** `CustomTkinter` (Modern Desktop Interface).
* **Auto-Discovery:** PowerShell (`Get-StartApps`), `winreg`, `shutil`.
* **Localization:** Entire User Interface and logs MUST be in **Polish**.

## 3. Automation & Setup
* **Launcher Script (`run_jarvis.bat`):** * Logic: Detect existing Python versions -> Select 3.11 or newer.
    * Fallback: If no suitable Python is found, attempt to install via winget or alert the user.
    * Automation: Create `.venv` -> Upgrade pip -> Install requirements.
    * Launch: Run `main.py` in the isolated environment.
* **Documentation:** Polish `README.md` with setup instructions.

## 4. Implementation Phases

### Phase 1: Bootstrapping & Repository Structure
* Create `run_jarvis.bat` with version detection.
* Define modular folder structure (gui/, vision/, controller/, discovery/).
* Write Polish `README.md`.

### Phase 2: Environment & Modern UI (Polish Language)
* Build the main dashboard in `CustomTkinter`.
* Interface components: Input box, action log, system stats, "Stop" button.
* UI must be fully localized in Polish.

### Phase 3: Autonomous "Eyes" & "Hands"
* Implement `vision.py` (mss) and `controller.py` (PyAutoGUI).
* Visual Grounding: Map screen elements to [x, y] coordinates via Gemini.

### Phase 4: Discovery System
* Implement `discovery.py`: Automatic app scanning (Start Menu, Registry, PATH).
* Integration with fuzzy matching (RapidFuzz).

### Phase 5: Brain & Agent Loop
* Integrate `google-genai`.
* Reasoning loop: Screenshot -> Analyze -> Act -> Verify.
