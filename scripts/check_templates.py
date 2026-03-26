"""Quick template syntax check — run then delete."""
from jinja2 import Environment, FileSystemLoader
import os

env = Environment(loader=FileSystemLoader('templates'))
errors = []
count = 0
for f in sorted(os.listdir('templates')):
    if f.endswith('.html'):
        count += 1
        try:
            env.get_template(f)
        except Exception as e:
            errors.append(f'{f}: {e}')
if errors:
    for e in errors:
        print('ERROR:', e)
else:
    print(f'All {count} templates parse OK')
