import requests

from spiders.parameters import headers
# from spiders.parameters import proxies


# TODO: remove proxy in modules
# need until deleted proxy in all modules
proxy_is_used = False
proxies = ''
# try:
#     responce_get = requests.get(url, timeout=3)
# except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
#     try:
#         responce_get = requests.get(url, proxies=proxies)
#         proxy_is_used = True
#     except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
#         print('!!! no direct connection and wrong proxy {} \nspiders not works!!!'.format(url))
#

def proxy_requests(url):
    print('---------proxy_request--------- ')
    return requests.get(url, headers=headers)

