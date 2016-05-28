import time
import sys
# import logging
from app import mongo_logging


# logging = logging.getLogger(__name__)
logging = mongo_logging

if sys.platform[:3] == 'win':
    timefunc = time.clock
else:
    timefunc = time.time

# from Lutc M.
def timer1(label='', trace=True): # Аргументы декоратора: сохраняются
    class Timer:
        def __init__(self, func):   # На этапе декорирования сохраняется
            self.func = func        # декорируемая функция
            self.alltime = 0
        def __call__(self, *args, **kargs): # При вызове: вызывается оригинал
            start = timefunc()
            result = self.func(*args, **kargs)
            elapsed = timefunc() - start
            self.alltime += elapsed
            if trace:
                format = '%s %s: %.5f, %.5f'
                values = (label, self.func.__name__, elapsed, self.alltime)
                print(format % values)
            return result
    return Timer



def timer(label='[EXE_TIME] >>>>', trace=True):
    # Декоратор с аргументами: сохраняет арг.
    def onDecorator(func):
        # На этапе декорирования @: сохраняет
        # декорируемую функцию
        def onCall(*args, **kargs): # При вызове: вызывает оригинал
            start = timefunc()
            # Информация в области видимости +
            result = func(*args, **kargs) # атрибуты функции
            elapsed = timefunc() - start
            onCall.alltime += elapsed
            if trace:
                template = '{} {}: {:.5f}, {:.5f}'
                values = (label, func.__name__, elapsed, onCall.alltime)
                # print(template.format(*values))
                logging.info(template.format(*values))
            return result
        onCall.alltime = 0
        return onCall
    return onDecorator
