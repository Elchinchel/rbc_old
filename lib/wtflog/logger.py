from datetime import datetime
from .writer import write
import os


_wardens = {}


def get_boy_for_warden(warden_name: str, name: str) -> 'ErrandBoy':
    return _wardens[warden_name].get_boy(name)


def create_warden(warden_name: str, filename: str, format_string: str = False,
                  level: int = 2, name: str = '', printing: bool = False,
                  clear_on_start: str = False) -> 'Warden':
    warden = Warden()
    warden.setup(
        os.path.join(os.getcwd(), filename), format_string,
        level, name, printing, clear_on_start
    )
    _wardens.update({warden_name: warden})


class Warden:
    path: str
    format_string: str = '%(time)s | %(level)s (%(name)s)'
    name: dict
    level: int
    printing: bool

    USELESS = 0
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5

    def setup(self, path, format_string: str = False,
              level: int = 2, name: str = '',
              printing: bool = False, clear_on_start: str = False):
        self.path = path
        if clear_on_start:
            self._clear_log(clear_on_start)
        self.level = level
        self.printing = printing
        if format_string:
            self.format_string = format_string
        return self.get_boy(name)

    def get_boy(self, name):
        return ErrandBoy(self, name)

    def format_log(self, text, name, level):
        time = datetime.now().replace(microsecond=0)
        return f"{self.format_string % {'time': time, 'name': name, 'level': level}} {text}"  # noqa

    def _clear_log(self, clear_on_start):
        if clear_on_start == 'backup':
            try:
                with open(self.path + '.backup', 'w', encoding='utf-8') as backup:
                    with open(self.path, 'r', encoding='utf-8') as log:
                        data = log.read(1024)
                        while data:
                            data = log.read(1024)
                            backup.write(data)
            except FileNotFoundError:
                pass
        try:
            os.remove(self.path)
        except FileNotFoundError:
            pass


class ErrandBoy:
    __name: str
    __warden: Warden

    def __init__(self, warden, name):
        self.__warden = warden
        self.__name = name

    def __call__(self, text):
        return self.info(text)

    def _write(self, line):
        write(self.__warden.path, line)
        if self.__warden.printing:
            print(line)

    def useless(self, text):
        if self.__warden.level == 0:
            self._write(self.__warden.format_log(text, self.__name, 'USELESS'))

    def debug(self, text):
        if self.__warden.level <= 1:
            self._write(self.__warden.format_log(text, self.__name, 'DEBUG'))

    def info(self, text):
        if self.__warden.level <= 2:
            self._write(self.__warden.format_log(text, self.__name, 'INFO'))

    def warning(self, text):
        if self.__warden.level <= 3:
            self._write(self.__warden.format_log(text, self.__name, 'WARNING'))

    def error(self, text):
        if self.__warden.level <= 4:
            self._write(self.__warden.format_log(text, self.__name, 'ERROR'))

    def critical(self, text):
        if self.__warden.level <= 5:
            self._write(self.__warden.format_log(text, self.__name, 'CRITICAL'))  # noqa


warden = Warden()
