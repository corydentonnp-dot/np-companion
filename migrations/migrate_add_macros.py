"""
Migration: Create ahk_macros, dot_phrases, macro_steps, macro_variables tables
and seed 10 starter macros + 15 starter dot phrases.
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'carecompanion.db')

# ── Seed macros: (name, description, hotkey, script_content, category) ──
SEED_MACROS = [
    (
        'Navigate to Patient Chart',
        'Open patient chart: Alt+C then type MRN and Enter',
        '^!c',
        '; Navigate to patient chart\nSend, !c\nSleep, 500\nSend, %patient_mrn%\nSleep, 300\nSend, {Enter}',
        'navigation',
    ),
    (
        'Open Orders Tab',
        'Click the Orders tab in the chart toolbar',
        '',
        '; Open Orders tab\nSend, !o\nSleep, 300',
        'navigation',
    ),
    (
        'Open Labs Tab',
        'Click the Labs tab in the chart toolbar',
        '',
        '; Open Labs tab\nSend, !l\nSleep, 300',
        'navigation',
    ),
    (
        'Paste HPI Template',
        'Click HPI field and insert a template',
        '',
        '; Insert HPI template\nSend, {Tab}\nSleep, 200\nSendInput, Patient presents with {complaint}. Onset {duration} ago. {quality} in nature. Severity {severity}/10.',
        'template',
    ),
    (
        'Open Rx Pad',
        'Alt+R to open the prescription writer',
        '!r',
        '; Open Rx Pad\nSend, !r\nSleep, 500',
        'navigation',
    ),
    (
        'Sign and Close Note',
        'Ctrl+S to save, then click Sign button',
        '^!s',
        '; Sign and close\nSend, ^s\nSleep, 1000\nSend, {Enter}\nSleep, 500',
        'data_entry',
    ),
    (
        'Open Inbox',
        'Alt+I to open the inbox',
        '!i',
        '; Open Inbox\nSend, !i\nSleep, 500',
        'navigation',
    ),
    (
        'Print Current Page',
        'Ctrl+P then Enter to print',
        '',
        '; Print\nSend, ^p\nSleep, 1000\nSend, {Enter}',
        'data_entry',
    ),
    (
        'Quick Vitals Entry',
        'Tab through vitals fields with delays',
        '^!v',
        '; Quick vitals entry\n; Height\nSendInput, %height%\nSend, {Tab}\nSleep, 200\n; Weight\nSendInput, %weight%\nSend, {Tab}\nSleep, 200\n; BP Systolic\nSendInput, %bp_sys%\nSend, {Tab}\nSleep, 100\n; BP Diastolic\nSendInput, %bp_dia%\nSend, {Tab}\nSleep, 200\n; Pulse\nSendInput, %pulse%\nSend, {Tab}\nSleep, 200\n; Temp\nSendInput, %temp%\nSend, {Tab}',
        'data_entry',
    ),
    (
        'Toggle Encounter Lock',
        'Ctrl+L to toggle the encounter lock',
        '^l',
        '; Toggle encounter lock\nSend, ^l\nSleep, 300',
        'data_entry',
    ),
]

# ── Seed dot phrases: (abbreviation, expansion, category) ──
SEED_DOT_PHRASES = [
    # HPI
    ('.hpi',
     'Patient presents today with {chief_complaint}. Onset was {duration} ago. '
     'The symptoms are described as {quality}. Severity is rated {severity}/10. '
     'Associated symptoms include {associated_symptoms}. '
     'Aggravating factors: {aggravating}. Relieving factors: {relieving}.',
     'hpi'),
    ('.hpiwv',
     'Patient presents for annual wellness visit. No acute complaints at this time. '
     'Patient reports compliance with medications and has no new concerns. '
     'Review of systems is negative except as noted below.',
     'hpi'),
    ('.hpiflu',
     'Patient presents with {duration} history of fever, body aches, cough, and fatigue. '
     'Onset was acute. Max temperature {max_temp}. Associated nasal congestion and sore throat. '
     'No shortness of breath or chest pain. Flu contacts: {contacts}.',
     'hpi'),
    # Exam
    ('.pegen',
     'GENERAL: Well-appearing, in no acute distress.\n'
     'HEENT: Normocephalic, atraumatic. PERRLA. Oropharynx clear.\n'
     'NECK: Supple, no lymphadenopathy, no thyromegaly.\n'
     'LUNGS: Clear to auscultation bilaterally.\n'
     'HEART: Regular rate and rhythm, no murmurs.\n'
     'ABDOMEN: Soft, non-tender, non-distended, normal bowel sounds.\n'
     'EXTREMITIES: No edema, pulses intact.\n'
     'NEURO: Alert, oriented x3, CN II-XII intact.',
     'exam'),
    ('.pecardio',
     'HEART: Regular rate and rhythm. S1, S2 normal. No S3, S4. No murmurs, rubs, or gallops. '
     'PMI non-displaced. JVP not elevated.\n'
     'PERIPHERAL VASCULAR: Pulses 2+ bilaterally in radial, dorsalis pedis, and posterior tibial. '
     'No carotid bruits. No peripheral edema.',
     'exam'),
    ('.penormal',
     'CONSTITUTIONAL: Well-developed, well-nourished, in no acute distress.\n'
     'HEENT: Normocephalic. PERRLA. TMs clear. Oropharynx without erythema or exudate.\n'
     'NECK: Supple, full ROM, no lymphadenopathy.\n'
     'CV: RRR, no murmurs, rubs, or gallops.\n'
     'PULM: CTAB, no wheezes, rales, or rhonchi.\n'
     'GI: Soft, NT/ND, +BS, no organomegaly.\n'
     'MSK: Full ROM all extremities, no tenderness.\n'
     'SKIN: Warm, dry, no rashes or lesions.\n'
     'NEURO: A&Ox3, CN II-XII intact, strength 5/5 all extremities.\n'
     'PSYCH: Normal mood and affect, cooperative.',
     'exam'),
    # Plan
    ('.planfu',
     'PLAN:\n'
     '1. Continue current medications as prescribed.\n'
     '2. Follow up in {follow_up_weeks} weeks.\n'
     '3. Lab work to be obtained prior to next visit: {labs}.\n'
     '4. Return sooner if symptoms worsen.',
     'plan'),
    ('.planref',
     'PLAN:\n'
     '1. Refer to {specialty} for evaluation of {condition}.\n'
     '2. Referral sent to {provider_name} at {practice}.\n'
     '3. Patient to call for appointment within 2 weeks.\n'
     '4. Continue current management pending specialist input.',
     'plan'),
    ('.planlab',
     'PLAN:\n'
     '1. Order: {lab_orders}.\n'
     '2. Fasting required: {fasting_required}.\n'
     '3. Results will be reviewed and patient notified within 3-5 business days.\n'
     '4. Follow up to discuss results as needed.',
     'plan'),
    # Instructions
    ('.instdiet',
     'DIETARY INSTRUCTIONS:\n'
     '- Increase fiber intake to 25-30g daily\n'
     '- Limit sodium to less than 2000mg daily\n'
     '- Increase water intake to 64oz daily\n'
     '- Reduce processed food and added sugars\n'
     '- Eat 5+ servings of fruits and vegetables daily\n'
     '- Consider Mediterranean-style diet pattern',
     'instructions'),
    ('.instexercise',
     'EXERCISE INSTRUCTIONS:\n'
     '- Goal: 150 minutes moderate-intensity aerobic activity per week\n'
     '- Start with 10-15 minute walks, gradually increase duration\n'
     '- Include strength training 2 days per week\n'
     '- Warm up 5 minutes before and cool down 5 minutes after\n'
     '- Stop and seek medical attention if you experience chest pain, severe SOB, or dizziness',
     'instructions'),
    ('.instmedstart',
     'NEW MEDICATION INSTRUCTIONS:\n'
     'You have been started on {medication_name} {dose}.\n'
     '- Take {frequency} with {with_food}.\n'
     '- Common side effects may include: {side_effects}.\n'
     '- Contact our office if you experience: {warning_signs}.\n'
     '- Do not stop this medication without consulting your provider.\n'
     '- Your next follow-up is in {follow_up} to assess response.',
     'instructions'),
    # Letters
    ('.letref',
     'Dear Dr. {recipient},\n\n'
     'I am referring {patient_name} (DOB: {dob}) to your practice for evaluation of {condition}.\n\n'
     'Brief History: {brief_history}\n\n'
     'Current Medications: {medications}\n\n'
     'Please evaluate and advise on management recommendations. '
     'I have enclosed relevant records for your review.\n\n'
     'Thank you for your assistance in the care of this patient.\n\n'
     'Sincerely,\n{provider_name}, {credentials}',
     'letters'),
    ('.letwork',
     'To Whom It May Concern,\n\n'
     '{patient_name} has been under my care and was seen on {visit_date}.\n\n'
     'Due to their medical condition, the patient was unable to work from '
     '{start_date} to {end_date}.\n\n'
     'The patient is cleared to return to work on {return_date} with the following '
     'restrictions: {restrictions}.\n\n'
     'Please do not hesitate to contact our office with any questions.\n\n'
     'Sincerely,\n{provider_name}, {credentials}\nNPI: {npi}',
     'letters'),
    ('.letprior',
     'To: {insurance_company}\nRe: Prior Authorization Request\n'
     'Patient: {patient_name} (DOB: {dob})\n'
     'Member ID: {member_id}\n\n'
     'I am writing to request prior authorization for {medication_or_procedure}.\n\n'
     'Diagnosis: {diagnosis} ({icd10_code})\n\n'
     'Medical Necessity: {clinical_justification}\n\n'
     'The patient has previously tried and failed the following alternatives: '
     '{alternatives_tried}.\n\n'
     'Please approve this request at your earliest convenience. '
     'Contact our office at {phone} for clinical questions.\n\n'
     'Sincerely,\n{provider_name}, {credentials}\nNPI: {npi}',
     'letters'),
]


def _extract_placeholders(text):
    """Extract {placeholder} tokens from text, return JSON list."""
    import re
    import json
    tokens = re.findall(r'\{(\w+)\}', text)
    return json.dumps(sorted(set(tokens))) if tokens else '[]'


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ── ahk_macros ──
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ahk_macros'")
    if cur.fetchone():
        print('[ahk_macros] Table already exists — skipping.')
    else:
        cur.execute('''
            CREATE TABLE ahk_macros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT DEFAULT '',
                hotkey VARCHAR(50) DEFAULT '',
                script_content TEXT DEFAULT '',
                category VARCHAR(50) DEFAULT 'custom',
                is_active BOOLEAN NOT NULL DEFAULT 1,
                display_order INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        cur.execute('CREATE INDEX IF NOT EXISTS ix_ahk_macros_user_id ON ahk_macros (user_id)')
        cur.execute('CREATE INDEX IF NOT EXISTS ix_ahk_macros_category ON ahk_macros (category)')
        print('[ahk_macros] Table created.')

        # Seed macros (user_id = 1 for default user)
        for i, (name, desc, hotkey, script, cat) in enumerate(SEED_MACROS):
            cur.execute(
                'INSERT INTO ahk_macros (user_id, name, description, hotkey, script_content, category, display_order) '
                'VALUES (?, ?, ?, ?, ?, ?, ?)',
                (1, name, desc, hotkey, script, cat, i + 1),
            )
        print(f'[ahk_macros] Seeded {len(SEED_MACROS)} starter macros.')

    # ── dot_phrases ──
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dot_phrases'")
    if cur.fetchone():
        print('[dot_phrases] Table already exists — skipping.')
    else:
        cur.execute('''
            CREATE TABLE dot_phrases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                abbreviation VARCHAR(50) NOT NULL,
                expansion TEXT NOT NULL,
                category VARCHAR(50) DEFAULT 'custom',
                placeholders TEXT DEFAULT '[]',
                use_count INTEGER NOT NULL DEFAULT 0,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE (user_id, abbreviation)
            )
        ''')
        cur.execute('CREATE INDEX IF NOT EXISTS ix_dot_phrases_user_id ON dot_phrases (user_id)')
        cur.execute('CREATE INDEX IF NOT EXISTS ix_dot_phrases_category ON dot_phrases (category)')
        print('[dot_phrases] Table created.')

        # Seed dot phrases (user_id = 1)
        for abbrev, expansion, cat in SEED_DOT_PHRASES:
            placeholders = _extract_placeholders(expansion)
            cur.execute(
                'INSERT INTO dot_phrases (user_id, abbreviation, expansion, category, placeholders) '
                'VALUES (?, ?, ?, ?, ?)',
                (1, abbrev, expansion, cat, placeholders),
            )
        print(f'[dot_phrases] Seeded {len(SEED_DOT_PHRASES)} starter dot phrases.')

    # ── macro_steps ──
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='macro_steps'")
    if cur.fetchone():
        print('[macro_steps] Table already exists — skipping.')
    else:
        cur.execute('''
            CREATE TABLE macro_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                macro_id INTEGER NOT NULL,
                step_order INTEGER NOT NULL,
                action_type VARCHAR(30) NOT NULL,
                target_x INTEGER,
                target_y INTEGER,
                key_sequence VARCHAR(200),
                delay_ms INTEGER DEFAULT 100,
                window_title VARCHAR(200),
                comment VARCHAR(200),
                FOREIGN KEY (macro_id) REFERENCES ahk_macros (id) ON DELETE CASCADE
            )
        ''')
        cur.execute('CREATE INDEX IF NOT EXISTS ix_macro_steps_macro_id ON macro_steps (macro_id)')
        print('[macro_steps] Table created.')

    # ── macro_variables ──
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='macro_variables'")
    if cur.fetchone():
        print('[macro_variables] Table already exists — skipping.')
    else:
        cur.execute('''
            CREATE TABLE macro_variables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                macro_id INTEGER NOT NULL,
                var_name VARCHAR(50) NOT NULL,
                var_label VARCHAR(100) DEFAULT '',
                default_value VARCHAR(200) DEFAULT '',
                var_type VARCHAR(20) DEFAULT 'text',
                choices TEXT,
                FOREIGN KEY (macro_id) REFERENCES ahk_macros (id) ON DELETE CASCADE
            )
        ''')
        cur.execute('CREATE INDEX IF NOT EXISTS ix_macro_variables_macro_id ON macro_variables (macro_id)')
        print('[macro_variables] Table created.')

    conn.commit()
    conn.close()
    print('Migration complete.')


if __name__ == '__main__':
    migrate()
