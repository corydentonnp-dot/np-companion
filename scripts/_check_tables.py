"""Quick check for new monitoring tables."""
import sqlite3
conn = sqlite3.connect('data/carecompanion.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
targets = ['medication_catalog', 'monitoring_rule_override', 'monitoring_evaluation',
           'monitoring_rule_test', 'monitoring_rule_diff']
for row in cur.fetchall():
    name = row[0]
    if any(t in name for t in targets) or 'monitor' in name:
        print(name)
conn.close()
