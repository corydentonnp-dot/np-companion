
### IMPLEMENT

Review running_plan.md. Identify the next unchecked step(s) that can be implemented together with a 99% chance of success. Implement them now — do not ask for permission to begin. After completing, update running_plan.md by checking off what was done, adding a brief note on outcome, and noting what comes next. Then stop and report what was completed until we finish what exists in the running plan. Once we reach the end of the running plan, update any necessary development files in C:\Users\coryd\Documents\CareCompanion\Documents\DevGuide and outline in the running plan what still remains to be developed.


### DEVELOP NEXT PLAN 

use this information and all of the development guide documents found at C:\Users\coryd\Documents\CareCompanion\Documents\DevGuide to plan the next phase of development. overwrite what currently exists in running_plan.md with the next lrage phase of development. Break it down into big bite sections that you can implement with 99% certianty.

### START PLAN AND UPDATE running_plan.md

Begin working on the plan outlined below. overwrite the running_plan.md file as appropriate. 

### APPEND PLAN

Append your plan with the information above/below. Build upon everything you just described in your last answer, and outline the coding logic and theory that should be used to get from where we are now to a full implementation of the described end-goal. 


###

Compacted conversation

Let me check the existing startup files to give you the exact commands.  

Read [](file:///c%3A/Users/coryd/Documents/CareCompanion/beta_launch.bat#1-1), lines 1 to 80

Read [](file:///c%3A/Users/coryd/Documents/CareCompanion/restart.bat#1-1), lines 1 to 30

Here are the step-by-step commands to run in PowerShell:

#### 1. Kill any existing Python/server processes
```powershell
taskkill /F /IM python.exe 2>$null
taskkill /F /IM pythonw.exe 2>$null
```

#### 2. Verify port 5000 is free
```powershell
netstat -ano | findstr ":5000"
```
If anything shows `LISTENING`, kill that PID:
```powershell
taskkill /F /PID <the_PID_number>
```

#### 3. Navigate to project and activate venv
```powershell
cd C:\Users\coryd\Documents\CareCompanion
.\venv\Scripts\Activate.ps1
```

#### 4. Start the Flask server
```powershell
python launcher.py --mode=server
```

That's it — the server will be running on `http://localhost:5000`. Open a browser to that URL (or launch the desktop exe from CareCompanion.exe separately).

**Or, the one-click option:** just double-click beta_launch.bat or restart.bat — they handle all of the above automatically.