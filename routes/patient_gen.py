"""
CareCompanion — Patient Generator Route
File: routes/patient_gen.py

Web interface for generating synthetic test patients with HL7 CDA XML output.
Wraps the standalone tools/patient_gen package for browser-based access.

All endpoints require @login_required. No PHI involved — purely synthetic data.
"""

import base64
import io
import re
import zipfile

from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required

from tools.patient_gen.generators import generate_patient
from tools.patient_gen.cda_builder import build_cda

patient_gen_bp = Blueprint('patient_gen', __name__)

VALID_COMPLEXITIES = {'Simple', 'Moderate', 'Complex'}
MAX_COUNT = 20
SAFE_FILENAME_RE = re.compile(r'^[\w\-. ]+\.xml$')


@patient_gen_bp.route('/patient-generator')
@login_required
def index():
    return render_template('patient_gen.html')


@patient_gen_bp.route('/api/patient-generator/generate', methods=['POST'])
@login_required
def generate():
    """Generate 1–20 synthetic patients and return JSON with base64 XML."""
    data = request.get_json(silent=True) or {}

    complexity = data.get('complexity', 'Moderate')
    if complexity not in VALID_COMPLEXITIES:
        return jsonify({'error': f'Invalid complexity. Must be one of: {", ".join(VALID_COMPLEXITIES)}'}), 400

    try:
        count = int(data.get('count', 1))
    except (TypeError, ValueError):
        return jsonify({'error': 'count must be an integer'}), 400
    count = max(1, min(count, MAX_COUNT))

    overrides = {}
    raw = data.get('overrides', {})
    if isinstance(raw, dict):
        # Only allow known safe string fields
        allowed = {
            'first_name', 'last_name', 'city', 'state',
            'language', 'religion',
        }
        for key in allowed:
            val = raw.get(key, '').strip()
            if val:
                overrides[key] = val

        # Sex: must be a valid tuple
        sex = raw.get('sex', '')
        if sex == 'M':
            overrides['sex_tuple'] = ('M', 'Male')
        elif sex == 'F':
            overrides['sex_tuple'] = ('F', 'Female')

        # Age range → pick a random age in range
        try:
            age_min = int(raw.get('age_min', 0))
            age_max = int(raw.get('age_max', 0))
            if 0 < age_min <= age_max <= 110:
                import random
                overrides['age'] = random.randint(age_min, age_max)
        except (TypeError, ValueError):
            pass

    results = []
    for _ in range(count):
        patient = generate_patient(overrides, complexity)
        xml_str = build_cda(patient)
        xml_b64 = base64.b64encode(xml_str.encode('utf-8')).decode('ascii')

        demo = patient['demo']
        dx_list = [p.get('display', p.get('description', '')) for p in patient.get('problems', [])[:5]]
        dx_summary = '; '.join(dx_list) if dx_list else 'None'

        results.append({
            'name': f"{demo['last']}, {demo['first']}",
            'mrn': demo['mrn'],
            'age': demo['age'],
            'sex': demo['sex_display'],
            'diagnoses_summary': dx_summary,
            'xml_b64': xml_b64,
            'filename': f"TestPatient_{demo['mrn']}_{demo['last']}.xml",
        })

    return jsonify({'patients': results})


@patient_gen_bp.route('/api/patient-generator/zip', methods=['POST'])
@login_required
def download_zip():
    """Build an in-memory ZIP of multiple patient XML files."""
    data = request.get_json(silent=True) or {}
    files = data.get('files', [])

    if not files or not isinstance(files, list):
        return jsonify({'error': 'No files provided'}), 400
    if len(files) > MAX_COUNT:
        return jsonify({'error': f'Maximum {MAX_COUNT} files per ZIP'}), 400

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for item in files:
            filename = item.get('filename', 'patient.xml')
            xml_b64 = item.get('xml_b64', '')

            # Sanitize filename
            if not SAFE_FILENAME_RE.match(filename):
                filename = 'patient.xml'

            try:
                xml_bytes = base64.b64decode(xml_b64)
            except Exception:
                continue

            zf.writestr(filename, xml_bytes)

    buf.seek(0)
    return send_file(
        buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name='test_patients.zip',
    )
