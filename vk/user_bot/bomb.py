from .utils import execme, find_time
from . import dlp, ND
from database import VkDB
import re


@dlp.register('б', receive=True)
def bomb(nd: ND):
    nd.vk.msg_op(3, nd[3], msg_id=nd[1])
    reply = ''
    sticker = ''
    p = 0
    att = []
    text = ' '

    msg = nd.msg
    payload = ''.join(re.findall(r'\n.*', msg['text']))

    time = find_time(' '.join(nd.msg['args']))

    if not time:
        time = 60
    elif time > 86400:
        nd.vk.msg_op(1, nd[3], '❗ Осади, максимальная длина - сутки')
        return "ok"

    if payload:
        text = payload
        p = 1

    if msg['attachments']:
        att = msg['attachments']
        p = 1

    if msg['reply']:
        reply = msg['reply']['id']
        if msg['reply']['from_id'] == nd.db.user_id:
            atts = msg['reply']['attachments']
            if atts:
                atts = atts[0]
                if atts['type'] == 'sticker':
                    sticker = atts['sticker']
                    sticker = int(sticker['sticker_id'])
                    p = 1
                    nd.vk.msg_op(3, nd[3], msg_id=reply)
                    reply = ''

    if p == 0:
        if reply:
            text = msg['reply_message']['text']
            reply = ''
        else:
            nd.vk.msg_op(1, nd[3], '❗ Ну и че мне отправить?')
            return
    code = """return API.messages.send({peer_id:%s,message:"%s",random_id:0,expire_ttl:"%s",attachment:"%s",
    sticker_id:"%s",reply_to:"%s"});""" % (nd[3], text[1:], time, ",".join(att), sticker, reply)
    execme(code, nd.db)
    return "ok"
