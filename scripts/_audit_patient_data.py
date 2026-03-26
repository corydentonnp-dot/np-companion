"""One-shot script: audit clinical data completeness in all demo XML files."""
import os, glob, re

all_xmls = (
    glob.glob('Documents/demo_patients/*.xml') +
    glob.glob('data/clinical_summaries/*.xml') +
    glob.glob('Documents/_archive/*.xml')
)

for f in sorted(all_xmls):
    fname = os.path.basename(f)
    loc = os.path.dirname(f)
    with open(f, 'r', encoding='utf-8', errors='replace') as fh:
        content = fh.read()
    
    # Extract patient name
    name_match = re.search(r'<given>([^<]+)</given>.*?<family>([^<]+)</family>', content, re.DOTALL)
    name = '{} {}'.format(name_match.group(1), name_match.group(2)) if name_match else 'UNKNOWN'
    
    # Extract MRN
    mrn_match = re.search(r'extension="(\d{4,10})"', content)
    mrn = mrn_match.group(1) if mrn_match else 'UNKNOWN'
    
    def count_rows(section_name):
        idx = content.lower().find(section_name.lower())
        if idx < 0:
            return 0
        chunk = content[idx:idx+3000]
        table_end = chunk.find('</table')
        if table_end > 0:
            chunk = chunk[:table_end]
        return max(0, chunk.count('<tr') - 1)  # -1 for header row
    
    sections = {
        'Vitals': count_rows('Vital Signs'),
        'Meds': count_rows('Medications'),
        'Allergies': count_rows('Allergies'),
        'Problems': count_rows('Problems'),
        'Labs': count_rows('Lab Results'),
        'FamHx': 'YES' if 'family history' in content.lower() else 'NO',
        'SocHx': count_rows('Social History'),
        'Immun': count_rows('Immunizations'),
        'Procedures': 'YES' if 'procedures' in content.lower() else 'NO',
        'Encounters': 'YES' if 'encounters' in content.lower() else 'NO',
    }
    
    print('\n{} | MRN: {} | {} | {:,} chars'.format(name, mrn, loc, len(content)))
    for k, v in sections.items():
        print('  {:12s}: {}'.format(k, v))
