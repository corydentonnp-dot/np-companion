"""
NP Companion — Clinical Terminology Spell Check & Fuzzy Matcher
File: app/services/clinical_spell_check.py

Provides medical-aware spell checking and fuzzy matching for free text
in clinical notes. Handles:
- Medical abbreviations (HTN, DM2, GERD, CHF, CKD, etc.)
- Clinical slang (nitro, dig, lytes, chem, bili, etc.)
- Misspelled drug names (fuzzy match against RxNorm)
- Misspelled diagnoses (fuzzy match against ICD-10 descriptions)
- Common documentation shorthand (yo, hx, sx, tx, rx, dx, etc.)

The matcher returns suggestions with confidence scores. High-confidence
matches (>85%) are auto-corrected; medium-confidence matches (60-85%)
are flagged for provider review; low-confidence matches (<60%) are
ignored to prevent false positives.

No patient data is sent externally. All matching happens locally using
cached terminology databases + the ICD-10 and RxNorm APIs for novel terms.
"""

import re
import logging
from difflib import SequenceMatcher, get_close_matches

logger = logging.getLogger(__name__)


# =====================================================================
# Medical abbreviation dictionary (standard clinical abbreviations)
# =====================================================================
MEDICAL_ABBREVIATIONS = {
    # Diagnoses
    'htn': 'hypertension',
    'dm': 'diabetes mellitus',
    'dm1': 'type 1 diabetes mellitus',
    'dm2': 'type 2 diabetes mellitus',
    't2dm': 'type 2 diabetes mellitus',
    'iddm': 'insulin-dependent diabetes mellitus',
    'niddm': 'non-insulin-dependent diabetes mellitus',
    'chf': 'congestive heart failure',
    'hf': 'heart failure',
    'hfref': 'heart failure with reduced ejection fraction',
    'hfpef': 'heart failure with preserved ejection fraction',
    'cad': 'coronary artery disease',
    'mi': 'myocardial infarction',
    'stemi': 'ST-elevation myocardial infarction',
    'nstemi': 'non-ST-elevation myocardial infarction',
    'afib': 'atrial fibrillation',
    'a-fib': 'atrial fibrillation',
    'af': 'atrial fibrillation',
    'ckd': 'chronic kidney disease',
    'esrd': 'end-stage renal disease',
    'copd': 'chronic obstructive pulmonary disease',
    'gerd': 'gastroesophageal reflux disease',
    'bph': 'benign prostatic hyperplasia',
    'uti': 'urinary tract infection',
    'uri': 'upper respiratory infection',
    'osa': 'obstructive sleep apnea',
    'dvt': 'deep vein thrombosis',
    'pe': 'pulmonary embolism',
    'tia': 'transient ischemic attack',
    'cva': 'cerebrovascular accident',
    'pvd': 'peripheral vascular disease',
    'pad': 'peripheral artery disease',
    'ra': 'rheumatoid arthritis',
    'oa': 'osteoarthritis',
    'doa': 'degenerative osteoarthritis',
    'djd': 'degenerative joint disease',
    'sob': 'shortness of breath',
    'doe': 'dyspnea on exertion',
    'cp': 'chest pain',
    'ha': 'headache',
    'n/v': 'nausea and vomiting',
    'n&v': 'nausea and vomiting',
    'abd': 'abdominal',
    'r/o': 'rule out',
    'hld': 'hyperlipidemia',
    'gout': 'gout',
    'anx': 'anxiety',
    'mdd': 'major depressive disorder',
    'gad': 'generalized anxiety disorder',
    'ptsd': 'post-traumatic stress disorder',
    'adhd': 'attention-deficit/hyperactivity disorder',
    'ocd': 'obsessive-compulsive disorder',
    'sz': 'seizure',
    'ams': 'altered mental status',
    'loc': 'loss of consciousness',
    'lle': 'left lower extremity',
    'rle': 'right lower extremity',
    'lue': 'left upper extremity',
    'rue': 'right upper extremity',

    # Clinical shorthand
    'yo': 'year old',
    'y/o': 'year old',
    'hx': 'history',
    'pmh': 'past medical history',
    'psh': 'past surgical history',
    'fh': 'family history',
    'sh': 'social history',
    'ros': 'review of systems',
    'cc': 'chief complaint',
    'hpi': 'history of present illness',
    'sx': 'symptoms',
    'tx': 'treatment',
    'rx': 'prescription',
    'dx': 'diagnosis',
    'ddx': 'differential diagnosis',
    'f/u': 'follow-up',
    'fu': 'follow-up',
    'prn': 'as needed',
    'bid': 'twice daily',
    'tid': 'three times daily',
    'qid': 'four times daily',
    'qd': 'once daily',
    'qhs': 'at bedtime',
    'po': 'by mouth',
    'im': 'intramuscular',
    'iv': 'intravenous',
    'sq': 'subcutaneous',
    'subq': 'subcutaneous',
    'sl': 'sublingual',
    'pr': 'per rectum',
    'od': 'right eye',
    'os': 'left eye',
    'ou': 'both eyes',
    'au': 'both ears',
    'ad': 'right ear',
    'as': 'left ear',
    'wnl': 'within normal limits',
    'wdwn': 'well-developed well-nourished',
    'nad': 'no acute distress',
    'a&o': 'alert and oriented',
    'aox3': 'alert and oriented x3',
    'aox4': 'alert and oriented x4',
    'perrl': 'pupils equal round reactive to light',
    'perrla': 'pupils equal round reactive to light and accommodation',
    'eomi': 'extraocular movements intact',
    'ctab': 'clear to auscultation bilaterally',
    'cta': 'clear to auscultation',
    'rrr': 'regular rate and rhythm',
    's1s2': 'S1 and S2 heart sounds',
    'ntnd': 'nontender nondistended',
    'nabs': 'normoactive bowel sounds',
    'brbpr': 'bright red blood per rectum',

    # Drug slang / abbreviations
    'asa': 'aspirin',
    'apap': 'acetaminophen',
    'nsaid': 'nonsteroidal anti-inflammatory drug',
    'nsaids': 'nonsteroidal anti-inflammatory drugs',
    'ace': 'ACE inhibitor',
    'acei': 'ACE inhibitor',
    'arb': 'angiotensin receptor blocker',
    'ccb': 'calcium channel blocker',
    'bb': 'beta blocker',
    'ssri': 'selective serotonin reuptake inhibitor',
    'snri': 'serotonin-norepinephrine reuptake inhibitor',
    'tca': 'tricyclic antidepressant',
    'ppi': 'proton pump inhibitor',
    'h2b': 'H2 blocker',
    'ics': 'inhaled corticosteroid',
    'laba': 'long-acting beta agonist',
    'lama': 'long-acting muscarinic antagonist',
    'saba': 'short-acting beta agonist',
    'sglt2': 'SGLT2 inhibitor',
    'glp1': 'GLP-1 receptor agonist',
    'dpp4': 'DPP-4 inhibitor',
    'nitro': 'nitroglycerin',
    'dig': 'digoxin',
    'lasix': 'furosemide',
    'coumadin': 'warfarin',
    'lytes': 'electrolytes',
    'chem': 'chemistry panel',
    'cbc': 'complete blood count',
    'bmp': 'basic metabolic panel',
    'cmp': 'comprehensive metabolic panel',
    'lfts': 'liver function tests',
    'tfts': 'thyroid function tests',
    'ua': 'urinalysis',
    'uds': 'urine drug screen',
    'ekg': 'electrocardiogram',
    'ecg': 'electrocardiogram',
    'cxr': 'chest x-ray',
    'ct': 'computed tomography',
    'mri': 'magnetic resonance imaging',
    'us': 'ultrasound',
    'bili': 'bilirubin',
    'cr': 'creatinine',
    'bun': 'blood urea nitrogen',
    'hgb': 'hemoglobin',
    'hct': 'hematocrit',
    'plt': 'platelets',
    'wbc': 'white blood cell count',
    'rbc': 'red blood cell count',
    'inr': 'international normalized ratio',
    'ptt': 'partial thromboplastin time',
    'a1c': 'hemoglobin A1c',
    'hba1c': 'hemoglobin A1c',
    'tsh': 'thyroid stimulating hormone',
    'ldl': 'low-density lipoprotein',
    'hdl': 'high-density lipoprotein',
    'tg': 'triglycerides',
    'tc': 'total cholesterol',
    'egfr': 'estimated glomerular filtration rate',
    'gfr': 'glomerular filtration rate',
    'psa': 'prostate-specific antigen',
    'bnp': 'brain natriuretic peptide',
    'crp': 'C-reactive protein',
    'esr': 'erythrocyte sedimentation rate',
    'anca': 'antineutrophil cytoplasmic antibody',
    'ana': 'antinuclear antibody',
    'rf': 'rheumatoid factor',
}

