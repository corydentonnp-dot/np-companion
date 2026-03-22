"""
tests/test_pip_widgets.py
PH44-4: Picture-in-Picture Widgets — automated checks
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    passed = 0
    failed = 0
    errors = []

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    css_path = os.path.join(base_dir, 'static', 'css', 'main.css')
    base_path = os.path.join(base_dir, 'templates', 'base.html')
    chart_path = os.path.join(base_dir, 'templates', 'patient_chart.html')
    labtrack_path = os.path.join(base_dir, 'templates', 'labtrack.html')
    caregap_path = os.path.join(base_dir, 'templates', 'caregap.html')
    timer_path = os.path.join(base_dir, 'templates', 'timer.html')
    notif_path = os.path.join(base_dir, 'templates', 'notifications.html')

    css = open(css_path, encoding='utf-8').read()
    base = open(base_path, encoding='utf-8').read()
    chart = open(chart_path, encoding='utf-8').read()
    labtrack = open(labtrack_path, encoding='utf-8').read()
    caregap = open(caregap_path, encoding='utf-8').read()
    timer = open(timer_path, encoding='utf-8').read()
    notif = open(notif_path, encoding='utf-8').read()

    def chk(desc, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            errors.append(f'FAIL [{desc}]')

    # CSS checks
    chk('pip-window CSS', '.pip-window {' in css)
    chk('pip-header CSS', '.pip-header {' in css)
    chk('pip-body CSS', '.pip-body {' in css)
    chk('pip-resize-handle CSS', '.pip-resize-handle {' in css)
    chk('pip-minimized CSS', '.pip-window.pip-minimized' in css)
    chk('pip-eligible CSS', '.pip-eligible' in css)
    chk('pip-popout-btn CSS', '.pip-popout-btn' in css)

    # base.html JS checks
    chk('PipManager defined in base.html', 'window.PipManager' in base)
    chk('PipManager.create method', 'function create(sourceEl' in base)
    chk('PipManager.destroy method', 'function destroy(pipId)' in base)
    chk('PipManager.minimize method', 'function minimize(pipId)' in base)
    chk('pip drag/resize handler', '_makeDraggable' in base)
    chk('pip popout btn click handler', '.pip-popout-btn' in base)

    # patient_chart.html PiP injection script
    chk('patient_chart has WIDGET_TITLES map', 'WIDGET_TITLES' in chart)
    chk('patient_chart sets data-pip attribute', "data-pip', 'true'" in chart or "setAttribute('data-pip'" in chart)
    chk('patient_chart adds pip-popout-btn', "pip-popout-btn" in chart)

    # Other templates with pip markers
    chk('labtrack has data-pip', 'data-pip="true"' in labtrack)
    chk('caregap has data-pip', 'data-pip="true"' in caregap)
    chk('timer has data-pip', 'data-pip="true"' in timer)
    chk('notifications has data-pip', 'data-pip="true"' in notif)

    return passed, failed, errors


if __name__ == '__main__':
    passed, failed, errors = run_tests()
    for e in errors:
        print(e)
    print(f'\nResults: {passed} passed, {failed} failed out of {passed + failed} checks')
    sys.exit(0 if failed == 0 else 1)
