# conftest.py — pytest configuration for the tests/ directory
#
# test_phase7.py is a standalone script (run via `python tests/test_phase7.py`).
# It runs all tests at module level and calls sys.exit(), which crashes pytest's
# collection phase. Exclude it from pytest discovery.

collect_ignore = ['test_phase7.py']
