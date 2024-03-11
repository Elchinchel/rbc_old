from database import __version__
from database.client import method
from .warnings import get_warns
from . import dlp


@dlp.register('info', 'инфа', 'инфо')
def about(nd):
    db = nd.db
    settings = db.settings_get()
    all_temps = method.get_all_templates_length()
    temps = len(nd.db.template_get('common', all_=True))
    p_temps = temps/all_temps['common']*100
    voices = len(nd.db.template_get('voice', all_=True))
    p_voices = voices/all_temps['voice']*100
    # получается деление на ноль, угу
    # добавь 1 гс и 1 шаб, че)
    message = f"""
    Случайный бот v{__version__}

    игнорируемых пользователей: {len(settings.ignore_list)}

    шаблонов: {temps} ({round(p_temps) if p_temps > 1 else round(p_temps, 2)}%)
    сохраненных голосовых: {voices} ({round(p_voices) if p_voices > 1 else round(p_voices, 2)}%)
    """.replace('    ', '') + get_warns()

    nd.vk.msg_op(2, nd[3], message, nd[1])
    return "ok"
