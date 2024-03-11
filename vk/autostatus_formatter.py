import re
from datetime import datetime, timedelta, timezone
from lib.vkmini import VkApi
from asyncio import sleep


counters_vars = {
    "сообщения": lambda d: d.get('messages', 0),
    "заявки": lambda d: d.get('friends', 0),
    "уведы": lambda d: d.get('notifications', 0)
}

avatar_vars = {
    "лайки": lambda d: d['likes']['count'],
    "комменты": lambda d: d['comments']['count'],
    "репосты": lambda d: d['reposts']['count']
}

blacklist_var = {
    "чс": lambda d: d['count']
}


time_re = re.compile(r'время ?([+-]?\d+)? ?(час|мин|сек).*')

time_formatters = {
    'час': '%H',
    'мин': '%M',
    'сек': '%S'
}


def format_time(time: tuple) -> str:
    delta = int(time[0]) if time[0] != '' else 3
    date = datetime.now(timezone(timedelta(hours=delta, seconds=180)))
    return date.strftime(time_formatters.get(time[1]))


async def render(formatter, vk: VkApi):
    blacklist = None
    counters = None
    avatar = None

    def replace(var: str, data: str) -> str:
        return formatter.replace('{'+var+'}', str(data))

    for var in re.findall(r'\{(.+?)\}', formatter):
        await sleep(0.5)
        if var in counters_vars:
            if counters is None:
                counters = await vk('account.getCounters') or {}
            formatter = replace(var, counters_vars[var](counters))
        elif var in avatar_vars:
            if avatar is None:
                avatar = (await vk('photos.get', album_id='profile',
                                   extended=True))['items'][-1]
            formatter = replace(var, avatar_vars[var](avatar))
        elif var in blacklist_var:
            if blacklist is None:
                blacklist = (await vk('account.getBanned', count=200))
            formatter = replace(var, blacklist_var[var](blacklist))
        else:
            time = time_re.findall(var)
            if len(time) == 0:
                pass
            formatter = replace(var, format_time(time[0]))
    return formatter
