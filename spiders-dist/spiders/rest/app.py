import falcon
import spiders.rest.resources as resourses
import sys
import logging

logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG)
# ----------- const block -------------------------
min_python_version = 3.6

# =================================================

current_python_version = sys.version_info.major + sys.version_info.minor * 0.1
if current_python_version < min_python_version:
    logger.error('python version is == {}, min python version should >= {}'.format(current_python_version,
                                                                                   min_python_version))
    sys.exit(9)


api = application = falcon.API()

command = resourses.Commands()

api.add_route('/command', command)
