import logging
import logging.config
import os
import sys
# from . import parse_minfin
# from . import check_proxy
# from . import filters

import yaml
# import logging.config
logging_config = os.path.join(sys.prefix, '.spiders', 'logging.yml')
try:
    logging.config.dictConfig(yaml.load(open(logging_config, 'r')))
except FileNotFoundError:
    # for testing, (working directory 'tests')
    logging.config.dictConfig(yaml.load(open('../config/logging.yml', 'r')))