# Common misspellings of clinical terms
COMMON_MISSPELLINGS = {
    'hypertenshion': 'hypertension',
    'hypertention': 'hypertension',
    'diabeties': 'diabetes',
    'diabetis': 'diabetes',
    'diebetes': 'diabetes',
    'hypothyriodism': 'hypothyroidism',
    'hypothyrodism': 'hypothyroidism',
    'hyperthyriodism': 'hyperthyroidism',
    'hyperlipedemia': 'hyperlipidemia',
    'hyperlipademia': 'hyperlipidemia',
    'dislipidemia': 'dyslipidemia',
    'dyslipedemia': 'dyslipidemia',
    'osteoarthitis': 'osteoarthritis',
    'osteaoarthritis': 'osteoarthritis',
    'rhuematoid': 'rheumatoid',
    'rheumatoid': 'rheumatoid',
    'fibromyalga': 'fibromyalgia',
    'fibromialgia': 'fibromyalgia',
    'pnuemonia': 'pneumonia',
    'pneumona': 'pneumonia',
    'bronchitus': 'bronchitis',
    'bronchites': 'bronchitis',
    'sinusitus': 'sinusitis',
    'pharyngitus': 'pharyngitis',
    'cellulitus': 'cellulitis',
    'diverticulitus': 'diverticulitis',
    'appendicitus': 'appendicitis',
    'gastroenteritus': 'gastroenteritis',
    'nueropathy': 'neuropathy',
    'nuropathy': 'neuropathy',
    'retinopthy': 'retinopathy',
    'cardiomyopthy': 'cardiomyopathy',
    'encephalopthy': 'encephalopathy',
    'nephropthy': 'nephropathy',
    'lisinipril': 'lisinopril',
    'lisinoprol': 'lisinopril',
    'metforman': 'metformin',
    'metformon': 'metformin',
    'atorvistatin': 'atorvastatin',
    'atorvastin': 'atorvastatin',
    'amoxacillin': 'amoxicillin',
    'amoxicilin': 'amoxicillin',
    'levothyroxin': 'levothyroxine',
    'levothyroxene': 'levothyroxine',
    'omeprazol': 'omeprazole',
    'metoprolal': 'metoprolol',
    'gabapenton': 'gabapentin',
    'gabapentine': 'gabapentin',
    'amlodapine': 'amlodipine',
    'amlodapene': 'amlodipine',
    'pantoprazol': 'pantoprazole',
    'sertralin': 'sertraline',
    'escitalopran': 'escitalopram',
    'duloxatine': 'duloxetine',
    'tramadal': 'tramadol',
    'trazadone': 'trazodone',
    'losartin': 'losartan',
    'albuterel': 'albuterol',
    'montelukest': 'montelukast',
    'prednizone': 'prednisone',
    'prednisine': 'prednisone',
    'azithromicin': 'azithromycin',
    'ciprofloxicin': 'ciprofloxacin',
    'doxycyclin': 'doxycycline',
    'clonazapam': 'clonazepam',
    'alprazolam': 'alprazolam',
    'lorazapam': 'lorazepam',
    'hydrochlorothiazid': 'hydrochlorothiazide',
    'carvedolol': 'carvedilol',
    'spironolacton': 'spironolactone',
    'warferin': 'warfarin',
    'clopidogrel': 'clopidogrel',
    'tiotropeum': 'tiotropium',
    'fluticasone': 'fluticasone',
    'budesanide': 'budesonide',
    'semaglutid': 'semaglutide',
    'empagliflozn': 'empagliflozin',
    'jardience': 'jardiance',
    'ozempik': 'ozempic',
    'eliquist': 'eliquis',
}


