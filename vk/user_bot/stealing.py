from .utils import find_mention_by_message, upload_avatar
from lib.microvk import VkApiResponseException
import requests
import io
from . import dlp, ND


@dlp.register('ава', receive=True)
def avatar(nd: ND):
    nd.msg_op(3)
    uid = find_mention_by_message(nd.msg, nd.vk)
    if uid:
        image_url = nd.vk('users.get', fields='photo_max_orig',
                       user_ids=uid)[0]['photo_max_orig']
    elif nd.msg['attachments']:
        atts = nd.msg['raw']['attachments']
        for att in atts:
            photo = att.get('photo')
            if photo: break
        if not photo:
            return nd.msg_op(1, '❗ Нет данных')
        image_url = photo['sizes'][-1]['url']
    
    try:
        post_id = upload_avatar(image_url, nd.vk)
        nd.msg_op(1, '☝🏻', attachment=f'wall{nd.db.user_id}_{post_id}')
    except VkApiResponseException as e:
        if e.error_code == 129:
            nd.msg_op(1, '❗ Неверный формат')
