# не хочу об этом разговаривать...
from sys import platform
from typing import Any, Callable, Dict
from lib.common_utils import parse_text
from database import VkDB
from lib.microvk import VkApi
from .utils import parseByID
from lib.wtflog import get_boy_for_warden

logger = get_boy_for_warden('LP', 'Обработчик команд LP')


class _Args(list):
    def get(self, index: int, default: Any = None):
        try:
            return self.__getitem__(index)
        except IndexError:
            return default


class ND:
    update: list

    db: VkDB
    vk: VkApi
    time: float
    args: _Args
    msg: dict

    def __init__(self, update, db: VkDB, vk: VkApi, time, msg):
        self.update = update
        self.db = db
        self.vk = vk
        self.time = time
        self.msg = msg

    def __getitem__(self, key):
        return self.update[key]

    def __setitem__(self, key, value):
        self.update[key] = value

    def parse_text(self, text: str):
        text = text.replace('<br>', '\n')
        cmd, args, payload = parse_text(text, False)
        self.set_msg({
            'payload': payload,
            'command': cmd,
            'text': text,
            'args': args
        })

    def set_msg(self, msg):
        self.msg = msg
        self.args = _Args(msg['args'])

    def msg_op(self, mode, text: str = '', **kwargs):
        '1 - новое сообщение, 2 - редактирование, 3 - удаление для всех'
        if type(mode) is str:
            text = mode
            mode = 2
        msg_id = self[1] if mode in {2, 3, 4} else 0
        self.vk.msg_op(mode, self[3], text, msg_id, **kwargs)

    def delete_and_send(self, text: str = '', **kwargs: dict):
        return self.vk('execute', code="""
        API.messages.delete({"message_id":%d,"delete_for_all":1});
        return API.messages.send({
            "peer_id":%d,"message":"%s", "random_id":0
        } + %s);
        """ % (self[1], self[3], text, kwargs))


# TODO: защитить переменные
commands_functions: Dict[str, Callable] = {}
commands_list = set()

parse_text_only = set()
receive_message = set()


def register(*args, receive=False):
    '''Присваивает декорируемой функции указанную команду\n
    Выполняется, если первое слово в нижнем регистре полностью
    соответствует команде'''
    logger.debug(f'Зарегистрирована новая функция. Команды: ({args})')

    def registrator(func):
        for arg in args:
            if arg in commands_functions:
                logger.warning(f'Перезапись команды {arg}!')
            commands_functions.update({arg: func})
            commands_list.add(arg)
            if receive:
                receive_message.add(arg)
        return func
    return registrator


def wrap_handler(wrapper: Callable):
    'Обернутой функции передаются все результаты вызова wrapper(event)'
    def wrapper_(func):
        logger.debug(f'Зарегистрирована новая обертка {wrapper.__name__} для функции {func.__name__}')  # noqa

        def handler(event):
            data = wrapper(event)
            if data is None:
                return
            if type(data) == tuple:
                return func(*data)
            return func(data)
        return handler
    return wrapper_


# TODO: сделать дерево слов
def launch(update, db, vk, time, msg=None):
    'Запускает выполнение команды, если она есть в списке зарегистрированных'
    nd = ND(update, db, vk, time, msg)
    words = nd[5].replace('<br>', ' ').split(' ', 3)
    name = msg['command'] if msg else words[0]

    def run(name: str, next_depth: int):
        if name in commands_list:
            logger(f'Выполняю команду "{name}"')
            if name in receive_message:
                nd.set_msg(msg or parseByID(vk, update[1], 1))
            else:
                nd.parse_text(nd[5])
            return commands_functions[name](nd)
        elif len(words) > next_depth:
            # name = name + ' ' + ' '.join(words[1:next_depth+1])
            # if next_depth < 2:
            #     run(name, next_depth + 1)
            run(name + ' ' + words[1], 100)
    run(name, 1)


def print_info():
    funcs = []
    for func in commands_functions.items():
        if func[1] not in funcs:
            funcs.append(func[1])
    if platform == 'linux':
        print(f"\x1b[33mЗарегистрировано функций: \x1b[31;1m{len(funcs)}\n\x1b[0m\x1b[33mКоманд: \x1b[31;1m{len(commands_list)}\x1b[0m")  # noqa
    else:
        print(f"Зарегистрировано функций: {len(funcs)}\nКоманд: {len(commands_list)}")  # noqa
    del(funcs)
