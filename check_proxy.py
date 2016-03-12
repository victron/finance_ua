import requests
from parameters import proxies

# TODO:
# - check connectivity with internet

url = 'http://google.com'
try:
    responce_get = requests.get(url, timeout=3)
    proxy_is_used = False
except requests.exceptions.ConnectTimeout:
    responce_get = requests.get(url, proxies=proxies)
    proxy_is_used = True

if __name__ == '__main__':
    print('proxy_is_used = {}'.format(proxy_is_used))
