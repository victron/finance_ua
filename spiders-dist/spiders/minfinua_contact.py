import requests
import pickle
import logging
import threading
from time import sleep

# for virtual framebuffer
# from pyvirtualdisplay import Display
from selenium import webdriver
# need to set firefox path to binary
# from selenium.webdriver.firefox.firefox_binary import FirefoxBinary


from spiders.mongo_start import data_active


logger = logging.getLogger(__name__)
firefox__path = '/usr/bin/firefox'
geckodriver = './bin/geckodriver'
chromedriver = './bin/chromedriver'

browser_life_time = 15
browser_session = None

# currently not used after migration on selenium
def prepare_request(doc: dict):
    try:
        match = {'currency': doc['currency'], 'operation': doc['operation'], 'session': True}
    except KeyError as e:
        logger.error('wrong input doc= {}'.format(e))
        raise KeyError(e)

    projection = {'_id': False, 'url': True, 'cookies': True}
    session = data_active.find_one(match, projection)
    logger.debug('session parameters from db= {}'.format(session))
    return session


def get_contacts(bid: str, data_func, session_parm: dict) -> requests:
    """

    :param bid:
    :param data_func:
    :param session_parm: get session parameters, such as 'Referer', 'cookies'
    :param content_json: return in json format
    :return: response or serialized json
    """
    # --------- curl method -----------------
    # url_get_contacts = 'http://minfin.com.ua/modules/connector/connector.php?action=auction-get-contacts&bid=' \
    #                    + str(int(bid) + 1) + '&r=true'
    # form_urlencoded = 'bid=' + bid + '&action=auction-get-contacts&r=true'
    # header_Content_Type = 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8'
    # if proxy == None:
    #     curl(url_get_contacts, '-c', cookies_file, '-b', cookies_file,  '--user-agent', user_agent, '-X', 'POST', '-e', url,
    #          '-d', form_urlencoded, '-H', header_Content_Type)
    # else:
    #     curl(url_get_contacts, '-c', cookies_file, '-b', cookies_file,  '--user-agent', user_agent, '-X', 'POST', '-e', url,
    #          '-d', form_urlencoded, '-H', header_Content_Type, '-x', proxy)
# ---------------------------------------------

    # ---------- requests ---------------------
    # at that moment successful responce on
    # http -f POST "http://minfin.com.ua/modules/connector/connector.php?action=auction-get-contacts&bid=25195556&
    # r=true" bid=25195555 action=auction-get-contacts r=true 'Cookie: minfincomua_region=1' 'Referer: http://minfin.com.ua/currency
    # /auction/usd/sell/kiev/?presort=&sort=time&order=desc'
    # global cook
    form_urlencoded = 'http://minfin.com.ua/modules/connector/connector.php'
    payload, data = data_func(bid)
    headers = {'user-agent': 'Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)'}
    headers.update({'Referer': session_parm['url']})

    # headers.update({'Cookie': 'minfincomua_region=1'})
    responce = requests.post(form_urlencoded, params=payload, headers=headers, data=data,
                             cookies=pickle.loads(session_parm['cookies']))
    if responce.status_code != 200:
        logger.error('wrong responce from minfin= {}'.format(responce.status_code))
        logger.error('request params; url= {}, params= {}, headers= {}, data= {}'
                     .format(form_urlencoded, payload, headers, data))
        raise ValueError

    # if content_json == False:
    logger.debug('minfin responce= {}'.format(responce.json()))
    return responce.json()
    # else:
    #     logger.info('minfin answer= {}'.format(responce.content))
    #     return responce.content
    # # return r.json()['data']


class Browser:
    def __init__(self):
        # self.display = Display(visible=0, size=(800, 600))
        # try:
        #     self.display.start()
        # except Exception as e:
        #     logger.error('X virtual framebuffer server problem; {}'.format(e))
        #     raise ModuleNotFoundError(e)
        self.currency, self.operation, self.city = None, None, None
        options = webdriver.ChromeOptions()
        # http://peter.sh/experiments/chromium-command-line-switches/
        options.add_argument('--headless')
        options.add_argument('--disable-logging')
        options.add_argument('--disable-pinch')
        # binary = FirefoxBinary(firefox__path)
        # self.browser = webdriver.Firefox(firefox_binary=binary, executable_path=geckodriver)
        self.browser = webdriver.Chrome(chromedriver, chrome_options=options)
        self.browser.implicitly_wait(3)
        url = self.browser.command_executor._url
        session_id = self.browser.session_id
        logger.debug('browser started url= {}, session_id= {}'.format(url, session_id))
        self.timeout = browser_life_time

    def load_page(self, currency, operation, city):
        if (self.currency, self.operation, self.city) != (currency, operation, city):
            url = 'http://minfin.com.ua/currency/auction/' + currency + '/' \
                                                            + operation + '/' \
                                                            + city
            self.browser.get(url)
            logger.info('loaded page url= {}'.format(url))
            self.currency, self.operation, self.city = currency, operation, city


    def get_contact(self, bid: str) -> str:
        logger.debug('start search bid= {}'.format(bid))
        try:
            element = self.browser.find_element_by_xpath("//div/span/a[@data-bid-id='" + bid + "']")
        except:
            logger.warning('bid= {} not in hidden'.format(bid))
        else:
            element.click()
        finally:
            try:
                element_after = self.browser.find_element_by_xpath("//div[@data-bid='" + bid + "']")
            except:
                logger.error('bid= {}, not found'.format(bid))
                return 'Not found'
        contact = element_after.find_element_by_class_name('is-shown').text
        logger.info('contact= {}'.format(contact))
        self.timeout = browser_life_time
        logger.debug('set timeout= {}'.format(self.timeout))
        return contact

    def quit(self):
        self.browser.quit()
        logger.debug('browser exited')


def browser_closer(object: Browser):
    while object.timeout >= 0:
        logger.debug('timeout= {}; decrement 1'.format(object.timeout))
        sleep(60)
        object.timeout -= 1
        logger.debug('timeout= {}'.format(object.timeout))
    logger.info('quit from browser; timeout= {}'.format(object.timeout))
    object.quit()



def return_contact(bid: str, currency='usd', operation='sell', city='kiev') -> str:
    global browser_session
    if browser_session is None:
        browser = Browser()
        browser_session = browser
        thread = threading.Thread(target=browser_closer, args=(browser,))
        thread.start()
    else:
        browser = browser_session

    browser.load_page(currency, operation, city)
    contact = browser.get_contact(bid)
    # browser.quit()
    return contact