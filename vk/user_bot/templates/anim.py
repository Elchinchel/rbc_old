import json
import re
import time
from database.client import method
from vk.user_bot import ND, dlp
from .life_is_strange import Rewind
from .operations import list_templates


class Anim:
    frames: list
    delay: float = 2

    def __init__(self, template: dict = {}):
        if template != {}:
            self.delay = json.loads(template['attachments'])['delay']
            self.frames = json.loads(template['text'])

    def pack(self, name, category):
        return {
            'name': name,
            'category': category,
            'text': json.dumps(self.frames, ensure_ascii=False),
            'attachments': json.dumps({'delay': self.delay})
        }


def play(anim: Anim, nd: ND):
    for frame in anim.frames:
        nd.msg_op(2, frame, keep_forward_messages=1)
        time.sleep(anim.delay)


@dlp.register('-анимка', receive=True)
def delete(nd: ND):
    if len(nd.msg['args']) > 0:
        name = ' '.join(nd.msg['args']).lower()
        old = nd.db.template_delete('anim', name)
        if old['name']:
            rew_id = Rewind(nd.db.user_id, 'animDelete', old).ident
            return nd.msg_op(2, f'🧹 Анимка "{name}" удалена\n' + # noqa
                f'Вернуть можно в течении 5 минут командой !!rewind {rew_id}') # noqa
        else:
            e = f'❗ Не существует анимки "{name}"'
    else:
        e = f'❗ А что именно удалить-то, чел?'
    nd.msg_op(2, e, delete=3)


@dlp.register('+анимка', receive=True)
def add_anim(nd: ND):
    name = re.findall(r"([^|]+)\|?([^|]*)", ' '.join(nd.msg['args']))
    if not name:
        nd.vk.msg_op(2, nd[3], "❗ Не указано название", msg_id=nd[1], delete=3)
        return "ok"
    category = name[0][1].lower().strip()
    category = category if category else 'без категории'
    name = name[0][0].lower().strip()

    if not nd.msg['payload']:
        return nd.msg_op(2, "❗ Нет данных")

    anim = Anim()

    anim.frames = nd.msg['payload'].split('#$')

    old = method.set_template(nd.db.user_id, 'anim', anim.pack(name, category))
    if old['name']:
        rew_id = Rewind(nd.db.user_id, 'common', old).ident
        msg = (f'✍ Анимка "{name}" перезаписана.\n' +
               'Вернуть старую можно в течении 5 минут командой !!rewind ' +
               str(rew_id))
    else:
        msg = f'✍ Анимка "{name}" сохранена'

    nd.msg_op(2, msg)


@dlp.register('анимка', receive=True)
def anim_render(nd: ND):
    if len(nd.msg['args']) > 0:
        var = []
        for arg in nd.msg['args']:
            if ':' in arg:
                var.append(arg.lower())
                nd.msg['args'].remove(arg)
        name = ' '.join(nd.msg['args'])
        template = nd.db.template_get('anim', name)
        if template:
            return play(Anim(template), nd)
        else:
            err = (f'❗ Не существует шаблона "{name}"')
    else:
        err = ('❗ Не существует безымянных анимок, чел')
    nd.msg_op(2, err, delete=3)


@dlp.register('анимки', receive=True)
def anim_list(nd: ND):
    return list_templates(nd,
                          'anim',
                          'анимок',
                          'У тебя нет ни одной анимки 😕\nДобавь командой +анимка', # noqa
                          'Анимки')
