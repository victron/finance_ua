# -*- coding: utf-8 -*-
# Установка путей
# import os, sys
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask.ext.script import Manager, Server
from app import app


manager = Manager(app)

# Включение по умолчанию отладчика и перезагрузки
manager.add_command("runserver", Server(
    use_debugger = True,
    use_reloader = True,
    host = '127.0.0.1')
)

if __name__ == "__main__":
    manager.run()

