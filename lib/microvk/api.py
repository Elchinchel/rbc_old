
# давай вот щас не начинай, работает, а больше мне ничего не нужно
import requests
from .methods import Messages
from time import sleep
from html import escape

from lib.wtflog import warden
logger = warden.get_boy('VK API')


class VkApiResponseException(Exception):  # да, спиздил))0)
    def __init__(self, *args, **kwargs):
        self.error_code = kwargs.get('error_code', None)
        self.error_msg = kwargs.get('error_msg', None)
        self.request_params = kwargs.get('request_params', None)

        self.args = args
        self.kwargs = kwargs


class VkApi:
    url: str = 'https://api.vk.com/method/'
    query: str
    raise_excepts: bool

    messages = Messages

    def __init__(self, access_token: str, raise_excepts: bool = False, version: str = "5.110"):
        'raise_excepts - если True, ошибки ВК будут вызывать исключения'
        self.query = f'?v={version}&access_token={access_token}&lang=ru'
        self.raise_excepts = raise_excepts

    def __call__(self, method, **kwargs):
        logger.debug(f'URL = "{self.url}{method}{self.query}" Data = {kwargs}')
        r = requests.post(f'{self.url}{method}{self.query}', data = kwargs)
        if r.status_code == 200:
            r = r.json()
            if 'response' in r.keys():
                logger.info(f"Запрос {method} выполнен")
                return r['response']
            elif 'error' in r.keys():
                logger.warning(f"Запрос {method} не выполнен: {r['error']}")
                if self.raise_excepts:
                    raise VkApiResponseException(**r["error"])
            return r
        elif self.raise_excepts:
            raise Exception('networkerror')

    def method(self, method, **kwargs):
        return self.__call__(method, **kwargs)

    def msg_op(self, mode: int, peer_id: str = 0, message = '', msg_id = '', delete: float = 0, delete_id: int = 0, **kwargs):
        '''mode: 1 - отправка, 2 - редактирование, 3 - удаление, 4 - удаление только для себя'''

        if mode == 4:
            mode = 3
            dfa = 0
        else: dfa = 1

        mode = ['messages.send', 'messages.edit', 'messages.delete'][mode - 1]
        
        if delete_id:
            response = self.exe('''API.messages.delete({"message_id":%d,"delete_for_all":1});
            return API.%s({"peer_id":%d,"message":"%s","message_id":%d,"delete_for_all":%d,"random_id":0%s});
            ''' % (delete_id, mode, peer_id, escape(message).replace('\n', '<br>'),
                   msg_id, dfa, kwargs_to_execute(kwargs)))
        else:
            response = self(mode, peer_id = peer_id, message = message,
            message_id = msg_id, delete_for_all = dfa, random_id = 0, **kwargs)

        if mode == 1:
            msg_id = response

        if delete:
            sleep(delete)
            self('messages.delete', message_id = msg_id, delete_for_all = 1)
        return response
            
    def exe(self, code):
        'Метод execute'
        return self('execute', code = code)


def kwargs_to_execute(kwargs: dict) -> str:
    data = ''
    for arg in kwargs:
        if type(kwargs[arg]) == str:
            kwargs[arg] = f'"{kwargs[arg]}"'
        if type(kwargs[arg]) == bool:
            if kwargs[arg]:
                kwargs[arg] = 'true'
            else:
                kwargs[arg] = 'false'
        data += f',"{arg}":{kwargs[arg]}'
    return data