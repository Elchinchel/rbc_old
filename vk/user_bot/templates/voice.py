from vk.user_bot.utils import upload_audio
from .life_is_strange import Rewind
from .operations import list_templates, remove_template
from vk.user_bot import dlp, ND
import re


@dlp.register('+гс', receive=True)
def voice_create(nd: ND):
    def e(text):
        nd.vk.msg_op(2, nd[3], text, msg_id = nd[1], delete = 3)

    name = re.findall(r"([^|]+)\|?([^|]*)", ' '.join(nd.msg['args']))
    if not name:
        e("❗ Не указано название")
        return "ok"
    category = name[0][1].lower().strip()
    name = name[0][0].lower().strip()

    if nd.msg['reply'] == None:
        e("❗ Необходим ответ на сообщение")
        return "ok"

    if not nd.msg['reply']['attachments']:
        e("❗ Необходим ответ на голосовое сообщение")
        return "ok"
    elif nd.msg['reply']['attachments'][0]['type'] != 'audio_message':
        e("❗ Необходим ответ на голосовое сообщение")
        return "ok"

    voice, length = upload_audio(nd.msg['reply']['attachments'][0], nd.vk)

    old = nd.db.template_create(name, voice, category = category)

    if old['name']:
        rew_id = Rewind(nd.db.user_id, 'voice', old).ident
        msg = (f'🗣 Голосовое сообщение "{name}" перезаписано\nНовая длина: {length}сек.\n' +
               f'Вернуть старое можно в течении 5 минут командой !!rewind {rew_id}')
    else:
        msg = f'🗣 Голосовое сообщение "{name}" сохранено\nДлина: {length}сек.'

    nd.vk.msg_op(2, nd[3], msg, msg_id = nd[1], delete = 0 if old['name'] else 3)
    return "ok"


@dlp.register('гсы', receive=True)
def voice_list(nd: ND):
    return list_templates(nd,
    'voice',
    'голосовых сообщений',
    'У тебя нет ни одного голосового сообщения 😕\nДобавь командой +гс',
    'Голосовые сообщения')


@dlp.register('-гс', receive=True)
def voice_remove(nd: ND):
    return remove_template(nd,
    'voice',
    ['Голосовое сообщение', 'о'],
    'голосового сообщения')


@dlp.register('гс', receive=True)
def voice_print(nd: ND):
    if len(nd.msg['args']) > 0:
        name = ' '.join(nd.msg['args']).lower()
        template = nd.db.template_get('voice', name)
        if template:
            sets = nd.db.settings_get()
            nd.msg['attachments'].extend([template['attachments']])
            nd.vk.exe("""API.messages.send({"peer_id":%d,"message":"%s",
            "attachment":"%s","reply_to":"%s","random_id":0});
            API.messages.delete({"message_ids":%d,"delete_for_all":1});""" %
            (nd[3] if not sets.templates_bind else sets.templates_bind, nd.msg['payload'].replace('\n', '<br>'),
            ','.join(nd.msg['attachments']),
             nd.msg['reply']['id'] if nd.msg['reply'] else '', nd[1]))
            return "ok"
        else:
            e = (f'❗ Не существует голосового сообщения "{name}"')
    else:
        return list_templates(nd,
        'voice',
        'голосовых сообщений',
        'У тебя нет ни одного голосового сообщения 😕\nДобавь командой +гс',
        'Голосовые сообщения')
    nd.vk.msg_op(2, nd[3], e, msg_id = nd[1], delete = 3)
    return "ok"