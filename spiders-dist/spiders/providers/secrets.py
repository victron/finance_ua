import os
import logging
logger = logging.getLogger(__name__)

env_secret = "secret_api"
try:
    apikey = os.environ[env_secret]
except KeyError as key_err:
    logger.error(f"no environment {env_secret}")
    raise key_err
except Exception as e:
    logger.error(f"unknown error")
    raise e
