import os
from vk.user_bot import driver as dlp

ND = dlp.ND


def init(path: str, alter_path: str = ''):
    if alter_path != '' and not alter_path.startswith('.'):
        alter_path = '.' + alter_path
    for name in os.listdir(path):
        if name in {'__init__.py', '__pycache__'}:
            continue
        ext = name.split('.')
        if len(ext) > 1:
            ext = ext[-1]
        else:
            if alter_path == '':
                init(os.path.join(path, name), ext[0])
            else:
                init(os.path.join(path, name), f"{alter_path}.{ext[0]}")
            continue
        if ext == 'py':
            name = name.replace('.py', '')
            exec(f"from {alter_path}.{name} import __name__")


init(os.path.dirname(__file__))

from .settings import sets
from .service import service_commands
