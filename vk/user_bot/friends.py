# да-да, я знаю про повтор кода, отстань
from .utils import find_mention_by_message, get_plural
from lib.microvk import VkApiResponseException
from time import sleep
from . import dlp, ND


@dlp.register('+др', '+друг', '-др', '-друг', receive=True)
def change_friend_status(nd) -> str:
    user_id = find_mention_by_message(nd.msg, nd.vk)
    if user_id:
        if nd.msg['command'].startswith('-др'):
            try:
                status = nd.vk('friends.delete', user_id=user_id)
                if status.get('friend_deleted'):
                    msg = "💔 Пользователь удален из друзей"
                elif status.get('out_request_deleted'):
                    msg = "✅ Отменена исходящая заявка"
                elif status.get('in_request_deleted'):
                    msg = "✅ Отклонена входящая заявка"
                elif status.get('suggestion_deleted'):
                    msg = "✅ Отклонена рекомендация друга"
                else:
                    msg = "❗ Произошла ошибка"
            except VkApiResponseException as e:
                msg = f"❗ Произошла ошибка VK №{e.error_code} {e.error_msg}"
        else:
            try:
                status = nd.vk('friends.add', user_id=user_id,
                               text=nd.msg['payload'])
                if status == 1:
                    msg = "✅ Заявка отправлена"
                elif status == 2:
                    msg = "✅ Заявка принята"
                else:
                    msg = "✅ Заявка отправлена повторно"
            except VkApiResponseException as e:
                if e.error_code == 174:
                    msg = "🤔 Ты себя добавить хочешь?"
                elif e.error_code == 175:
                    msg = "❗ Ты в ЧС данного пользователя"
                elif e.error_code == 176:
                    msg = "❗ Пользователь в ЧС"
                else:
                    msg = f"❗ Ошибка: {e.error_msg}"
    else:
        msg = "❗ Необходимо пересланное сообщение или упоминание"
    nd.vk.msg_op(2, nd[3], msg, nd[1])
    return "ok"


@dlp.register('+чс', '-чс', receive=True)
def ban_user(nd):
    user_id = find_mention_by_message(nd.msg, nd.vk)
    if user_id:
        if nd.msg['command'] == '+чс':
            try:
                if nd.vk('account.ban', owner_id = user_id) == 1:
                    msg = '😡 Забанено'
            except VkApiResponseException as e:
                if e.error_msg.endswith('already blacklisted'):
                    msg = '❗ Пользователь уже забанен'
                else: msg = f'❗ Ошиб_очка: {e.error_msg}'
        else:
            try:
                if nd.vk('account.unban', owner_id = user_id) == 1:
                    msg = '💚 Разбанено'
            except VkApiResponseException as e:
                if e.error_msg.endswith('not blacklisted'):
                    msg = '👌🏻 Пользователь не забанен'
                else: msg = f'❗ Ошиб_очка: {e.error_msg}'
    else:
        msg = "❗ Необходимо пересланное сообщение или упоминание"
    nd.vk.msg_op(2, nd[3], msg, nd[1], delete = 1)
    return "ok"


@dlp.register('амнистия')
def unban_all(nd: ND):
    not_all = True
    banned = []
    for i in range(5):
        banned.extend(nd.vk('account.getBanned', count = 200, offset = i*200)['items'])
        if len(banned) == 0:
            return nd.msg_op(2, '👍🏻 Черный список и так пуст')
        if len(banned) % 200 != 0: break
        sleep(0.5)
    nd.msg_op(2, f'⏳ {len(banned)} пользовател' +
              get_plural(len(banned), 'ь будет разбанен', 'я будут разбанены', 'ей будут разбанены') +
              ('\nВозможно, потребуется много времени' if len(banned) > 20 else ''))
    
    for user in banned:
        nd.vk('account.unban', owner_id = user)
        sleep(10)
    
