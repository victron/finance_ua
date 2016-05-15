# -*- coding: utf-8 -*-
# Установка путей
# import os, sys
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, web_logging
from flask.ext.script import Manager, Server


manager = Manager(app)


# Включение по умолчанию отладчика и перезагрузки
manager.add_command("runserver", Server(
    use_debugger = True,
    use_reloader = True,
    host = '127.0.0.1')
)

if __name__ == "__main__":
    web_logging.debug('start \'manager\'')
    manager.run()

