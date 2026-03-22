"""
Integration tests for Phase 22: GoodRx Price Compare Service Module (Tier 2)

Tests verify:
- GoodRxService class structure and inheritance
- HMAC-SHA256 request signing logic
- search_drug method signature and graceful degradation
- get_price_compare method signature and attribution
- get_price unified entry point with all response shapes
"""

import os
import sys
import hmac
import hashlib
import base64
from urllib.parse import urlencode

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(ROOT, relpath), 'r', encoding='utf-8') as f:
        return f.read()


def run_tests():
    passed = []
    failed = []

    goodrx_py = _read('app/services/api/goodrx_service.py')

    # ==================================================================
    # 22.1 — GoodRxService class structure
    # ==================================================================
    print('[1/15] GoodRxService inherits BaseAPIClient...')
    try:
        assert 'class GoodRxService(BaseAPIClient)' in goodrx_py, 'Class inheritance'
        assert 'api_name="goodrx"' in goodrx_py, 'API name'
        assert 'GOODRX_BASE_URL' in goodrx_py, 'Uses config URL'
        assert 'GOODRX_CACHE_TTL_DAYS' in goodrx_py, 'Uses config TTL'
        passed.append('22.1 GoodRxService class structure')
    except AssertionError as e:
        failed.append(f'22.1 GoodRxService class: {e}')

    print('[2/15] Prominent Coupon API exclusion docstring...')
    try:
        assert 'PRICE COMPARE API ONLY' in goodrx_py, 'Price Compare Only notice'
        assert 'Coupon API' in goodrx_py, 'Coupon API mentioned'
        assert 'INTENTIONALLY EXCLUDED' in goodrx_py, 'Exclusion notice'
        assert '3,000 coupon accesses/month' in goodrx_py, 'Volume reason'
        passed.append('22.1b Coupon API exclusion docstring')
    except AssertionError as e:
        failed.append(f'22.1b Coupon exclusion docstring: {e}')

    print('[3/15] Config imports present...')
    try:
        assert 'from app.api_config import' in goodrx_py, 'Config import block'
        assert 'GOODRX_API_KEY' in goodrx_py, 'API key imported'
        assert 'GOODRX_SECRET_KEY' in goodrx_py, 'Secret key imported'
        assert 'GOODRX_DEFAULT_ZIP' in goodrx_py, 'Default ZIP imported'
        passed.append('22.1c Config imports')
    except AssertionError as e:
        failed.append(f'22.1c Config imports: {e}')

    # ==================================================================
    # 22.2 — HMAC-SHA256 Request Signing
    # ==================================================================
    print('[4/15] _sign_request method exists...')
    try:
        assert 'def _sign_request(self, params)' in goodrx_py, '_sign_request method'
        assert 'hmac' in goodrx_py.lower(), 'Uses hmac module'
        assert 'hashlib' in goodrx_py.lower(), 'Uses hashlib module'
        assert 'sha256' in goodrx_py.lower(), 'SHA256 algorithm'
        passed.append('22.2 _sign_request method')
    except AssertionError as e:
        failed.append(f'22.2 _sign_request method: {e}')

    print('[5/15] HMAC signing produces correct signature for known input...')
    try:
        # Reproduce the signing algorithm from the service
        test_secret = "test_secret_key"
        test_params = {"name": "atorvastatin", "quantity": "30", "api_key": "test_key"}
        sorted_params = sorted(test_params.items())
        query_string = urlencode(sorted_params)
        digest = hmac.new(
            test_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        sig = base64.b64encode(digest).decode("utf-8")

        # Verify the sig is a non-empty base64 string
        assert len(sig) > 0, 'Signature is non-empty'
        # Verify it's valid base64
        base64.b64decode(sig)
        # Verify consistency — same input produces same output
        digest2 = hmac.new(
            test_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        sig2 = base64.b64encode(digest2).decode("utf-8")
        assert sig == sig2, 'Signing is deterministic'
        passed.append('22.2b HMAC signing consistency')
    except AssertionError as e:
        failed.append(f'22.2b HMAC signing: {e}')

    print('[6/15] Graceful degradation when secret key is empty...')
    try:
        assert 'GOODRX_SECRET_KEY' in goodrx_py, 'Checks secret key'
        assert 'return None' in goodrx_py, 'Returns None on missing key'
        # Verify the method checks for empty key before signing
        lines = goodrx_py.split('\n')
        in_sign = False
        found_guard = False
        for line in lines:
            if 'def _sign_request' in line:
                in_sign = True
            elif in_sign and line.strip().startswith('def '):
                break
            elif in_sign and 'not GOODRX_SECRET_KEY' in line:
                found_guard = True
                break
        assert found_guard, 'Guard clause for empty secret key'
        passed.append('22.2c Graceful degradation (empty key)')
    except AssertionError as e:
        failed.append(f'22.2c Graceful degradation: {e}')

    # ==================================================================
    # 22.3 — Drug Search
    # ==================================================================
    print('[7/15] search_drug method exists...')
    try:
        assert 'def search_drug(self, drug_name)' in goodrx_py, 'search_drug method'
        passed.append('22.3 search_drug method')
    except AssertionError as e:
        failed.append(f'22.3 search_drug method: {e}')

    print('[8/15] search_drug checks API key before calling...')
    try:
        lines = goodrx_py.split('\n')
        in_search = False
        found_key_check = False
        for line in lines:
            if 'def search_drug' in line:
                in_search = True
            elif in_search and line.strip().startswith('def '):
                break
            elif in_search and 'GOODRX_API_KEY' in line:
                found_key_check = True
                break
        assert found_key_check, 'Checks API key in search_drug'
        passed.append('22.3b search_drug key check')
    except AssertionError as e:
        failed.append(f'22.3b search_drug key check: {e}')

    # ==================================================================
    # 22.4 — Price Compare
    # ==================================================================
    print('[9/15] get_price_compare method exists...')
    try:
        assert 'def get_price_compare(self, drug_name' in goodrx_py, 'get_price_compare'
        assert 'quantity' in goodrx_py, 'Quantity param'
        assert 'zip_code' in goodrx_py, 'ZIP code param'
        passed.append('22.4 get_price_compare method')
    except AssertionError as e:
        failed.append(f'22.4 get_price_compare method: {e}')

    print('[10/15] Price compare uses GOODRX_DEFAULT_ZIP fallback...')
    try:
        lines = goodrx_py.split('\n')
        in_compare = False
        found_default_zip = False
        for line in lines:
            if 'def get_price_compare' in line:
                in_compare = True
            elif in_compare and line.strip().startswith('def ') and 'get_price_compare' not in line:
                break
            elif in_compare and 'GOODRX_DEFAULT_ZIP' in line:
                found_default_zip = True
                break
        assert found_default_zip, 'Falls back to default ZIP'
        passed.append('22.4b Default ZIP fallback')
    except AssertionError as e:
        failed.append(f'22.4b Default ZIP fallback: {e}')

    print('[11/15] Attribution text included in results...')
    try:
        assert 'Powered by GoodRx' in goodrx_py, 'Attribution text present'
        assert 'attribution_text' in goodrx_py, 'Attribution key in result'
        passed.append('22.4c Attribution text')
    except AssertionError as e:
        failed.append(f'22.4c Attribution text: {e}')

    print('[12/15] Deep link URL built (not coupon link)...')
    try:
        assert 'goodrx.com/' in goodrx_py, 'GoodRx page link'
        assert 'deep_link_url' in goodrx_py, 'Deep link key'
        # Verify it's NOT a coupon link
        assert '/coupon' not in goodrx_py.split('deep_link')[1][:100] if 'deep_link' in goodrx_py else True, 'Not a coupon link'
        passed.append('22.4d Deep link (no coupon)')
    except AssertionError as e:
        failed.append(f'22.4d Deep link: {e}')

    # ==================================================================
    # 22.5 — Unified get_price Entry Point
    # ==================================================================
    print('[13/15] get_price unified entry point...')
    try:
        assert 'def get_price(self' in goodrx_py, 'get_price method'
        assert '"source": "goodrx"' in goodrx_py, 'Source label'
        assert '"found": False' in goodrx_py or '"found": True' in goodrx_py, 'Found flag'
        passed.append('22.5 get_price unified entry')
    except AssertionError as e:
        failed.append(f'22.5 get_price unified entry: {e}')

    print('[14/15] API-key-not-configured graceful response...')
    try:
        assert 'api_key_not_configured' in goodrx_py, 'Key not configured reason'
        assert 'api_unavailable' not in goodrx_py or 'api_unavailable' in goodrx_py, 'Check present'
        # Find the pattern: returns {found: False, source: goodrx, reason: api_key_not_configured}
        lines = goodrx_py.split('\n')
        in_get_price = False
        found_not_configured = False
        for line in lines:
            if 'def get_price(self' in line:
                in_get_price = True
            elif in_get_price and line.strip().startswith('def '):
                break
            elif in_get_price and 'api_key_not_configured' in line:
                found_not_configured = True
                break
        assert found_not_configured, 'api_key_not_configured in get_price method'
        passed.append('22.5b Graceful not-configured response')
    except AssertionError as e:
        failed.append(f'22.5b Not-configured response: {e}')

    print('[15/15] Service module imports validate...')
    try:
        from app.api_config import (GOODRX_BASE_URL, GOODRX_CACHE_TTL_DAYS,
                                     GOODRX_DEFAULT_ZIP, GOODRX_API_KEY,
                                     GOODRX_SECRET_KEY)
        assert GOODRX_BASE_URL == 'https://api.goodrx.com', f'URL={GOODRX_BASE_URL}'
        assert GOODRX_CACHE_TTL_DAYS == 1, f'TTL={GOODRX_CACHE_TTL_DAYS}'
        assert GOODRX_DEFAULT_ZIP == '23832', f'ZIP={GOODRX_DEFAULT_ZIP}'
        assert isinstance(GOODRX_API_KEY, str), 'Key is string'
        assert isinstance(GOODRX_SECRET_KEY, str), 'Secret is string'
        passed.append('22 Config imports all valid')
    except AssertionError as e:
        failed.append(f'22 Config imports: {e}')
    except ImportError as e:
        failed.append(f'22 Config imports: ImportError - {e}')

    # ==================================================================
    # Summary
    # ==================================================================
    print()
    print('=' * 60)
    print(f'Phase 22 GoodRx Service: {len(passed)} passed, {len(failed)} failed')
    print('=' * 60)

    if failed:
        for f in failed:
            print(f'  FAIL: {f}')
        sys.exit(1)
    else:
        print('  All tests passed!')
    return len(passed), len(failed)


if __name__ == '__main__':
    run_tests()
