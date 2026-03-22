# No Companion — Patient CDA Generator
## Complete Setup & Build Guide (VS Code Terminal)

---

## PROJECT STRUCTURE

```
patient_generator/
├── main.py          ← Entry point (run this or build this)
├── gui.py           ← Tkinter GUI
├── generators.py    ← All randomization / generation logic
├── cda_builder.py   ← Converts patient dict → HL7 CDA XML
├── data.py          ← All reference data (diagnoses, meds, labs, etc.)
├── requirements.txt ← Dev dependency list
└── README.md        ← This file
```

---

## PREREQUISITES

1. **Python 3.9 or newer** (required for `ET.indent()`)
   - Download: https://www.python.org/downloads/
   - During install → check ✅ "Add Python to PATH"
   - Verify in terminal: `python --version`

2. **VS Code** with the Python extension installed

3. **tkinter** (bundled with Python on Windows — no extra step needed)
   - On Linux only: `sudo apt install python3-tk`

---

## STEP 1 — OPEN THE PROJECT IN VS CODE

```bash
# In VS Code: File → Open Folder → select patient_generator/
# Then open the integrated terminal: View → Terminal  (or Ctrl + `)
```

---

## STEP 2 — CREATE A VIRTUAL ENVIRONMENT (recommended)

```bash
# Inside the patient_generator/ folder:
python -m venv venv

# Activate it (Windows):
venv\Scripts\activate

# Activate it (Mac/Linux):
source venv/bin/activate

# You should see (venv) at the start of your terminal prompt.
```

---

## STEP 3 — INSTALL PYINSTALLER

PyInstaller is the only package you need to install.
The app itself uses only Python stdlib — nothing else to pip install.

```bash
pip install pyinstaller
```

Verify:
```bash
pyinstaller --version
```

---

## STEP 4 — RUN IN DEV MODE (test before building)

Always test in Python before building the exe:

```bash
python main.py
```

The GUI window should appear. Try generating 1 patient at Simple, Moderate, and Complex.
Check the output folder on your Desktop (or wherever you set it).

If you see any errors, they'll print to the terminal — much easier to debug here than in the exe.

---

## STEP 5 — BUILD THE STANDALONE EXECUTABLE

```bash
pyinstaller --onefile --windowed --name "NoCompanion_PatientGenerator" main.py
```

**What those flags mean:**
| Flag | What it does |
|------|-------------|
| `--onefile` | Packages everything into a single .exe file |
| `--windowed` | No black terminal window behind the GUI |
| `--name "NoCompanion_PatientGenerator"` | Sets the .exe filename |

**This will take 1–3 minutes.** PyInstaller analyzes your entire project.

---

## STEP 6 — FIND YOUR EXECUTABLE

After the build completes:

```
patient_generator/
├── build/                          ← Temporary build files (can delete)
├── dist/
│   └── NoCompanion_PatientGenerator.exe   ← YOUR STANDALONE APP ✓
├── NoCompanion_PatientGenerator.spec      ← Build spec (keep for rebuilds)
└── ...
```

Your .exe is at:
```
patient_generator/dist/NoCompanion_PatientGenerator.exe
```

Double-click it — no Python installation needed on any machine you copy it to.

---

## REBUILDING AFTER CHANGES

If you edit any .py file, just re-run Step 5:

```bash
pyinstaller NoCompanion_PatientGenerator.spec
```

Using the .spec file is faster than re-running the full command.

Or force a clean rebuild:

```bash
pyinstaller --onefile --windowed --name "NoCompanion_PatientGenerator" --clean main.py
```

---

## TROUBLESHOOTING

### "ModuleNotFoundError: No module named 'data'" in the .exe
PyInstaller missed one of your modules. Run:
```bash
pyinstaller --onefile --windowed --name "NoCompanion_PatientGenerator" \
  --hidden-import=data \
  --hidden-import=generators \
  --hidden-import=cda_builder \
  main.py
```

### The window opens but immediately closes
Remove `--windowed` temporarily to see the error:
```bash
pyinstaller --onefile --name "NoCompanion_PatientGenerator_DEBUG" main.py
```
Then run `dist\NoCompanion_PatientGenerator_DEBUG.exe` from the terminal to see the error message.

### "python is not recognized as a command" (Windows)
Python is not on your PATH. Options:
- Re-run the Python installer and check "Add to PATH"
- Or use `py` instead of `python` in all commands above

### tkinter not found (Linux only)
```bash
sudo apt install python3-tk
```

### Antivirus quarantines the .exe
PyInstaller-built executables occasionally trigger false positives.
Add the `dist/` folder to your antivirus exclusions, then rebuild.

---

## OPTIONAL: ADD AN ICON

If you have a .ico file (Windows icon):
```bash
pyinstaller --onefile --windowed --icon=myicon.ico --name "NoCompanion_PatientGenerator" main.py
```

Free icon converters: https://convertio.co/png-ico/

---

## DISTRIBUTING THE APP

Copy just this one file to any Windows machine:
```
dist/NoCompanion_PatientGenerator.exe
```

No Python, no pip, no installation — just double-click and run.
All output XML files are saved to the folder you choose inside the app (default: Desktop/TestPatients/).

---

## QUICK REFERENCE — ALL COMMANDS IN ORDER

```bash
# One-time setup
python -m venv venv
venv\Scripts\activate
pip install pyinstaller

# Test before building
python main.py

# Build the exe
pyinstaller --onefile --windowed --name "NoCompanion_PatientGenerator" main.py

# Find your exe
cd dist
dir
```
