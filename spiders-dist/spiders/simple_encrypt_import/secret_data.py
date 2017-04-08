#######################################################
# secret code below
#######################################################
# secret data for berlox.py and parse_minfin.py
# Don't forget add file to  .git/info/exclude
from datetime import datetime

# --------- data for berlox ----------------------
baseKey = bytes([50, 232, 91, 57, 68, 103, 172, 76, 226, 16, 81, 41, 150, 254, 73, 60,
                 41, 236, 155, 160, 223, 163, 197, 59, 19, 228, 70, 20, 21, 162, 214, 15])
Vector = bytes([144, 122, 107, 210, 49, 159, 207, 63, 152, 153, 248, 238, 19, 100, 188, 178])
# I don't know why it present in original code
DefaultKey = bytes([240, 87, 127, 144, 28, 0, 79, 53, 169, 114, 208, 54, 226, 236, 255, 87,
                     58, 106, 152, 26, 49, 1, 41, 242, 94, 225, 134, 204, 143, 107, 193, 149])
def current_key():
    month = datetime.utcnow().month
    year = datetime.utcnow().year
    key = bytearray(baseKey)
    key[month] =  year % ( 128 + month)
    return bytes(key)

# ------------------ data for parse_minfin ---------------
def bid_to_payload(bid: str) -> tuple:
    # early in 2016 str(int(bid)+1)
    payload = {'action' : 'auction-get-contacts', 'bid' : str(int(bid)+2), 'r' : 'true'}
    data = {'action': 'auction-get-contacts', 'bid': bid, 'r': 'true'}
    return payload, data
# ===============================================