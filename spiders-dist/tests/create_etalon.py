import pickle
import requests

from common import DATA_PATH, url_to_file

for url, file_name in url_to_file.items():
    with open(DATA_PATH + file_name, 'wb') as f:
        data = requests.get(url)
        pickle.dump(data, f)