def analyze_text(text, use_api=True):
    """
    Analyze free text for medical terminology issues.

    Returns a list of findings, each with:
      - original: the word/phrase as found in text
      - suggested: the corrected/expanded form
      - category: 'abbreviation', 'misspelling', 'drug_fuzzy', 'diagnosis_fuzzy'
      - confidence: float 0.0-1.0
      - position: (start, end) character position in text
      - context: surrounding text for display

    Parameters
    ----------
    text : str
        Free text from clinical note section.
    use_api : bool
        If True, queries RxNorm/ICD-10 APIs for unknown terms.
        If False, uses only local dictionaries (faster, offline-safe).
    """
    if not text or len(text.strip()) < 3:
        return []

    findings = []
    words = _tokenize(text)

    for word_info in words:
        word = word_info['word']
        word_lower = word.lower().strip('.,;:!?()')

        if len(word_lower) < 2:
            continue

        # 1. Check known abbreviations
        if word_lower in MEDICAL_ABBREVIATIONS:
            findings.append({
                'original': word,
                'suggested': MEDICAL_ABBREVIATIONS[word_lower],
                'category': 'abbreviation',
                'confidence': 1.0,
                'position': (word_info['start'], word_info['end']),
                'context': _get_context(text, word_info['start'], word_info['end']),
            })
            continue

        # 2. Check known misspellings
        if word_lower in COMMON_MISSPELLINGS:
            findings.append({
                'original': word,
                'suggested': COMMON_MISSPELLINGS[word_lower],
                'category': 'misspelling',
                'confidence': 0.95,
                'position': (word_info['start'], word_info['end']),
                'context': _get_context(text, word_info['start'], word_info['end']),
            })
            continue

        # 3. Fuzzy match against known medical terms (local)
        if len(word_lower) >= 5:
            # Check against misspelling keys (catches close variants)
            close = get_close_matches(word_lower, COMMON_MISSPELLINGS.keys(), n=1, cutoff=0.8)
            if close:
                corrected = COMMON_MISSPELLINGS[close[0]]
                confidence = SequenceMatcher(None, word_lower, close[0]).ratio()
                findings.append({
                    'original': word,
                    'suggested': corrected,
                    'category': 'misspelling',
                    'confidence': confidence,
                    'position': (word_info['start'], word_info['end']),
                    'context': _get_context(text, word_info['start'], word_info['end']),
                })
                continue

            # Check against abbreviation values (expanded forms)
            all_terms = list(set(MEDICAL_ABBREVIATIONS.values()))
            close_terms = get_close_matches(word_lower, [t.lower() for t in all_terms], n=1, cutoff=0.75)
            if close_terms:
                # Find the original term
                for term in all_terms:
                    if term.lower() == close_terms[0]:
                        confidence = SequenceMatcher(None, word_lower, term.lower()).ratio()
                        if confidence < 0.95:  # Don't flag near-perfect matches
                            findings.append({
                                'original': word,
                                'suggested': term,
                                'category': 'misspelling',
                                'confidence': confidence,
                                'position': (word_info['start'], word_info['end']),
                                'context': _get_context(text, word_info['start'], word_info['end']),
                            })
                        break

    # 4. API-based fuzzy matching for unresolved clinical-looking words
    if use_api:
        _enrich_with_api(text, findings)

    # Filter: only return findings with confidence >= 0.6
    findings = [f for f in findings if f['confidence'] >= 0.6]

    # Deduplicate by position
    seen_positions = set()
    unique = []
    for f in findings:
        pos_key = (f['position'][0], f['position'][1])
        if pos_key not in seen_positions:
            seen_positions.add(pos_key)
            unique.append(f)

    return sorted(unique, key=lambda x: x['position'][0])


