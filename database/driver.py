import os
import json
import time
from typing import List
from lib.microvk import VkApi
from .client import method
from .data_classes import Settings, Account
from .billing_manager import vk_users
from lib.wtflog import get_boy_for_warden

logger = get_boy_for_warden('DB', 'Драйвер базы даннных')

_root_path = os.path.dirname(__file__)


def _reader(rel_path):
    with open(os.path.join(_root_path, f'{rel_path}.json'), 'r', encoding="utf-8") as data:
        return json.loads(data.read())


def _saver(rel_path, data_):
    with open(os.path.join(_root_path, f'{rel_path}.json'), 'w', encoding="utf-8") as data:
        data.write(json.dumps(data_, ensure_ascii=False, indent=2))


try:
    general_data = _reader('general')
except FileNotFoundError:
    _saver('general', {
        "owner_id": 0,
        "admins": [],
        "moderators": [],
        "group_token": "",
        "group_id": 0,
        "warnings": []
    })
    general_data = _reader('general')

owner_id: int = general_data['owner_id']
admins: List[int] = general_data['admins']
moderators: List[int] = general_data['moderators']

group_token = general_data['group_token']

group_id = general_data['group_id']

warns: List[str] = general_data['warnings']


def save_general() -> None:
    _saver('general', general_data)


def set_warn_list(warn_list: list) -> None:
    global warns
    general_data['warnings'] = warn_list
    warns = general_data['warnings']
    save_general()


class VkDB:
    user_id: int
    access_token: str
    me_token: str
    secret: str

    method = method

    def __init__(self, uid):
        user_data = method.get_tokens(uid)
        self.user_id = uid
        self.access_token = user_data['access_token']
        self.me_token = user_data['me_token']

    def token_set(self, token: str, vkme: bool = False):
        if vkme:
            method.update_token(self.user_id, me_token=token)
            self.me_token = token
        else:
            method.update_token(self.user_id, access_token=token)
            self.access_token = token

    def settings_get(self) -> Settings:
        data = method.get_settings(self.user_id)
        return Settings(data)

    def settings_set(self, settings: Settings):
        method.update_settings(self.user_id, settings)

    def account_get(self) -> Account:
        data = method.get_account(self.user_id)
        return Account(data)

    def account_set(self, account):
        method.update_account(self.user_id, account)

    def template_get(self, type_: str, name: str = '', category: bool = False, all_: bool = False):
        templates = method.get_templates(self.user_id, type_)
        name = name.lower()
        if category:
            if all_:
                temps = {}
                for template in templates:
                    temps.update({
                        template['category']: temps.get(template['category'], 0) + 1
                        })
            else:
                temps = []
                for template in templates:
                    if template['category'] == name:
                        temps.append(template)
            return temps
        else:
            if all_:
                return templates
            else:
                for template in templates:
                    if template['name'].lower() == name.lower():
                        return template
        return None

    def template_delete(self, type_, name):
        'Возвращает True в случае успеха'
        return method.remove_template(self.user_id, type_, {'name': name})

    # TODO: убрать или реализовать
    def template_rename_category(self, type_, new_name, old_name):
        'Возвращает "taken", "not exist" или None в случае успеха'
        templates = _reader(f'templates/{self.user_id}/{type_}')
        exist = False
        for template in templates:
            if template['category'] == old_name:
                exist = True
            if template['category'] == new_name:
                return 'taken'
        if not exist:
            return 'not exist'
        # append({
        #     'type': 'rename_temp_cat',
        #     'uid': self.user_id,
        #     'new_name': new_name,
        #     'old_name': old_name,
        #     'templates': templates
        # })

    def template_create(self, name, attachments=[], payload='',  # noqa
                        category='', animation=False):
        'Возвращает True, если шаблон уже существует и будет перезаписан'
        if category in {'', 'все'}:
            category = 'без категории'
        if not animation:
            type_ = 'common'
            if type(attachments) == str:
                if attachments.startswith('audio_message'):
                    type_ = 'voice'
            if category.startswith('___binded___'):
                type_ = 'binded'
            elif category.startswith('___dutys___'):
                type_ = 'dutys'
        else:
            type_ = 'anim'
        if type_ == 'common':
            data = {
                    'name': name,
                    'category': category,
                    'text': payload,
                    'attachments': ','.join(attachments)
                    }
        elif type_ == 'voice':
            data = {
                    'name': name,
                    'category': category,
                    'attachments': attachments
                    }
        elif type_ == 'binded':
            data = {
                    'name': name,
                    'peer_id': int(category.replace('___binded___', '')),
                    'text': payload
                    }
        elif type_ == 'dutys':
            data = {
                    'name': name,
                    'text': payload
                    }
        return method.set_template(self.user_id, type_, data)  # type: ignore


def add_user(uid):
    method.add_user(uid)


def remove_user(uid):
    method.remove_user(uid)


def DB_init():
    def refactor(user):
        acc = Account(method.get_account(user))
        acc.added_by = 332619272
        method.update_account(user, acc)
        pass
    vk_users.clear()
    users = method.start()
    if not users:
        print("Похоже, это первый запуск сервера")
        setted = False
        while not setted:
            try:
                token = input("Токен первого пользователя: ")
                uid = VkApi(token, raise_excepts=True)('users.get')[0]['id']
                method.add_user(uid)
                method.update_token(uid, access_token=token)
                acc = Account(method.get_account(uid))
                acc.vk_longpoll = True
                method.update_account(uid, acc)
                setted = True
            except Exception as e:
                print(f"Ошибка {e}, еще раз...")
        print('Дальнейшая настройка производится через VK')
        time.sleep(3)
        users = method.start()
    for user in users:
        # refactor(user)
        print(user)
        vk_users.append(user)


DB_init()
