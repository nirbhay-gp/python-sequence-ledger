import hashlib
import base64
import json
import logging
import os

log = logging.getLogger(__name__)

def sha256(string):
    digest = hashlib.sha256(string.encode('utf-8')).digest()
    return ''.join(format(byte, '02x') for byte in digest)

def match_keys(digest, keys):
    for key in keys:
        if key.get('secret-key-hash') == digest:
            return key
    return None

def authenticate(k, keys):
    log.debug("Matching: %s %s", k, keys)
    key_digest = sha256(k)
    account = match_keys(key_digest, keys)
    return account if account else None

def decode(to_decode):
    try:
        return base64.b64decode(to_decode).decode('utf-8')
    except Exception as e:
        log.error(f"Failed to decode: {e}")
        return None

def remove_colon(s):
    return s[:-1]

def authz_header(context):
    return context.get_in(['request', 'headers', 'authorization'])

def header_key(context):
    header = authz_header(context)
    if header:
        parts = header.split(' ')
        if len(parts) >= 2:
            return decode(parts[1])
    return None

def str_to_map(s):
    try:
        return json.loads(s)
    except Exception as e:
        log.error(f"Failed to parse keys: {e}")
        return None

def apikey_auth(context):
    key = header_key(context)
    if key:
        keys = str_to_map(os.environ.get('keys'))
        if keys:
            customer = authenticate(key, keys)
            if customer:
                log.debug("Got customer: %s", customer)
                return customer
            else:
                log.debug("Invalid credentials")
        else:
            log.warning("Error parsing keys from env")
    else:
        log.debug("Invalid Authz header: %s", authz_header(context))