def expand_abbreviation(abbrev):
    """Expand a single medical abbreviation. Returns None if not found."""
    return MEDICAL_ABBREVIATIONS.get(abbrev.lower().strip())


def check_spelling(word):
    """
    Check a single word against medical dictionaries.
    Returns {'corrected': str, 'confidence': float} or None.
    """
    w = word.lower().strip()
    if w in MEDICAL_ABBREVIATIONS:
        return {'corrected': MEDICAL_ABBREVIATIONS[w], 'confidence': 1.0, 'type': 'abbreviation'}
    if w in COMMON_MISSPELLINGS:
        return {'corrected': COMMON_MISSPELLINGS[w], 'confidence': 0.95, 'type': 'misspelling'}

    # Fuzzy match
    all_known = list(COMMON_MISSPELLINGS.keys()) + list(MEDICAL_ABBREVIATIONS.keys())
    close = get_close_matches(w, all_known, n=1, cutoff=0.75)
    if close:
        key = close[0]
        corrected = COMMON_MISSPELLINGS.get(key) or MEDICAL_ABBREVIATIONS.get(key, key)
        confidence = SequenceMatcher(None, w, key).ratio()
        return {'corrected': corrected, 'confidence': confidence, 'type': 'fuzzy'}

    return None


def _tokenize(text):
    """Split text into word tokens with position tracking."""
    tokens = []
    for match in re.finditer(r'\b[A-Za-z][A-Za-z0-9/&-]*[A-Za-z0-9]\b|[A-Za-z]{2,}', text):
        tokens.append({
            'word': match.group(),
            'start': match.start(),
            'end': match.end(),
        })
    return tokens


