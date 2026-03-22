"""
Integration tests for Phase 12 — Three-Tier Notification Model:
  - 12.1 Notification priority schema (priority column, NOTIFICATION_PRIORITY_DEFAULTS)
  - 12.2 P1 interrupt delivery (modal, 15s poll, Pushover priority=1)
  - 12.3 P2 passive sidebar (grouped dropdown, priority indicators)
  - 12.4 P3 morning-only aggregation (suppressed from bell, in briefing)
  - 12.5 Per-type priority overrides (settings table, JSON pref)
  - 12.6 DB index for P1 fast-poll performance

Tests verify model schema, API endpoints, JS functions, CSS classes,
template structures, and route-level integration.
"""

import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(ROOT, relpath), 'r', encoding='utf-8') as f:
        return f.read()


def run_tests():
    passed = []
    failed = []

    # Load sources
    model_py    = _read('models/notification.py')
    notifier_py = _read('agent/notifier.py')
    auth_py     = _read('routes/auth.py')
    intel_py    = _read('routes/intelligence.py')
    main_js     = _read('static/js/main.js')
    main_css    = _read('static/css/main.css')
    base_html   = _read('templates/base.html')
    settings_html = _read('templates/settings_notifications.html')
    migrate_py  = _read('migrations/migrate_add_notification_priority.py')

    # ==================================================================
    # 12.1 — Notification priority schema
    # ==================================================================
    print('[1/15] Notification model has priority column...')
    try:
        assert 'priority = db.Column(db.Integer' in model_py, 'priority column defined'
        assert 'priority = db.Column(db.Integer, default=2)' in model_py, 'priority default is 2'
        passed.append('12.1a priority column')
    except AssertionError as e:
        failed.append(f'12.1a priority column: {e}')

    print('[2/15] NOTIFICATION_PRIORITY_DEFAULTS dict defined...')
    try:
        assert 'NOTIFICATION_PRIORITY_DEFAULTS' in model_py, 'defaults dict exists'
        assert "'critical_value': 1" in model_py, 'critical_value is P1'
        assert "'lab_result': 2" in model_py, 'lab_result is P2'
        assert "'policy_update': 3" in model_py, 'policy_update is P3'
        assert "'morning_briefing': 3" in model_py, 'morning_briefing is P3'
        passed.append('12.1b priority defaults')
    except AssertionError as e:
        failed.append(f'12.1b priority defaults: {e}')

    print('[3/15] Migration file exists and adds priority column...')
    try:
        assert 'priority' in migrate_py, 'migration references priority'
        assert 'ALTER TABLE notifications ADD COLUMN priority' in migrate_py, 'ALTER TABLE statement'
        assert 'is_critical = 1' in migrate_py, 'back-fill critical to P1'
        passed.append('12.1c migration')
    except AssertionError as e:
        failed.append(f'12.1c migration: {e}')

    # ==================================================================
    # 12.6 — DB index for P1 fast-poll
    # ==================================================================
    print('[4/15] Composite index defined in model...')
    try:
        assert 'ix_notif_p1_poll' in model_py, 'index name in model'
        assert '__table_args__' in model_py, '__table_args__ defined'
        # Index should cover user_id, priority, acknowledged_at
        idx_section = model_py[model_py.index('ix_notif_p1_poll'):][:200]
        assert 'user_id' in idx_section, 'index includes user_id'
        assert 'priority' in idx_section, 'index includes priority'
        assert 'acknowledged_at' in idx_section, 'index includes acknowledged_at'
        passed.append('12.6 composite index')
    except (AssertionError, ValueError) as e:
        failed.append(f'12.6 composite index: {e}')

    # ==================================================================
    # 12.2 — P1 interrupt delivery
    # ==================================================================
    print('[5/15] P1 fast-poll endpoint exists...')
    try:
        assert '/api/notifications/p1' in auth_py, 'P1 endpoint route'
        assert 'priority=1' in auth_py.split('api_notifications_p1')[1][:300], 'filters by priority=1'
        assert 'acknowledged_at' in auth_py.split('api_notifications_p1')[1][:300], 'filters unacknowledged'
        passed.append('12.2a P1 endpoint')
    except (AssertionError, IndexError) as e:
        failed.append(f'12.2a P1 endpoint: {e}')

    print('[6/15] P1 interrupt modal in base.html...')
    try:
        assert 'p1-modal-overlay' in base_html, 'P1 modal overlay'
        assert 'p1-modal-header' in base_html, 'P1 modal header'
        assert 'p1-modal-body' in base_html, 'P1 modal body'
        assert 'acknowledgeP1' in base_html, 'acknowledge button'
        assert 'snoozeP1' in base_html, 'snooze button'
        passed.append('12.2b P1 modal HTML')
    except AssertionError as e:
        failed.append(f'12.2b P1 modal HTML: {e}')

    print('[7/15] P1 polling JS at 15-second interval...')
    try:
        assert 'initP1Poll' in main_js, 'initP1Poll function'
        assert '15000' in main_js, '15-second interval'
        assert 'acknowledgeP1' in main_js, 'acknowledgeP1 function'
        assert 'snoozeP1' in main_js, 'snoozeP1 function'
        assert 'showP1Modal' in main_js, 'showP1Modal function'
        passed.append('12.2c P1 polling JS')
    except AssertionError as e:
        failed.append(f'12.2c P1 polling JS: {e}')

    print('[8/15] Notifier sets priority=1 for critical notifications...')
    try:
        assert 'priority=1' in notifier_py, 'priority=1 in notifier'
        assert 'from datetime import' in notifier_py and 'timedelta' in notifier_py, 'timedelta imported'
        passed.append('12.2d notifier priority')
    except (AssertionError, IndexError) as e:
        failed.append(f'12.2d notifier priority: {e}')

    # ==================================================================
    # 12.3 — P2 passive sidebar
    # ==================================================================
    print('[9/15] Dropdown groups: New / Earlier Today...')
    try:
        assert 'notif-dd-section-label' in main_js, 'section label class in JS'
        assert 'New' in main_js.split('notif-dd-section-label')[1][:50], 'New section'
        assert 'Earlier Today' in main_js, 'Earlier Today section'
        passed.append('12.3a dropdown grouping')
    except (AssertionError, IndexError) as e:
        failed.append(f'12.3a dropdown grouping: {e}')

    print('[10/15] Priority indicator CSS classes...')
    try:
        assert '.notif-dd-item--p1' in main_css, 'P1 indicator class'
        assert '.notif-dd-item--p2' in main_css, 'P2 indicator class'
        assert '.notif-dd-section-label' in main_css, 'section label CSS'
        passed.append('12.3b priority indicators CSS')
    except AssertionError as e:
        failed.append(f'12.3b priority indicators CSS: {e}')

    # ==================================================================
    # 12.4 — P3 morning-only aggregation
    # ==================================================================
    print('[11/15] P3 suppressed from bell (API filters P1+P2 only)...')
    try:
        api_section = auth_py.split('def api_notifications()')[1][:500]
        assert 'priority.in_([1, 2])' in api_section, 'API filters P1+P2 only'
        passed.append('12.4a P3 suppressed')
    except (AssertionError, IndexError) as e:
        failed.append(f'12.4a P3 suppressed: {e}')

    print('[12/15] P3 passed to morning briefing...')
    try:
        briefing_section = intel_py.split('def morning_briefing')[1][:3000]
        assert 'p3_notifications' in briefing_section, 'p3_notifications in briefing'
        assert 'priority' in briefing_section, 'queries by priority'
        passed.append('12.4b P3 in morning briefing')
    except (AssertionError, IndexError) as e:
        failed.append(f'12.4b P3 in morning briefing: {e}')

    print('[13/15] P3 count endpoint + dropdown teaser...')
    try:
        assert '/api/notifications/p3-count' in auth_py, 'P3 count endpoint'
        assert 'p3-count' in main_js, 'JS fetches P3 count'
        assert 'morning briefing' in main_js, 'morning briefing teaser text'
        passed.append('12.4c P3 dropdown teaser')
    except AssertionError as e:
        failed.append(f'12.4c P3 dropdown teaser: {e}')

    # ==================================================================
    # 12.5 — Per-type priority overrides
    # ==================================================================
    print('[14/15] Priority override table in settings...')
    try:
        assert 'notification_priority_overrides' in settings_html, 'overrides pref key'
        assert 'priority_override_' in settings_html, 'override form fields'
        assert 'P1 — Interrupt' in settings_html, 'P1 option'
        assert 'P2 — Passive' in settings_html, 'P2 option'
        assert 'P3 — Morning' in settings_html, 'P3 option'
        assert 'P1 (locked)' in settings_html, 'critical value locked to P1'
        passed.append('12.5a settings UI')
    except AssertionError as e:
        failed.append(f'12.5a settings UI: {e}')

    print('[15/15] Route saves priority overrides to preferences...')
    try:
        settings_section = auth_py.split('def settings_notifications')[1][:4000]
        assert 'notification_priority_overrides' in settings_section, 'overrides saved'
        assert 'priority_override_' in settings_section, 'form fields parsed'
        passed.append('12.5b route saves overrides')
    except (AssertionError, IndexError) as e:
        failed.append(f'12.5b route saves overrides: {e}')

    # ==================================================================
    # Results
    # ==================================================================
    print('\n' + '=' * 60)
    print(f'Phase 12 Results: {len(passed)} passed, {len(failed)} failed')
    print('=' * 60)
    for p in passed:
        print(f'  ✓ {p}')
    for f in failed:
        print(f'  ✗ {f}')

    return 0 if not failed else 1


if __name__ == '__main__':
    sys.exit(run_tests())
