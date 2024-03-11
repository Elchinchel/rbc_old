from .utils import msg_op, parseByID, find_mention_by_message, parse
from lib.microvk import VkApiResponseException
from . import dlp, ND


@dlp.register('+админ', '-админ', receive=True)
def admin_set(nd: ND):
    uid = find_mention_by_message(nd.msg, nd.vk)
    if uid:
        try:
            if nd.vk('messages.setMemberRole', peer_id = nd[3], member_id = uid,
                     role = 'admin' if nd.msg['command'] == '+админ' else 'member') == 1:
                if uid < 0:
                    return nd.msg_op(3)
                user = nd.vk('users.get', user_ids = uid)[0]
                nd.msg_op(2, f"""✅ Пользователь [id{uid}|{user['first_name']} {user['last_name']}] {'теперь администратор беседы'
                          if nd.msg['command'] == '+админ' else 'снят с должности администратора'}""")
        except VkApiResponseException as e:
            if e.error_code == 15:
                nd.msg_op(2, '❗ Доступ запрещен. Скорее всего, у вас недостаточно прав, чтобы изменять администраторов беседы.')
            else:
                nd.msg_op(2, f'❗ Ошибка VK: {e.error_msg}')
    else:
        nd.msg_op(2, '❗ Необходимо упоминание или ответ на сообщение')