import subprocess
import json

from vk.user_bot import dlp, ND
from .admin import check_admin

LONGPOLL = "RBClub LONGPOLL module"
DATABASE = "RBClub DATABASE module"
MAIN = "RBClub MAIN module"


@dlp.register('чекресурсы')
@dlp.wrap_handler(check_admin)
def check_resources(nd: ND):
    processes = json.loads(
        subprocess.run('pm2 jlist', shell=True, capture_output=True).stdout
    )
    proc_data = {}
    for proc in processes:
        if not proc['name'].startswith('RBClub'):
            continue
        monit = proc['monit']
        info = f"ОЗУ: {round(monit['memory']/(1024**2))}МБ | ЦП: {monit['cpu']}%"  # noqa
        proc_data.update({proc['name']: info})
    nd.msg_op(f"""
        📊 Потребление ресурсов по мнению PM2:
        Главный модуль -- {proc_data[MAIN]}
        LongPoll модуль -- {proc_data[LONGPOLL]}
        Модуль базы данных -- {proc_data[DATABASE]}
    """.replace('    ', ''))
