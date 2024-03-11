from vk.user_bot import ND, dlp
from .life_is_strange import Rewind
from .operations import remove_template


@dlp.register('+деж', receive=True)
def duty_create(nd: ND):
    def e(text):
        nd.vk.msg_op(2, nd[3], text, msg_id=nd[1], delete=3)

    name = ' '.join(nd.msg['args'])
    if not name:
        e("❗ Не указано название")
        return "ok"

    if not nd.msg['payload']:
        e("❗ Нет данных")
        return "ok"

    if nd.msg['payload'].endswith('\n'):
        nd.msg['payload'] = nd.msg['payload'][:-1]

    old = nd.db.template_create(name, payload=nd.msg['payload'],
                                category='___dutys___')

    if old['name']:
        rew_id = Rewind(nd.db.user_id, 'dutys', old).ident
        msg = (f'⚙ Дежурный "{name}" перезаписан\n' +
               'Вернуть старый можно в течении 5 минут командой !!rewind ' +
               str(rew_id))
    else:
        msg = f'⚙ Дежурный "{name}" сохранен'

    nd.vk.msg_op(2, nd[3], msg, msg_id=nd[1], delete=0 if old['name'] else 3)
    return "ok"


@dlp.register('деж', receive=True)
def duty_print(nd: ND):
    if len(nd.msg['args']) > 0:
        name = ' '.join(nd.msg['args']).lower()
        template = nd.db.template_get('dutys', name)
        if template:
            print(template)
            nd.vk.msg_op(1, -174105461, template['text'])
            nd.vk.msg_op(2, nd[3], '✅ Отправлено', nd[1])
            return "ok"
        else:
            e = (f'❗ Не существует дежа "{name}"')
    else:
        e = ('❗ Необходимо указать название')
    nd.vk.msg_op(2, nd[3], e, msg_id=nd[1], delete=3)
    return "ok"


@dlp.register('дежи', receive=True)
def duty_list(nd: ND):
    templates = nd.db.template_get('dutys', all_=True)
    if templates:
        msg = '📄 Список дежурных / биндингов лс ириса:'
        for template in templates:
            msg += f"\n-- {template['name']}"
    else:
        msg = '🤷‍♀ Нет ни одного биндинга лс ириса. Добавь командой +деж'
    nd.vk.msg_op(2, nd[3], msg, msg_id=nd[1])
    return "ok"


@dlp.register('-деж', receive=True)
def duty_remove(nd: ND):
    return remove_template(nd,
                           'dutys',
                           ['Дежурный', ''],
                           'дежурного')
