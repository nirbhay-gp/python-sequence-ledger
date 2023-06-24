import hashlib
import json

def md5(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()

def map_to_tuple(data):
    return str(
        data['id'],
        data['from'],
        data['to'],
        data['amount'],
        data['currency'])

def map_to_md5(data):
    return (
        hashlib.md5(map_to_tuple(data).encode('utf-8')).hexdigest()
    )