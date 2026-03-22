Compacted conversation

Let me check the existing startup files to give you the exact commands.  

Read [](file:///c%3A/Users/coryd/Documents/NP_Companion/beta_launch.bat#1-1), lines 1 to 80

Read [](file:///c%3A/Users/coryd/Documents/NP_Companion/restart.bat#1-1), lines 1 to 30

Here are the step-by-step commands to run in PowerShell:

### 1. Kill any existing Python/server processes
```powershell
taskkill /F /IM python.exe 2>$null
taskkill /F /IM pythonw.exe 2>$null
```

### 2. Verify port 5000 is free
```powershell
netstat -ano | findstr ":5000"
```
If anything shows `LISTENING`, kill that PID:
```powershell
taskkill /F /PID <the_PID_number>
```

### 3. Navigate to project and activate venv
```powershell
cd C:\Users\coryd\Documents\NP_Companion
.\venv\Scripts\Activate.ps1
```

### 4. Start the Flask server
```powershell
python launcher.py --mode=server
```

That's it — the server will be running on `http://localhost:5000`. Open a browser to that URL (or launch the desktop exe from NP_Companion.exe separately).

**Or, the one-click option:** just double-click beta_launch.bat or restart.bat — they handle all of the above automatically.