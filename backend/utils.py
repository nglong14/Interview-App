from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)

def base62_encode(num):
    alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    if num == 0:
        return alphabet[0]
    arr = []
    while num:
        arr.append(alphabet[num % 62])
        num = num // 62
    return ''.join(reversed(arr))