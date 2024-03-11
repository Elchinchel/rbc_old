from vk.user_bot import ND
from .life_is_strange import Rewind


def remove_template(nd: ND, type_, success, not_exist):
    if len(nd.msg['args']) > 0:
        name = ' '.join(nd.msg['args']).lower()
        old = nd.db.template_delete(type_, name)
        if old['name']:
            rew_id = Rewind(nd.db.user_id, type_+'Delete', old).ident
            return nd.msg_op(2, f'🧹 {success[0]} "{name}" удален{success[1]}\n' + # noqa
                f'Вернуть можно в течении 5 минут командой !!rewind {rew_id}') # noqa
        else:
            e = f'❗ Не существует {not_exist} "{name}"'
    else:
        e = f'❗ А что именно удалить-то, чел?'
    nd.vk.msg_op(2, nd[3], e, msg_id=nd[1], delete=3)
    return "ok"


def list_templates(nd, type_, all_, no_temps, cat_list): # noqa
    msg = ''
    if len(nd.msg['args']) > 0:
        if nd.msg['args'][0] == 'все':
            if len(nd.msg['args']) > 1:
                try:
                    page = int(nd.msg['args'][1])
                    i = 1
                except Exception:
                    page = 1
            else:
                page = 0
            if page == 0:
                msg = f'📑 Список всех {all_}:'
            else:
                msg_ = f'📑 Список всех {all_} (страница №{page}):'
            templates = nd.db.template_get(type_, all_=True)
            if templates:
                for template in templates:
                    msg += f"\n{template['id']}. {template['name']} | {template['category']}" # noqa
                    if len(msg) > 1000 and page > 0:
                        if i == page:
                            break
                        i += 1
                        msg = ''
                    if len(msg) > 4000:
                        msg = f'🤷‍♀ Слишком много {all_} для отображения их на одной странице' # noqa
                        break
                if page > 0:
                    if i != page:
                        msg = f'🙃 Страница №{page} пока пуста'
                    else:
                        msg = msg_ + msg
            else:
                msg = no_temps
        else:
            name = ' '.join(nd.msg['args']).lower()
            templates = nd.db.template_get(type_, name, True)
            if templates:
                msg = f'📚 {cat_list} категории "{name}":'
                for template in templates:
                    msg += f"\n-- {template['name']}"
            else:
                msg = f'❗ Не существует категории "{name}"'
    else:
        msg = f'📚 Категории {all_}:'
        cats = nd.db.template_get(type_, category=True, all_=True)
        for cat in cats:
            msg += f"\n-- {cat} ({cats[cat]})"
        if msg == f'📚 Категории {all_}:':
            msg = no_temps
    nd.vk.msg_op(2, nd[3], msg, msg_id=nd[1])
    return "ok"
