"""
Extract base32 TOTP secret from a Google Authenticator migration URI.

Usage:
    python tools/totp_extractor.py "otpauth-migration://offline?data=..."

Outputs the base32 secret(s) found in the migration payload.
Requires: protobuf (pip install protobuf)
"""

import sys
import base64
import hmac
from urllib.parse import unquote, urlparse, parse_qs


def decode_migration_uri(uri: str) -> list[dict]:
    """Decode an otpauth-migration:// URI and return a list of accounts.

    Each account dict has keys: secret_b32, name, issuer, type, algorithm, digits.
    """
    parsed = urlparse(uri)
    qs = parse_qs(parsed.query)
    raw_b64 = qs.get('data', [''])[0]
    payload = base64.b64decode(unquote(raw_b64))

    # Minimal protobuf decoding without requiring google.protobuf.
    # The migration payload is a repeated field 1 (OtpParameters message).
    # Inside each OtpParameters: field 1=secret (bytes), field 2=name (string),
    # field 3=issuer (string), field 4=algorithm (varint), field 5=digits (varint),
    # field 6=type (varint).
    accounts = []
    pos = 0
    while pos < len(payload):
        # Read outer tag
        tag_byte = payload[pos]; pos += 1
        field_num = tag_byte >> 3
        wire_type = tag_byte & 0x07

        if wire_type == 2:  # length-delimited (our repeated OtpParameters)
            length, pos = _read_varint(payload, pos)
            if field_num == 1:
                inner = payload[pos:pos + length]
                accounts.append(_parse_otp_params(inner))
            pos += length
        elif wire_type == 0:  # varint
            _, pos = _read_varint(payload, pos)
        else:
            break

    return accounts


def _read_varint(buf: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while True:
        b = buf[pos]; pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, pos


def _parse_otp_params(data: bytes) -> dict:
    result = {'secret_b32': '', 'name': '', 'issuer': '', 'type': 0, 'algorithm': 0, 'digits': 0}
    pos = 0
    while pos < len(data):
        tag_byte = data[pos]; pos += 1
        field_num = tag_byte >> 3
        wire_type = tag_byte & 0x07

        if wire_type == 2:
            length, pos = _read_varint(data, pos)
            raw = data[pos:pos + length]
            pos += length
            if field_num == 1:
                result['secret_b32'] = base64.b32encode(raw).decode().rstrip('=')
            elif field_num == 2:
                result['name'] = raw.decode('utf-8', errors='replace')
            elif field_num == 3:
                result['issuer'] = raw.decode('utf-8', errors='replace')
        elif wire_type == 0:
            val, pos = _read_varint(data, pos)
            if field_num == 4:
                result['algorithm'] = val
            elif field_num == 5:
                result['digits'] = val
            elif field_num == 6:
                result['type'] = val
        else:
            break

    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python tools/totp_extractor.py "otpauth-migration://offline?data=..."')
        sys.exit(1)

    uri = sys.argv[1]
    accounts = decode_migration_uri(uri)

    for i, acct in enumerate(accounts):
        print(f"\n--- Account {i + 1} ---")
        print(f"  Name:    {acct['name']}")
        print(f"  Issuer:  {acct['issuer']}")
        print(f"  Secret:  {acct['secret_b32']}")
        print(f"  Type:    {'TOTP' if acct['type'] == 2 else 'HOTP' if acct['type'] == 1 else acct['type']}")
