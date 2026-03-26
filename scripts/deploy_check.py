"""
Phase 4 — Automated Pre-Flight Deployment Checker (final_plan.md Phase 4)

Verifies every automatable item from pre_beta_deployment_checklist.md (Production Environment Setup section):
  1. Environment & Security
  2. Machine & Display
  3. Database & Migrations
  4. User Accounts
  5. Notifications
  6. API Keys
  7. NetPractice / AC
  8. Agent Job Registry
  9. Health & Logging
  10. Full Test Suite
  11. Report Generation

Usage:
    venv\\Scripts\\python.exe tools/deploy_check.py
"""

import os
import sys
import json
import sqlite3
import subprocess
import platform
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

KNOWN_DEV_DEFAULTS = [
    'dev-secret-key', 'change-me', 'your-secret', 'changeme',
    'supersecret', 'testing', 'test-key', 'default-secret',
    'replace-this', 'placeholder',
]

CRITICAL_TABLES = [
    'users', 'billing_opportunity', 'billing_rule', 'patient_record',
    'monitoring_rule', 'monitoring_schedule', 'rems_tracker_entry',
    'calculator_result', 'ccm_enrollment', 'tcm_watch_entry',
    'bonus_tracker', 'documentation_phrase', 'closed_loop_status',
    'opportunity_suppression', 'immunization_series', 'communication_log',
    'billing_campaign', 'payer_coverage_matrix', 'diagnosis_revenue_profile',
    'patient_lab_results', 'patient_social_history',
]

EXPECTED_AGENT_JOBS = [
    'heartbeat', 'mrn_reader', 'inbox_check', 'inbox_digest',
    'callback_check', 'overdue_lab_check', 'xml_archive_cleanup',
    'xml_poll', 'weekly_summary', 'monthly_billing', 'deactivation_check',
    'delayed_message_sender', 'eod_check', 'drug_recall_scan',
    'previsit_billing', 'daily_backup',
]

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
GRAY = '\033[90m'
BOLD = '\033[1m'
RESET = '\033[0m'


