from .utils import find_mention_by_message
from lib.microvk import VkApiResponseException
import time
from . import dlp, ND


@dlp.register('влс', 'в', receive=True)
def to_private(nd: ND):
    if nd.msg['command'] == 'в':
        if nd.msg['args'][0] != 'лс':
            return "ok"
    uid = find_mention_by_message(nd.msg, nd.vk)
    if uid:
        if not nd.msg['payload'] and not nd.msg['attachments']:
            nd.msg_op(2, '❗ Нет данных')
        try:
            nd.vk.msg_op(1, uid, nd.msg['payload'], attachment = ','.join(nd.msg['attachments']))
            msg = '✅ Сообщение отправлено'
        except VkApiResponseException as e:
            if e.error_code == 902:
                msg = '❗ Пользователь ограничил круг лиц, которые могут отправлять ему сообщения'
            else:
                msg = f'❗ Ошибка VK №{e.error_code}: {e.error_msg}'
        time.sleep(0.5)
        nd.msg_op(2, msg, delete = 3)
    else:
        nd.msg_op(2, '❗ Необходимо упоминание или ответ на сообщение')