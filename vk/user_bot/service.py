from database.data_classes import AccountTG
import re
from time import time as timenow
from typing import Any, Tuple, Dict

from database.driver import add_user, remove_user, owner_id, vk_users, method
from database.billing_manager import recheck
from lib.microvk import VkApi, VkApiResponseException

from database import VkDB
from .templates.life_is_strange import rewinds
from .utils import ExcReload

reload_queue = []
kill_queue = []

vk_lp_running: Dict[int, str] = {}

lp_failed: Dict[int, Dict[str, Any]] = {}  # noqa


# TODO: ПИЗДЕЦ БЛЯДЬ
def service_commands(nd, db: VkDB, vk: VkApi, time):
    if nd[5].startswith('!!связать гс'):
        pid = re.findall(r'(\[id)?(\d+)', nd[5])
        if pid:
            if pid[0][0]:
                pid = int(pid[0][1])
            elif pid[0][1]:
                pid = int(pid[0][1]) + 2000000000
        else:
            pid = nd[3]
        sets = db.settings_get()
        sets.templates_bind = pid
        db.settings_set(sets)
        vk.msg_op(3, nd[3], msg_id=nd[1])


    elif nd[5] == '!!отвязать гс':
        sets = db.settings_get()
        sets.templates_bind = 0
        db.settings_set(sets)
        vk.msg_op(3, nd[3], msg_id=nd[1])


    elif nd[5] == '!!чаты':
        chats = ''
        for chat in vk(vk.messages.getConversations, count = 200)['items']:
            chat = chat['conversation']
            if chat['peer']['type'] == 'chat':
                chats += f"{chat['chat_settings']['title']}\nID: {chat['peer']['id'] - 2000000000}\n\n"
            if len(chats) > 1000:
                break
        vk.msg_op(1, nd[3], chats)

    elif nd[5] == '!!сколько?':
        vk.msg_op(1, nd[3], 'Я один')

    elif nd[5].startswith('!!rewind'):
        rew_id = nd[5][8:].strip()
        if not rew_id or rew_id == 's':
            msg = '🙅‍♀ Список событий, которые можно отменить:\n'
            for rewind in rewinds:
                if rewind.user_id == db.user_id:
                    msg += f'''{rewind.ident}. {rewind.desc} ({
                        round(rewind.expire_time - timenow())}с.)\n'''
            if msg == '🙅‍♀ Список событий, которые можно отменить:\n':
                return
            vk.msg_op(2, nd[3], msg, nd[1])
        elif not rew_id.isdigit:
            vk.msg_op(2, nd[3], '🤔 Давай лучше цифрой (список - !!rewinds)', nd[1])
        else:
            rew_id = int(rew_id)
            for rewind in rewinds:
                if rewind.user_id == db.user_id and rewind.ident == rew_id:
                    rewind()
                    break
            vk.msg_op(2, nd[3], '👌🏻 Отменено', nd[1])

    elif nd[5] == '!!лпрестарт':
        raise ExcReload(vk, pid=nd[3], text='🐗 На подскоке')

    elif nd[5].startswith('!!regtg'):
        uid = int(nd[5][8:])
        method.tg.add_user(uid)
        acc = AccountTG(method.tg.get_account(uid))
        acc.on = True
        method.tg.update_account(uid, acc)
        recheck.set()

    elif nd[5].startswith('!!unregtg'):
        uid = int(nd[5][10:])
        method.tg.remove_user(uid)
        recheck.set()

    elif nd[5] in {'!!findtokens', '!!аштвещлуты', '!!токены'} and db.user_id == owner_id:
        def check_text(text: str) -> Tuple[str, bool, VkApi]:
            for match in re.findall(r'[a-z0-9]{85}', text):
                try:
                    api = VkApi(match, raise_excepts=True)
                    if 'vk.me' in api('messages.getLongPollServer')['server']:
                        return match, True, api
                    else:
                        return match, False, api
                except VkApiResponseException:
                    continue
            return '', False, VkApi

        def edit_msg(api: VkApi, msg: dict, text: str) -> bool:
            for msg_ in api('messages.getHistory', peer_id=owner_id, count=200)['items']:
                if msg_['conversation_message_id'] == msg['conversation_message_id']:
                    try:
                        api.msg_op(2, msg_['peer_id'], text, msg_['id'])
                        return True
                    except VkApiResponseException:
                        return False

        token = ''
        metoken = ''

        for msg in vk('messages.getHistory', peer_id = nd[3], count = 200)['items']:
            if token and metoken: break
            if not msg['out']:
                token_, is_me, api = check_text(msg['text'])
                for fmsg in msg['fwd_messages']:
                    if token_: break
                    token_, is_me, api = check_text(fmsg['text'])
                if token_:
                    if is_me:
                        if edit_msg(api, msg, '🔧 Обнаружен токен VkMe'):
                            metoken = token_
                    else:
                        if edit_msg(api, msg, '⚙️ Обнаружен токен не VkMe'):
                            token = token_
                    token_ = ''
        try:
            method.update_token(nd[3], access_token=token, me_token=metoken)
        except Exception as e:
            return vk.msg_op(2, nd[3], f'❗ Что-то пошло не так: {e}', nd[1])
        if token and metoken:
            msg = '👌🏻 Оба.'
        elif not (token or metoken):
            msg = '❗ Токены не найдены'
        else:
            msg = '👌🏻 Один найден, не VK Me' if token else '👌🏻 Один найден, VK Me'
        vk.msg_op(2, nd[3], msg, nd[1])
        reload_queue.append(nd[3])


    elif nd[5] == '!!тест' and db.user_id == owner_id:
        try:
            VkApi(method.get_tokens(nd[3])['access_token'], raise_excepts=True).msg_op(1, owner_id, 'нд')
        except VkApiResponseException:
            vk.msg_op(2, nd[3], '❗ Неверный основной токен', nd[1])


    elif nd[5] == '!!аня иди нахуй' and db.user_id == owner_id:
        anya = 324036713
        title = vk('messages.getConversationsById', peer_ids=nd[3])['items'][0]['chat_settings']['title']
        vk_ = VkApi(method.get_tokens(anya)['access_token'])
        for conv in vk_('messages.getConversations', count=200)['items']:
            conv = conv['conversation']
            if conv.get('chat_settings', {}).get('title') == title:
                chat = conv['peer']['local_id']
                break
        vk_('messages.removeChatUser', chat_id=chat, member_id=anya)