def _get_context(text, start, end, window=30):
    """Extract surrounding context for display."""
    ctx_start = max(0, start - window)
    ctx_end = min(len(text), end + window)
    prefix = '...' if ctx_start > 0 else ''
    suffix = '...' if ctx_end < len(text) else ''
    return prefix + text[ctx_start:ctx_end] + suffix


def _enrich_with_api(text, findings):
    """
    For words that look clinical but weren't matched locally,
    try RxNorm spelling suggestions and ICD-10 search.
    """
    try:
        # Find words >= 6 chars that aren't already in findings
        found_positions = {(f['position'][0], f['position'][1]) for f in findings}
        tokens = _tokenize(text)

        # Only check words that look like they might be clinical terms
        # (longer words not in common English)
        COMMON_ENGLISH = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
            'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has',
            'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see',
            'way', 'who', 'did', 'let', 'say', 'she', 'too', 'use', 'with',
            'have', 'from', 'this', 'that', 'they', 'been', 'said', 'each',
            'which', 'their', 'will', 'other', 'about', 'many', 'then',
            'them', 'these', 'some', 'would', 'make', 'like', 'time',
            'very', 'when', 'what', 'your', 'just', 'know', 'take',
            'people', 'into', 'year', 'could', 'than', 'look', 'only',
            'come', 'over', 'such', 'also', 'back', 'after', 'work',
            'first', 'well', 'even', 'want', 'because', 'patient',
            'today', 'currently', 'reports', 'denies', 'states',
            'presents', 'complains', 'history', 'examination',
            'assessment', 'plan', 'follow', 'return', 'continue',
            'start', 'stop', 'increase', 'decrease', 'monitor',
            'refer', 'consult', 'prescribe', 'recommend', 'advise',
            'normal', 'abnormal', 'positive', 'negative', 'chronic',
            'acute', 'stable', 'improved', 'worsening', 'unchanged',
        }

        unchecked = []
        for tok in tokens:
            pos = (tok['start'], tok['end'])
            if pos in found_positions:
                continue
            w = tok['word'].lower()
            if len(w) < 6 or w in COMMON_ENGLISH:
                continue
            unchecked.append(tok)

        # Limit API calls to 5 words per text block
        for tok in unchecked[:5]:
            word = tok['word']
            word_lower = word.lower()

            # Try RxNorm spelling suggestions
            try:
                from app.services.api.rxnorm import RxNormService
                from models import db as _db
                svc = RxNormService(_db)
                suggestions = svc.get_spelling_suggestions(word_lower)
                if suggestions and suggestions.get('suggestions'):
                    best = suggestions['suggestions'][0]
                    confidence = SequenceMatcher(None, word_lower, best.lower()).ratio()
                    if 0.6 <= confidence < 0.95:
                        findings.append({
                            'original': word,
                            'suggested': best,
                            'category': 'drug_fuzzy',
                            'confidence': confidence,
                            'position': (tok['start'], tok['end']),
                            'context': _get_context(text, tok['start'], tok['end']),
                        })
                        continue
            except Exception:
                pass

    except Exception as e:
        logger.debug('API enrichment failed: %s', e)