class DeployChecker:
    def __init__(self):
        self.results = {}
        self.warnings = set()

    def check(self, name, passed, detail='', is_warning=False):
        """Record a single check result."""
        self.results[name] = {
            'pass': bool(passed),
            'detail': detail,
            'warning': is_warning,
        }
        if is_warning and not passed:
            self.warnings.add(name)
        return passed

    # ── Section 1: Environment & Security ──────────────────────────
    def section_environment(self):
        results = []
        try:
            import config as cfg
        except ImportError:
            self.check('config_importable', False, 'config.py not found')
            return

        self.check('debug_false',
                    getattr(cfg, 'DEBUG', True) is False,
                    f'DEBUG={getattr(cfg, "DEBUG", "MISSING")}')

        self.check('mock_mode_false',
                    getattr(cfg, 'AC_MOCK_MODE', True) is False,
                    f'AC_MOCK_MODE={getattr(cfg, "AC_MOCK_MODE", "MISSING")}')

        secret = getattr(cfg, 'SECRET_KEY', '')
        is_long = len(secret) >= 32
        is_not_dev = secret.lower() not in KNOWN_DEV_DEFAULTS
        self.check('secret_key_random',
                    is_long and is_not_dev,
                    f'len={len(secret)}, known_default={not is_not_dev}')

        gitignore_path = os.path.join(ROOT, '.gitignore')
        in_gitignore = False
        if os.path.exists(gitignore_path):
            with open(gitignore_path, encoding='utf-8', errors='replace') as f:
                in_gitignore = 'config.py' in f.read()
        self.check('config_in_gitignore', in_gitignore)

    # ── Section 2: Machine & Display ───────────────────────────────
    def section_machine(self):
        try:
            import config as cfg
        except ImportError:
            cfg = None

        tess_path = getattr(cfg, 'TESSERACT_PATH', '') if cfg else ''
        self.check('tesseract_installed',
                    os.path.exists(tess_path) if tess_path else False,
                    tess_path or 'not configured')

        mock = getattr(cfg, 'AC_MOCK_MODE', True) if cfg else True
        ac_path = getattr(cfg, 'AC_EXE_PATH', '') if cfg else ''
        if mock:
            self.check('ac_exe_reachable', True, 'skipped (mock mode)')
        else:
            self.check('ac_exe_reachable',
                        os.path.exists(ac_path) if ac_path else False,
                        ac_path or 'not configured')

        self.check('data_dir_exists', os.path.isdir(os.path.join(ROOT, 'data')))
        self.check('logs_dir_exists', os.path.isdir(os.path.join(ROOT, 'data', 'logs')))
        self.check('backups_dir_exists', os.path.isdir(os.path.join(ROOT, 'data', 'backups')))

    # ── Section 3: Database & Migrations ───────────────────────────
    def section_database(self):
        db_path = os.path.join(ROOT, 'data', 'carecompanion.db')
        self.check('db_file_exists', os.path.exists(db_path), db_path)

        if not os.path.exists(db_path):
            self.check('db_integrity', False, 'DB file missing')
            self.check('migrations_table', False, 'DB file missing')
            self.check('migration_count', False, 'DB file missing')
            self.check('critical_tables', False, 'DB file missing')
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('PRAGMA integrity_check')
            result = cursor.fetchone()[0]
            self.check('db_integrity', result == 'ok', result)
        except Exception as e:
            self.check('db_integrity', False, str(e))

        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='_applied_migrations'")
            has_table = cursor.fetchone() is not None
            self.check('migrations_table', has_table)
        except Exception as e:
            self.check('migrations_table', False, str(e))

        try:
            cursor.execute('SELECT COUNT(*) FROM _applied_migrations')
            count = cursor.fetchone()[0]
            self.check('migration_count', count >= 35, f'{count} migrations')
        except Exception as e:
            self.check('migration_count', False, str(e))

        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing = {row[0] for row in cursor.fetchall()}
            missing = [t for t in CRITICAL_TABLES if t not in existing]
            self.check('critical_tables',
                        len(missing) == 0,
                        f'{len(CRITICAL_TABLES) - len(missing)}/{len(CRITICAL_TABLES)} present' +
                        (f', missing: {missing}' if missing else ''))
            conn.close()
        except Exception as e:
            self.check('critical_tables', False, str(e))

    # ── Section 4: User Accounts ───────────────────────────────────
    def section_users(self):
        db_path = os.path.join(ROOT, 'data', 'carecompanion.db')
        if not os.path.exists(db_path):
            self.check('admin_exists', False, 'DB missing')
            self.check('user_count', False, 'DB missing')
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
            admin_count = cursor.fetchone()[0]
            self.check('admin_exists', admin_count >= 1, f'{admin_count} admin(s)')

            cursor.execute('SELECT COUNT(*) FROM users')
            user_count = cursor.fetchone()[0]
            self.check('user_count', user_count >= 1, f'{user_count} user(s)')
            conn.close()
        except Exception as e:
            self.check('admin_exists', False, str(e))
            self.check('user_count', False, str(e))

    # ── Section 5: Notifications ───────────────────────────────────
    def section_notifications(self):
        try:
            import config as cfg
        except ImportError:
            cfg = None

        self.check('pushover_user_key',
                    bool(getattr(cfg, 'PUSHOVER_USER_KEY', '') if cfg else ''))
        self.check('pushover_api_token',
                    bool(getattr(cfg, 'PUSHOVER_API_TOKEN', '') if cfg else ''))
        self.check('smtp_server',
                    bool(getattr(cfg, 'SMTP_SERVER', '') if cfg else ''),
                    is_warning=True)

    # ── Section 6: API Keys ────────────────────────────────────────
    def section_api_keys(self):
        try:
            import config as cfg
        except ImportError:
            cfg = None

        self.check('openfda_key',
                    bool(os.environ.get('OPENFDA_API_KEY') or
                         getattr(cfg, 'OPENFDA_API_KEY', '') if cfg else ''))
        self.check('umls_key',
                    bool(os.environ.get('UMLS_API_KEY') or
                         getattr(cfg, 'UMLS_API_KEY', '') if cfg else ''))
        self.check('loinc_creds',
                    bool(os.environ.get('LOINC_USERNAME') or
                         getattr(cfg, 'LOINC_USERNAME', '') if cfg else ''))
        self.check('pubmed_key',
                    bool(os.environ.get('PUBMED_API_KEY') or
                         getattr(cfg, 'PUBMED_API_KEY', '') if cfg else ''),
                    is_warning=True)

    # ── Section 7: NetPractice / AC ────────────────────────────────
    def section_netpractice(self):
        try:
            import config as cfg
        except ImportError:
            cfg = None

        self.check('netpractice_url',
                    bool(getattr(cfg, 'NETPRACTICE_URL', '') if cfg else ''))
        self.check('ac_mock_false',
                    getattr(cfg, 'AC_MOCK_MODE', True) is False if cfg else False,
                    f'AC_MOCK_MODE={getattr(cfg, "AC_MOCK_MODE", "MISSING") if cfg else "no config"}')
        self.check('ac_credentials',
                    bool(getattr(cfg, 'AC_LOGIN_USERNAME', '') if cfg else '') and
                    bool(getattr(cfg, 'AC_LOGIN_PASSWORD', '') if cfg else ''))

    # ── Section 8: Agent Job Registry ──────────────────────────────
    def section_agent_jobs(self):
        src_path = os.path.join(ROOT, 'agent_service.py')
        try:
            with open(src_path, encoding='utf-8') as f:
                src = f.read()
            found_jobs = []
            for job_name in EXPECTED_AGENT_JOBS:
                if f'def job_{job_name}' in src:
                    found_jobs.append(job_name)
            missing = [j for j in EXPECTED_AGENT_JOBS if j not in found_jobs]
            self.check('agent_job_count',
                        len(found_jobs) >= len(EXPECTED_AGENT_JOBS),
                        f'{len(found_jobs)}/{len(EXPECTED_AGENT_JOBS)} jobs' +
                        (f', missing: {missing}' if missing else ''))
        except Exception as e:
            self.check('agent_job_count', False, str(e))

    # ── Section 9: Health & Logging ────────────────────────────────
    def section_health(self):
        try:
            os.environ['FLASK_ENV'] = 'testing'
            from app import create_app
            app = create_app()
            app.config['TESTING'] = True
            with app.test_client() as client:
                with app.app_context():
                    from models.user import User
                    user = User.query.filter_by(is_active_account=True).first()
                    if user:
                        with client.session_transaction() as sess:
                            sess['_user_id'] = str(user.id)
                r = client.get('/api/health')
                self.check('health_endpoint',
                            r.status_code == 200,
                            f'status={r.status_code}')
        except Exception as e:
            self.check('health_endpoint', False, str(e))

        logs_dir = os.path.join(ROOT, 'data', 'logs')
        self.check('log_dir_writable',
                    os.access(logs_dir, os.W_OK) if os.path.isdir(logs_dir) else False)

        src_path = os.path.join(ROOT, 'agent_service.py')
        try:
            with open(src_path, encoding='utf-8') as f:
                src = f.read()
            self.check('backup_job_in_src', 'daily_backup' in src)
        except Exception:
            self.check('backup_job_in_src', False)

    # ── Section 10: Test Suite ─────────────────────────────────────
    def section_test_suite(self):
        try:
            python = sys.executable
            result = subprocess.run(
                [python, os.path.join(ROOT, 'tests', 'test_verification.py')],
                capture_output=True, text=True, timeout=180,
                cwd=ROOT,
            )
            output = result.stdout + result.stderr
            passed = result.returncode == 0
            # Extract last 10 lines for detail
            lines = output.strip().split('\n')
            snippet = '\n'.join(lines[-10:])
            self.check('test_suite_pass', passed, snippet)
        except subprocess.TimeoutExpired:
            self.check('test_suite_pass', False, 'Timed out after 180s')
        except Exception as e:
            self.check('test_suite_pass', False, str(e))

    # ── Run all sections ───────────────────────────────────────────
    def run_all_checks(self):
        sections = [
            ('Environment & Security', self.section_environment),
            ('Machine & Display', self.section_machine),
            ('Database & Migrations', self.section_database),
            ('User Accounts', self.section_users),
            ('Notifications', self.section_notifications),
            ('API Keys', self.section_api_keys),
            ('NetPractice / AC', self.section_netpractice),
            ('Agent Job Registry', self.section_agent_jobs),
            ('Health & Logging', self.section_health),
            ('Full Test Suite', self.section_test_suite),
        ]

        for name, fn in sections:
            try:
                fn()
            except Exception as e:
                self.check(f'{name}_error', False, str(e))

        return self.results

    # ── Report generation ──────────────────────────────────────────
    def generate_report(self):
        passed = sum(1 for r in self.results.values() if r['pass'])
        failed_hard = sum(1 for n, r in self.results.items()
                          if not r['pass'] and not r.get('warning'))
        warnings = sum(1 for r in self.results.values()
                       if not r['pass'] and r.get('warning'))

        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': 'v1.1.3',
            'host': platform.node(),
            'checks': self.results,
            'summary': {
                'passed': passed,
                'failed': failed_hard,
                'warnings': warnings,
            },
        }

        report_path = os.path.join(ROOT, 'tools', 'deploy_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)

        return report

    # ── Console output ─────────────────────────────────────────────
    def print_results(self):
        sections = {
            'Environment & Security': ['debug_false', 'mock_mode_false', 'secret_key_random', 'config_in_gitignore', 'config_importable'],
            'Machine & Display': ['tesseract_installed', 'ac_exe_reachable', 'data_dir_exists', 'logs_dir_exists', 'backups_dir_exists'],
            'Database & Migrations': ['db_file_exists', 'db_integrity', 'migrations_table', 'migration_count', 'critical_tables'],
            'User Accounts': ['admin_exists', 'user_count'],
            'Notifications': ['pushover_user_key', 'pushover_api_token', 'smtp_server'],
            'API Keys': ['openfda_key', 'umls_key', 'loinc_creds', 'pubmed_key'],
            'NetPractice / AC': ['netpractice_url', 'ac_mock_false', 'ac_credentials'],
            'Agent Job Registry': ['agent_job_count'],
            'Health & Logging': ['health_endpoint', 'log_dir_writable', 'backup_job_in_src'],
            'Full Test Suite': ['test_suite_pass'],
        }

        for section_name, check_names in sections.items():
            section_checks = [(n, self.results.get(n)) for n in check_names if n in self.results]
            if not section_checks:
                continue

            section_pass = sum(1 for _, r in section_checks if r['pass'])
            section_total = len(section_checks)
            print(f'\n{BOLD}── {section_name} ({section_pass}/{section_total}) ──{RESET}')

            for name, r in section_checks:
                if r['pass']:
                    icon = f'{GREEN}✓{RESET}'
                elif r.get('warning'):
                    icon = f'{YELLOW}⚠{RESET}'
                else:
                    icon = f'{RED}✗{RESET}'
                detail = f'  ({r["detail"]})' if r.get('detail') else ''
                print(f'  {icon} {name}{detail}')

        # Summary
        total_pass = sum(1 for r in self.results.values() if r['pass'])
        total_fail = sum(1 for n, r in self.results.items()
                         if not r['pass'] and not r.get('warning'))
        total_warn = sum(1 for r in self.results.values()
                         if not r['pass'] and r.get('warning'))

        print(f'\n{BOLD}{"=" * 60}{RESET}')
        if total_fail == 0:
            print(f'{GREEN}{BOLD}READY FOR DEPLOY ✓  ({total_pass} passed, {total_fail} failed, {total_warn} warnings){RESET}')
        else:
            print(f'{RED}{BOLD}NOT READY — {total_fail} failures ✗  ({total_pass} passed, {total_fail} failed, {total_warn} warnings){RESET}')
        print(f'{BOLD}{"=" * 60}{RESET}')

        return total_fail == 0


def run_all_checks():
    """Entry point for programmatic use (e.g., from verify_all.py)."""
    checker = DeployChecker()
    checker.run_all_checks()
    report = checker.generate_report()
    return report


if __name__ == '__main__':
    checker = DeployChecker()
    checker.run_all_checks()
    checker.generate_report()
    is_ready = checker.print_results()
    sys.exit(0 if is_ready else 1)
