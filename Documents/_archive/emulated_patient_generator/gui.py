"""
gui.py — Tkinter GUI for the No Companion patient generator.
Collects optional demographic overrides, then calls generators + cda_builder.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
from datetime import date

# ---------------------------------------------------------------------------
# Import our modules (handle both frozen .exe and dev mode)
# ---------------------------------------------------------------------------
try:
    from data import (
        RELIGIONS, LANGUAGES, GENERATIONAL_SUFFIXES,
        FIRST_NAMES_MALE, FIRST_NAMES_FEMALE, LAST_NAMES,
        CITIES_STATES, BIOLOGICAL_SEX,
    )
    from generators import generate_patient
    from cda_builder import build_cda
except ModuleNotFoundError:
    # If running as packaged exe, adjust path
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, base)
    from data import (
        RELIGIONS, LANGUAGES, GENERATIONAL_SUFFIXES,
        FIRST_NAMES_MALE, FIRST_NAMES_FEMALE, LAST_NAMES,
        CITIES_STATES, BIOLOGICAL_SEX,
    )
    from generators import generate_patient
    from cda_builder import build_cda


# ---------------------------------------------------------------------------
# COLORS / THEME
# ---------------------------------------------------------------------------
BG = "#1e2532"
PANEL = "#252d3d"
CARD = "#2c3650"
ACCENT = "#4a9eff"
ACCENT2 = "#2ecc71"
TEXT = "#e8eaf0"
MUTED = "#8892a4"
RED = "#e74c3c"
YELLOW = "#f39c12"
INPUT_BG = "#1a2035"
INPUT_FG = "#e8eaf0"
BORDER = "#3d4b6b"
FONT_BODY = ("Segoe UI", 10)
FONT_LABEL = ("Segoe UI", 9)
FONT_TITLE = ("Segoe UI Semibold", 11)
FONT_H1 = ("Segoe UI", 14, "bold")
FONT_SMALL = ("Segoe UI", 8)
FONT_MONO = ("Consolas", 9)


def style_entry(e):
    e.configure(
        bg=INPUT_BG, fg=INPUT_FG, insertbackground=ACCENT,
        relief="flat", highlightthickness=1,
        highlightcolor=ACCENT, highlightbackground=BORDER,
        font=FONT_BODY,
    )


def style_combo(c):
    # ttk comboboxes are styled via ttk.Style
    c.configure(font=FONT_BODY)


# ---------------------------------------------------------------------------
# FIELD BUILDER HELPERS
# ---------------------------------------------------------------------------
def labeled_entry(parent, label, row, col=0, width=22, default=""):
    tk.Label(parent, text=label, bg=PANEL, fg=MUTED, font=FONT_LABEL,
             anchor="w").grid(row=row, column=col, sticky="w", padx=(8, 4), pady=2)
    var = tk.StringVar(value=default)
    e = tk.Entry(parent, textvariable=var, width=width)
    style_entry(e)
    e.grid(row=row, column=col + 1, sticky="ew", padx=(0, 8), pady=2)
    return var


def labeled_combo(parent, label, row, values, col=0, width=22, default=None):
    tk.Label(parent, text=label, bg=PANEL, fg=MUTED, font=FONT_LABEL,
             anchor="w").grid(row=row, column=col, sticky="w", padx=(8, 4), pady=2)
    var = tk.StringVar(value=default or (values[0] if values else ""))
    c = ttk.Combobox(parent, textvariable=var, values=values, width=width, state="readonly")
    c.grid(row=row, column=col + 1, sticky="ew", padx=(0, 8), pady=2)
    return var


# ---------------------------------------------------------------------------
# MAIN APP WINDOW
# ---------------------------------------------------------------------------
class PatientGeneratorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("No Companion — Patient CDA Generator")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(900, 700)
        self._apply_style()
        self._build_ui()
        self._center_window(1050, 780)

    def _center_window(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _apply_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TCombobox",
                     fieldbackground=INPUT_BG, background=INPUT_BG,
                     foreground=INPUT_FG, bordercolor=BORDER,
                     arrowcolor=ACCENT, selectbackground=CARD,
                     selectforeground=TEXT)
        s.map("TCombobox", fieldbackground=[("readonly", INPUT_BG)])
        s.configure("TNotebook", background=BG, tabmargins=[0, 0, 0, 0])
        s.configure("TNotebook.Tab", background=CARD, foreground=MUTED,
                     font=FONT_LABEL, padding=[14, 6])
        s.map("TNotebook.Tab",
               background=[("selected", PANEL)], foreground=[("selected", TEXT)])
        s.configure("Vertical.TScrollbar", background=CARD, troughcolor=BG,
                     bordercolor=BORDER, arrowcolor=MUTED)

    # ---- TOP HEADER ----
    def _build_ui(self):
        header = tk.Frame(self, bg=ACCENT, height=3)
        header.pack(fill="x")

        title_bar = tk.Frame(self, bg=PANEL, pady=12)
        title_bar.pack(fill="x")
        tk.Label(title_bar, text="⚕ No Companion", font=FONT_H1,
                 bg=PANEL, fg=TEXT).pack(side="left", padx=18)
        tk.Label(title_bar, text="CDA XML Patient Generator  |  TEST DATA ONLY — NO REAL PHI",
                 font=FONT_SMALL, bg=PANEL, fg=MUTED).pack(side="left", padx=4)

        # Main pane
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=16, pady=12)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=1)

        # Left — form
        left = tk.Frame(main, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        nb = ttk.Notebook(left)
        nb.grid(row=0, column=0, sticky="nsew")

        tab_demo = tk.Frame(nb, bg=PANEL)
        tab_clinical = tk.Frame(nb, bg=PANEL)
        tab_output = tk.Frame(nb, bg=PANEL)
        nb.add(tab_demo, text="  Demographics  ")
        nb.add(tab_clinical, text="  Clinical Options  ")
        nb.add(tab_output, text="  Output  ")

        self._build_demo_tab(tab_demo)
        self._build_clinical_tab(tab_clinical)
        self._build_output_tab(tab_output)

        # Right — log + actions
        right = tk.Frame(main, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        self._build_action_panel(right)
        self._build_log(right)

    # ----------------------------------------------------------------
    # DEMOGRAPHICS TAB
    # ----------------------------------------------------------------
    def _build_demo_tab(self, parent):
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(3, weight=1)

        # Section header
        tk.Label(parent, text="Patient Identity", bg=PANEL, fg=ACCENT,
                 font=FONT_TITLE).grid(row=0, column=0, columnspan=4,
                                        sticky="w", padx=8, pady=(10, 4))

        # Name fields
        self.v_first = labeled_entry(parent, "First Name", 1, 0, 18)
        self.v_last = labeled_entry(parent, "Last Name", 1, 2, 18)
        self.v_middle = labeled_entry(parent, "Middle Initial", 2, 0, 10)

        suffix_vals = ["(none)"] + GENERATIONAL_SUFFIXES
        self.v_suffix = labeled_combo(parent, "Name Suffix", 2, suffix_vals, 2, 14)

        self.v_mrn = labeled_entry(parent, "MRN (T#####)", 3, 0, 18,
                                   default="(auto-generate)")
        self.v_dob = labeled_entry(parent, "Date of Birth", 3, 2, 18,
                                   default="YYYY-MM-DD or leave blank")

        # If DOB blank, use age
        self.v_age = labeled_entry(parent, "Age (if no DOB)", 4, 0, 10)

        sex_vals = [f"{code} — {disp}" for code, disp in BIOLOGICAL_SEX]
        sex_vals.insert(0, "(random)")
        self.v_sex = labeled_combo(parent, "Biological Sex", 4, sex_vals, 2, 18)

        tk.Label(parent, text="Contact / Address", bg=PANEL, fg=ACCENT,
                 font=FONT_TITLE).grid(row=5, column=0, columnspan=4,
                                        sticky="w", padx=8, pady=(12, 4))

        self.v_address = labeled_entry(parent, "Street Address", 6, 0, 28)
        self.v_city = labeled_entry(parent, "City", 7, 0, 18)
        self.v_state = labeled_entry(parent, "State", 7, 2, 8)
        self.v_zip = labeled_entry(parent, "ZIP Code", 8, 0, 10)
        self.v_home_phone = labeled_entry(parent, "Home Phone", 8, 2, 16,
                                          default="(auto)")
        self.v_cell_phone = labeled_entry(parent, "Cell Phone", 9, 0, 16,
                                          default="(auto)")

        tk.Label(parent, text="Cultural / Social", bg=PANEL, fg=ACCENT,
                 font=FONT_TITLE).grid(row=10, column=0, columnspan=4,
                                        sticky="w", padx=8, pady=(12, 4))

        lang_vals = ["(random)"] + list(LANGUAGES.keys())
        self.v_lang = labeled_combo(parent, "Language", 11, lang_vals, 0, 22)

        rel_vals = ["(random)"] + RELIGIONS
        self.v_religion = labeled_combo(parent, "Religion", 12, rel_vals, 0, 30)

        marital_opts = ["(random)", "Single", "Married", "Divorced",
                        "Widowed", "Separated", "Common Law", "Unknown"]
        self.v_marital = labeled_combo(parent, "Marital Status", 13, marital_opts, 0, 22)

    # ----------------------------------------------------------------
    # CLINICAL OPTIONS TAB
    # ----------------------------------------------------------------
    def _build_clinical_tab(self, parent):
        parent.columnconfigure(1, weight=1)

        tk.Label(parent, text="Chart Complexity", bg=PANEL, fg=ACCENT,
                 font=FONT_TITLE).grid(row=0, column=0, columnspan=2,
                                        sticky="w", padx=8, pady=(10, 4))

        self.v_complexity = tk.StringVar(value="Moderate")
        comp_frame = tk.Frame(parent, bg=PANEL)
        comp_frame.grid(row=1, column=0, columnspan=2, sticky="w", padx=8, pady=4)
        for val, desc, color in [
            ("Simple", "1–3 Dx  |  0–3 Meds  |  1–2 Lab panels", ACCENT2),
            ("Moderate", "3–7 Dx  |  3–8 Meds  |  3–5 Lab panels", YELLOW),
            ("Complex", "7–18 Dx  |  8–20 Meds  |  5–12 Lab panels", RED),
        ]:
            row_f = tk.Frame(comp_frame, bg=PANEL)
            row_f.pack(anchor="w", pady=2)
            rb = tk.Radiobutton(row_f, text=val, variable=self.v_complexity,
                                value=val, bg=PANEL, fg=color,
                                selectcolor=BG, activebackground=PANEL,
                                font=("Segoe UI Semibold", 10))
            rb.pack(side="left")
            tk.Label(row_f, text=f"  {desc}", bg=PANEL, fg=MUTED,
                     font=FONT_SMALL).pack(side="left")

        tk.Label(parent, text="Batch Generation", bg=PANEL, fg=ACCENT,
                 font=FONT_TITLE).grid(row=2, column=0, columnspan=2,
                                        sticky="w", padx=8, pady=(16, 4))

        tk.Label(parent, text="Number of patients to generate:", bg=PANEL, fg=MUTED,
                 font=FONT_LABEL).grid(row=3, column=0, sticky="w", padx=8, pady=2)
        self.v_batch = tk.IntVar(value=1)
        spin = tk.Spinbox(parent, from_=1, to=500, textvariable=self.v_batch,
                          width=6, bg=INPUT_BG, fg=INPUT_FG, insertbackground=ACCENT,
                          buttonbackground=CARD, relief="flat",
                          highlightthickness=1, highlightbackground=BORDER,
                          font=FONT_BODY)
        spin.grid(row=3, column=1, sticky="w", padx=8, pady=2)

        tk.Label(parent,
                 text="When batch > 1, demographic overrides from the Demographics tab\n"
                      "are ignored — all fields are fully randomized.",
                 bg=PANEL, fg=MUTED, font=FONT_SMALL, justify="left"
                 ).grid(row=4, column=0, columnspan=2, sticky="w", padx=8, pady=(2, 12))

        tk.Label(parent, text="Age Range (batch mode)", bg=PANEL, fg=ACCENT,
                 font=FONT_TITLE).grid(row=5, column=0, columnspan=2,
                                        sticky="w", padx=8, pady=(4, 4))

        age_frame = tk.Frame(parent, bg=PANEL)
        age_frame.grid(row=6, column=0, columnspan=2, sticky="w", padx=8, pady=2)
        tk.Label(age_frame, text="Min age:", bg=PANEL, fg=MUTED,
                 font=FONT_LABEL).pack(side="left")
        self.v_age_min = tk.IntVar(value=0)
        tk.Spinbox(age_frame, from_=0, to=100, textvariable=self.v_age_min,
                   width=5, bg=INPUT_BG, fg=INPUT_FG, buttonbackground=CARD,
                   relief="flat", font=FONT_BODY).pack(side="left", padx=4)
        tk.Label(age_frame, text="Max age:", bg=PANEL, fg=MUTED,
                 font=FONT_LABEL).pack(side="left", padx=(12, 0))
        self.v_age_max = tk.IntVar(value=101)
        tk.Spinbox(age_frame, from_=0, to=101, textvariable=self.v_age_max,
                   width=5, bg=INPUT_BG, fg=INPUT_FG, buttonbackground=CARD,
                   relief="flat", font=FONT_BODY).pack(side="left", padx=4)

        tk.Label(parent, text="Sex Distribution (batch mode)", bg=PANEL, fg=ACCENT,
                 font=FONT_TITLE).grid(row=7, column=0, columnspan=2,
                                        sticky="w", padx=8, pady=(16, 4))
        self.v_sex_dist = tk.StringVar(value="Random mix")
        for val in ["Random mix", "All Male", "All Female"]:
            tk.Radiobutton(parent, text=val, variable=self.v_sex_dist, value=val,
                           bg=PANEL, fg=TEXT, selectcolor=BG,
                           activebackground=PANEL, font=FONT_BODY).grid(
                sticky="w", padx=16, pady=1,
                row=8 + ["Random mix", "All Male", "All Female"].index(val),
                column=0, columnspan=2)

    # ----------------------------------------------------------------
    # OUTPUT TAB
    # ----------------------------------------------------------------
    def _build_output_tab(self, parent):
        parent.columnconfigure(1, weight=1)

        tk.Label(parent, text="Output Directory", bg=PANEL, fg=ACCENT,
                 font=FONT_TITLE).grid(row=0, column=0, columnspan=3,
                                        sticky="w", padx=8, pady=(10, 4))

        self.v_outdir = tk.StringVar(value=os.path.join(os.path.expanduser("~"),
                                                         "Desktop", "TestPatients"))
        e = tk.Entry(parent, textvariable=self.v_outdir, width=36)
        style_entry(e)
        e.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(8, 4), pady=2)
        tk.Button(parent, text="Browse…", command=self._browse_dir,
                  bg=CARD, fg=TEXT, relief="flat", font=FONT_LABEL,
                  activebackground=BORDER, cursor="hand2").grid(
            row=1, column=2, sticky="w", padx=4, pady=2)

        tk.Label(parent, text="File Naming", bg=PANEL, fg=ACCENT,
                 font=FONT_TITLE).grid(row=2, column=0, columnspan=3,
                                        sticky="w", padx=8, pady=(14, 4))

        tk.Label(parent, text="Files are named: {MRN}_{LastName}_{FirstName}.xml",
                 bg=PANEL, fg=MUTED, font=FONT_SMALL).grid(
            row=3, column=0, columnspan=3, sticky="w", padx=8)

        tk.Label(parent, text="XML Preview (most recently generated patient)",
                 bg=PANEL, fg=ACCENT, font=FONT_TITLE).grid(
            row=4, column=0, columnspan=3, sticky="w", padx=8, pady=(16, 4))

        self.preview_text = scrolledtext.ScrolledText(
            parent, width=60, height=18, bg=INPUT_BG, fg=INPUT_FG,
            font=FONT_MONO, relief="flat",
            highlightthickness=1, highlightbackground=BORDER,
            insertbackground=ACCENT, wrap="none",
        )
        self.preview_text.grid(row=5, column=0, columnspan=3,
                                sticky="nsew", padx=8, pady=4)
        parent.rowconfigure(5, weight=1)

    # ----------------------------------------------------------------
    # ACTION PANEL
    # ----------------------------------------------------------------
    def _build_action_panel(self, parent):
        panel = tk.Frame(parent, bg=PANEL, padx=12, pady=12)
        panel.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        panel.columnconfigure(0, weight=1)

        tk.Label(panel, text="Generate", bg=PANEL, fg=TEXT,
                 font=FONT_TITLE).pack(anchor="w")
        tk.Label(panel,
                 text="Fill in demographics above (all fields optional).\n"
                      "Blank fields are randomized.",
                 bg=PANEL, fg=MUTED, font=FONT_SMALL, justify="left").pack(anchor="w", pady=(2, 8))

        self.btn_generate = tk.Button(
            panel, text="⚕  GENERATE PATIENT(S)",
            command=self._start_generate,
            bg=ACCENT, fg="white", font=("Segoe UI Semibold", 11),
            relief="flat", pady=8, cursor="hand2",
            activebackground="#3a8eef", activeforeground="white"
        )
        self.btn_generate.pack(fill="x", pady=(0, 6))

        btn_clear = tk.Button(
            panel, text="✕  Clear Form",
            command=self._clear_form,
            bg=CARD, fg=MUTED, font=FONT_LABEL,
            relief="flat", pady=5, cursor="hand2",
        )
        btn_clear.pack(fill="x", pady=(0, 4))

        btn_open = tk.Button(
            panel, text="📁  Open Output Folder",
            command=self._open_output_folder,
            bg=CARD, fg=MUTED, font=FONT_LABEL,
            relief="flat", pady=5, cursor="hand2",
        )
        btn_open.pack(fill="x")

        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(panel, variable=self.progress_var,
                                         maximum=100, length=200)
        self.progress.pack(fill="x", pady=(10, 0))
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(panel, textvariable=self.status_var, bg=PANEL, fg=MUTED,
                 font=FONT_SMALL).pack(anchor="w", pady=(2, 0))

    # ----------------------------------------------------------------
    # LOG PANEL
    # ----------------------------------------------------------------
    def _build_log(self, parent):
        log_frame = tk.Frame(parent, bg=PANEL, padx=8, pady=8)
        log_frame.grid(row=1, column=0, sticky="nsew")
        parent.rowconfigure(1, weight=1)
        log_frame.rowconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)

        tk.Label(log_frame, text="Activity Log", bg=PANEL, fg=ACCENT,
                 font=FONT_TITLE).grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.log_box = scrolledtext.ScrolledText(
            log_frame, height=10, bg=INPUT_BG, fg=TEXT,
            font=FONT_MONO, relief="flat",
            highlightthickness=1, highlightbackground=BORDER,
            insertbackground=ACCENT, state="disabled",
        )
        self.log_box.grid(row=1, column=0, sticky="nsew")

        # Tags for colored log lines
        self.log_box.tag_config("ok", foreground=ACCENT2)
        self.log_box.tag_config("error", foreground=RED)
        self.log_box.tag_config("info", foreground=ACCENT)
        self.log_box.tag_config("warn", foreground=YELLOW)

    # ----------------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------------
    def _log(self, msg, tag=""):
        self.log_box.configure(state="normal")
        ts = date.today().strftime("%m/%d")
        self.log_box.insert("end", f"[{ts}] {msg}\n", tag)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _browse_dir(self):
        d = filedialog.askdirectory(title="Select output directory")
        if d:
            self.v_outdir.set(d)

    def _open_output_folder(self):
        folder = self.v_outdir.get()
        if os.path.isdir(folder):
            os.startfile(folder) if sys.platform == "win32" else \
                os.system(f'open "{folder}"' if sys.platform == "darwin"
                          else f'xdg-open "{folder}"')
        else:
            messagebox.showwarning("Not found", "Output directory does not exist yet.")

    def _clear_form(self):
        for var in [self.v_first, self.v_last, self.v_middle, self.v_address,
                    self.v_city, self.v_state, self.v_zip, self.v_age, self.v_mrn]:
            var.set("")
        self.v_home_phone.set("(auto)")
        self.v_cell_phone.set("(auto)")
        self.v_dob.set("YYYY-MM-DD or leave blank")
        self.v_sex.set("(random)")
        self.v_lang.set("(random)")
        self.v_religion.set("(random)")
        self.v_marital.set("(random)")
        self.v_suffix.set("(none)")
        self._log("Form cleared.", "info")

    def _build_overrides(self):
        """Convert GUI field values into the overrides dict for generate_patient."""
        ov = {}

        def get(v): return v.get().strip()

        if get(self.v_first):
            ov["first_name"] = get(self.v_first)
        if get(self.v_last):
            ov["last_name"] = get(self.v_last)
        if get(self.v_suffix) not in ("(none)", ""):
            ov["name_suffix"] = get(self.v_suffix)
        mrn_val = get(self.v_mrn)
        if mrn_val and mrn_val != "(auto-generate)":
            ov["mrn"] = mrn_val
        dob_val = get(self.v_dob)
        if dob_val and dob_val not in ("YYYY-MM-DD or leave blank", ""):
            try:
                from datetime import datetime
                ov["dob"] = datetime.strptime(dob_val, "%Y-%m-%d").date()
            except ValueError:
                pass
        age_val = get(self.v_age)
        if age_val and "dob" not in ov:
            try:
                ov["age"] = int(age_val)
            except ValueError:
                pass
        sex_val = get(self.v_sex)
        if sex_val != "(random)":
            code = sex_val.split(" — ")[0].strip()
            disp = sex_val.split(" — ")[1].strip() if " — " in sex_val else code
            ov["sex_tuple"] = (code, disp)
        if get(self.v_address):
            ov["address"] = get(self.v_address)
        if get(self.v_city):
            ov["city"] = get(self.v_city)
        if get(self.v_state):
            ov["state"] = get(self.v_state)
        if get(self.v_zip):
            ov["zip"] = get(self.v_zip)
        home = get(self.v_home_phone)
        if home and home != "(auto)":
            ov["home_phone"] = home if home.startswith("tel:") else f"tel:+1{home}"
        cell = get(self.v_cell_phone)
        if cell and cell != "(auto)":
            ov["cell_phone"] = cell if cell.startswith("tel:") else f"tel:+1{cell}"
        lang_val = get(self.v_lang)
        if lang_val != "(random)":
            ov["language"] = lang_val
        return ov

    # ----------------------------------------------------------------
    # GENERATION
    # ----------------------------------------------------------------
    def _start_generate(self):
        self.btn_generate.configure(state="disabled")
        self.progress_var.set(0)
        t = threading.Thread(target=self._run_generation, daemon=True)
        t.start()

    def _run_generation(self):
        import traceback
        try:
            batch = self.v_batch.get()
            complexity = self.v_complexity.get()
            out_dir = self.v_outdir.get().strip()
            os.makedirs(out_dir, exist_ok=True)

            age_min = self.v_age_min.get()
            age_max = self.v_age_max.get()
            sex_dist = self.v_sex_dist.get()

            self._log(f"Starting generation — {batch} patient(s), {complexity} complexity...", "info")
            self.status_var.set(f"Generating 0/{batch}...")

            last_xml = None
            errors = 0

            for i in range(1, batch + 1):
                try:
                    if batch == 1:
                        overrides = self._build_overrides()
                    else:
                        # Batch mode — full random with age/sex constraints
                        import random
                        overrides = {}
                        target_age = random.randint(age_min, age_max)
                        overrides["age"] = target_age
                        if sex_dist == "All Male":
                            overrides["sex_tuple"] = ("M", "Male")
                        elif sex_dist == "All Female":
                            overrides["sex_tuple"] = ("F", "Female")

                    patient = generate_patient(overrides=overrides, complexity=complexity)
                    xml_str = build_cda(patient)

                    demo = patient["demo"]
                    mrn = demo["mrn"]
                    last_name = demo["last"]
                    first_name = demo["first"]
                    fname = f"{mrn}_{last_name}_{first_name}.xml"
                    fpath = os.path.join(out_dir, fname)
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(xml_str)

                    last_xml = xml_str
                    self._log(
                        f"✓ [{i}/{batch}] {demo['first']} {demo['last']} "
                        f"(MRN: {mrn}) — Age {demo['age']}, "
                        f"{demo.get('sex_display', demo['sex_code'])} — {fname}",
                        "ok"
                    )
                except Exception as e:
                    self._log(f"✗ Error on patient {i}: {e}", "error")
                    errors += 1

                pct = (i / batch) * 100
                self.progress_var.set(pct)
                self.status_var.set(f"Generated {i}/{batch}...")

            # Update preview with last generated XML
            if last_xml:
                self.preview_text.delete("1.0", "end")
                self.preview_text.insert("1.0", last_xml[:8000])
                if len(last_xml) > 8000:
                    self.preview_text.insert("end", "\n\n... [truncated for preview — full file saved] ...")

            done_msg = f"Done — {batch - errors}/{batch} patients generated to:\n{out_dir}"
            if errors:
                self._log(f"⚠ Completed with {errors} error(s). Check log above.", "warn")
            else:
                self._log(done_msg, "ok")

            self.status_var.set(f"✓ Done — {batch - errors}/{batch} files saved")
            self.progress_var.set(100)
            if errors == 0:
                messagebox.showinfo("Generation complete",
                                    f"{batch} patient(s) saved to:\n{out_dir}")
            else:
                messagebox.showwarning("Completed with errors",
                                       f"{batch - errors}/{batch} succeeded.\n{errors} failed — see log.")

        except Exception as e:
            self._log(f"✗ Fatal error: {traceback.format_exc()}", "error")
            self.status_var.set("Error — see log")
            messagebox.showerror("Error", str(e))
        finally:
            self.btn_generate.configure(state="normal")


# ---------------------------------------------------------------------------
def launch():
    app = PatientGeneratorApp()
    app.mainloop()


if __name__ == "__main__":
    launch()
