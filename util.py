import logging
from logging import Formatter, getLogger, StreamHandler

class Color(object):
    """
     utility to return ansi colored text.
    """

    colors = {
        'black': 30,
        'red': 31,
        'green': 32,
        'yellow': 33,
        'blue': 34,
        'magenta': 35,
        'cyan': 36,
        'white': 37,
        'bgred': 41,
        'bggrey': 100
    }

    prefix = '\033['

    suffix = '\033[0m'

    def colored(self, text, color=None):
        if color not in self.colors:
            color = 'white'

        clr = self.colors[color]
        return (self.prefix+'%dm%s'+self.suffix) % (clr, text)


colored = Color().colored

class ColoredFormatter(Formatter):

    def format(self, record):

        message = record.getMessage()

        mapping = {
            'INFO': 'cyan',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bgred',
            'DEBUG': 'bggrey',
            'SUCCESS': 'green'
        }

        clr = mapping.get(record.levelname, 'white')

        return colored(record.levelname, clr) + ': ' + colored(message,clr)


'''
    Logging을 위해 각 파일에서 import하여 사용
'''
Logger=logging.getLogger(__name__)

'''
    Logger의 Logging Level 설정
    Logger의 색을 설정 
    
    각 py 파일에서
     logger=util.get_colorized_logger(__name__) 
     logger.info("~~~~")
     logger.error("~~~")
    형태로 logger 사용

'''
def init_logger(level=logging.INFO):

    global Logger

    Logger.setLevel(level)
    handler = StreamHandler()
    formatter = ColoredFormatter()
    handler.setFormatter(formatter)
    Logger.addHandler(handler)

    # set success level
    logging.SUCCESS = 25  # between WARNING and INFO
    logging.addLevelName(logging.SUCCESS, 'SUCCESS')
    setattr(Logger, 'success', lambda message, *args: Logger._log(logging.SUCCESS, message, args))

'''
    FLAGS 출력
'''
def log_args(FLAGS):
    Logger.info("\tParameters:")
    for attr, value in sorted(vars(FLAGS).items()):
        Logger.info("\t\t{}={}".format(attr.upper(), value))
    Logger.info("")


