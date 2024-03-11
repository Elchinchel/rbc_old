# согласен, пиздец полный
import re
from asyncio import sleep
from random import choice
from typing import List, Tuple

from database.driver import owner_id, set_warn_list, warns
from database.client import method
from database.data_classes import Account
from vk.user_bot.service import reload_queue, kill_queue
from lib.vkmini import VkApi, VkResponseException
from lib.vkmini.group_longpoll import Update

pings_chat: List[List[Tuple[str, int]]] = [
    [('ОГО, ОБОСРАТЬСЯ, ЕЩЕ ОДИН ПИНГ, ТЕПЕРЬ У НАС БЛЯДЬ ТРИ СУКА ПИНГА', 0), ('', 163)],
    [('Hfyljvbpbhetv gbyu///', 0), ('Бля, раскладкой ошибся...', 0), ('', 17675)],
    [('', 11247)],
    [('', 12925)],
    [('', 18683)]
]

pings_private = [
    [('Ну понг, че', 0)]
]


async def check_for_tokens(update: Update, group_id: int):  # noqa
    async def edit_msg(api: VkApi, msg: dict, text: str) -> bool:
        for msg_ in (await api('messages.getHistory',
                               peer_id=0-group_id, count=200))['items']:
            if msg_['conversation_message_id'] == msg['conversation_message_id']:  # noqa
                try:
                    await api.msg_op(2, msg_['peer_id'], text, msg_['id'])
                    return True
                except VkResponseException:
                    return False

    async def check_text(text: str) -> Tuple[str, bool, VkApi]:
        for match in re.findall(r'[a-z0-9]{85}', text):
            try:
                api = VkApi(match, excepts=True)
                if 'vk.me' in (await api('messages.getLongPollServer'
                                         ))['server']:
                    return match, True, api
                else:
                    return match, False, api
            except VkResponseException:
                continue
        return '', False, VkApi

    token = metoken = ''

    token_, is_me, api = await check_text(update.message.text)
    for fmsg in update.message.fwd_messages:
        if token_:
            break
        token_, is_me, api = await check_text(fmsg['text'])
    if token_:
        if is_me:
            if await edit_msg(api, update.object['message'],
                              '🔧 Обнаружен токен VkMe'):
                metoken = token_
            else:
                return await update.reply_to_peer(
                    'Это не твой токен, либо отсутствует доступ к сообщениям'
                )
        else:
            if await edit_msg(api, update.object['message'],
                              '⚙️ Обнаружен токен НЕ VkMe'):
                token = token_
            else:
                return await update.reply_to_peer(
                    'Это не твой токен, либо отсутствует доступ к сообщениям'
                )
        if not method.is_user(update.message.peer_id):
            return await update.reply_to_peer('Ты кто вообще такой?')
        try:
            method.update_token(update.message.peer_id,
                                access_token=token, me_token=metoken)
        except Exception as e:
            await update.reply_to_peer('❗ Что-то пошло не так')
            raise e
        if is_me:
            await sleep(1)
            try:
                await VkApi(
                    method.get_tokens(update.message.peer_id)['access_token'],
                    excepts=True
                )('users.get')
                main = True
            except VkResponseException:
                main = False
            if main:
                msg = '👌🏻 Me токен сохранен'
            else:
                msg = '🤔 Me токен сохранен, но основной токен неактуален'
        else:
            msg = '✅ Запущено!'
        reload_queue.append(update.message.peer_id)
        await update.reply_to_peer(msg)


async def warn_list(update: Update):
    if update.message.text.lower() in {'предупреждения', 'преды'}:
        if not warns:
            await update.reply_to_peer('☑️ Все как будто бы в порядке')
        else:
            await update.reply_to_peer('\n'.join(warns))
    elif (update.message.from_id != owner_id
          if update.message.peer_id > 2e9 else
          update.message.peer_id != owner_id):
        return
    elif update.lowered.startswith('+пред'):
        message = update.message.text[5:]
        if not message:
            return await update.reply_to_peer('❗️ Нет текста')
        warns.append(message)
        set_warn_list(warns)
        await update.reply_to_peer('☑️ Добавлено')
    elif update.lowered.startswith('-пред'):
        message = update.message.text[5:]
        if not message:
            return await update.reply_to_peer('❗️ Нет текста')
        if message in warns:
            warns.remove(message)
            set_warn_list(warns)
            await update.reply_to_peer('☑️ Удалено')
        else:
            await update.reply_to_peer('❗️ Не нашел')


goodbyes = {'споки', 'спокойной ночи', 'пока', 'выключи'}
greetings = {'утречка', 'доброе утро', 'привет', 'включи'}


async def switch_state(update: Update, on: bool):
    uid = update.message.from_id if update.message.peer_id > 2e9 else update.message.peer_id  # noqa
    if not method.is_user(uid):
        return await update.reply_to_peer(
            'А ты, собсна, кто такой вообще?..'
        )
    acc = Account(method.get_account(uid))
    if on:
        acc.vk_longpoll = True
        try:
            VkApi(method.get_tokens(update.message.peer_id)['access_token'],
                  excepts=True)('users.get')
            await sleep(0.5)
            reload_queue.append(uid)
            msg = '💚 Запущено!'
        except VkResponseException:
            msg = '😒 Токен инвалид...'
    else:
        acc.vk_longpoll = False
        kill_queue.append(uid)
        msg = '😴 Выключаю...'
    method.update_account(uid, acc)
    await update.reply_to_peer(msg)


async def ping(update: Update):
    if update.message.peer_id > 2e9:
        arg_list = choice(pings_chat)
    else:
        arg_list = choice(pings_private)

    for args in arg_list:
        await update.reply_to_peer(args[0], sticker_id=args[1])
