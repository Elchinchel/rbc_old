# Телега сюда очень хуево вписывалась,
# количество говнокода начало неадекватно расти с ее добавлением
# (вообще, наверное, есть надежда на рефакторинг, но чет я не верю уже...)
from typing import List, Union
from database.client import method
from database.data_classes import SettingsTG
from telethon.sessions import StringSession


class TgDB:
    user_id: int
    session: StringSession
    settings: SettingsTG

    def __init__(self, tg_uid: int):
        self.session = StringSession(method.tg.get_session(tg_uid))
        self.settings = SettingsTG(method.tg.get_settings(tg_uid))
        self.settings._deleter_edit = self.settings.deleter + '-'
        self.user_id = tg_uid

    def settings_update(self):
        self.setting = SettingsTG(method.tg.get_settings(self.user_id))
        SettingsTG(method.tg.get_settings(self.user_id))

    def stickers_get(self, name: str = '') -> Union[List[dict], dict, None]:
        stickers = method.tg.stickers_get(self.user_id)
        if name != '':
            for stick in stickers:
                if stick['name'] == name:
                    return stick
            return None
        if stickers == []:
            return None
        return stickers

    def sticker_set(self, sticker: dict) -> Union[dict, None]:
        sticker = method.tg.sticker_set(self.user_id, sticker)
        if sticker['name'] == '':
            return None
        return sticker

    def sticker_remove(self, name: str) -> Union[dict, None]:
        sticker = method.tg.sticker_remove(self.user_id, {'name': name})
        if sticker['name'] == '':
            return None
        return sticker
