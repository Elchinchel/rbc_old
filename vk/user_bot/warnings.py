from . import dlp, ND
from database.driver import owner_id, warns, set_warn_list


def get_warns() -> str:
    return '\n\n' + '\n'.join(warns) if warns else ''


@dlp.register('варны', 'преды')
def warn_list(nd: ND):
    if not warns:
        return nd.msg_op(2, '☑️ Все как будто бы в порядке')
    
    nd.msg_op(2, '\n'.join(warns))


@dlp.register('+варн', '+пред', receive=True)
def warn_set(nd: ND):
    if nd.db.user_id != owner_id:
        return

    message = ' '.join(nd.msg['args']) if nd.msg['args'] else nd.msg['payload']

    if not message:
        return nd.msg_op(2, '❗️ Нет текста')

    warns.append(message)
    set_warn_list(warns)
    nd.msg_op(2, '☑️ Добавлено')


@dlp.register('-варн', '-пред', receive=True)
def warn_unset(nd: ND):
    if nd.db.user_id != owner_id:
        return

    message = ' '.join(nd.msg['args']) if nd.msg['args'] else nd.msg['payload']
    
    if not message:
        nd.msg_op(2, '❗️ Нет текста')
    elif message in warns:
        warns.remove(message)
        set_warn_list(warns)
        nd.msg_op(2, '☑️ Удалено')
    else:
        nd.msg_op(2, '❗️ Не нашел')