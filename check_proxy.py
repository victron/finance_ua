import requests
from parameters import proxies
from parameters import headers

# TODO:
# - check connectivity with internet

url = 'http://google.com'
proxy_is_used = False
try:
    responce_get = requests.get(url, timeout=3)
except requests.exceptions.ConnectTimeout:
    responce_get = requests.get(url, proxies=proxies)
    proxy_is_used = True


def proxy_requests(url):
    print('---------proxy_request--------- ')
    if proxy_is_used == False:
        return requests.get(url, headers=headers)
    else:
        return requests.get(url, headers=headers, timeout = 3, proxies=proxies)

if __name__ == '__main__':
    print('proxy_is_used = {}'.format(proxy_is_used))
