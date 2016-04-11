from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random
import hashlib, random, struct, types, sys
import os
# ----------------- the encrypted file name -------------
file_with_code = 'secret_data.pye'
# ======================================================
# password = input('please enter password:').encode()
from password import password
key = hashlib.sha256(password).digest()

def deccryp_file(key, in_file, out_file=None, chunksize=64*1024):
    """
    function not in use in module, just for reference
    :param key:  it expects your key to be either 16, 24 or 32 bytes long (for AES-128, AES-196 and AES-256, respectively).
    :param in_file: str, input file name
    :param out_file: str or None, output file name
    :param chunksize: int, chunk size, actualy just for big files
    :return: None
    """
    if not out_file:
        out_file = os.path.splitext(in_file)[0]

    with open(in_file, 'rb') as infile:
        origsize = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
        iv = infile.read(16)
        decryptor = AES.new(key, AES.MODE_CBC, iv)

        with open(out_file, 'wb') as outfile:
            while True:
                chunk = infile.read(chunksize)
                if len(chunk) == 0:
                    break
                outfile.write(decryptor.decrypt(chunk))
            outfile.truncate(origsize)

def decrypt_file_in_mem(key, in_file, chunksize=64*1024):
    # using full path to file
    path = os.path.split(os.path.realpath(__file__))[0] # get head of path
    in_file = os.path.join(path, in_file)

    with open(in_file, 'rb') as infile:
        origsize = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
        iv = infile.read(16)
        check_sum = infile.read(32)
        decryptor = AES.new(key, AES.MODE_CBC, iv)
        out_data = bytes()
        while True:
            chunk = infile.read(chunksize)
            if len(chunk) == 0:
                break
            out_data += decryptor.decrypt(chunk)
        check_sum1 = SHA256.new(out_data[:origsize]).digest()
        if check_sum1 == check_sum:
            return out_data[:origsize].decode('utf-8')
        else:
            raise ValueError('integrity error')


code = decrypt_file_in_mem(key, file_with_code) # now it in memory, and availbale for !!!debuger!!!
code = compile(code, '<string>', mode='exec')
current_module = sys.modules[__name__]
exec(code, current_module.__dict__)

# --------------- it's beteter to make link on real functions for IDE ---
# -------- berlox ------
baseKey = baseKey
Vector = Vector
current_key = current_key
# ------- minfin ----
bid_to_payload = bid_to_payload
# ========================================================================

if __name__ == '__main__':
    file_with_code = 'test_module.pye'
    assert 'test1' in dir(current_module), 'missing test1 function'
    assert 'test2' in dir(current_module), 'missing test2 function'
    assert 'test string' == test1('test string'), 'function not working'
