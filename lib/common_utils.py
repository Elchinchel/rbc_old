import re
from typing import List, Any, Tuple, Union


async def aenum(items: List[Any], start: int = 0) -> Tuple[int, Any]:
    "`enumerate` для асинхронных циклов"
    async for item in items:
        yield start, item
        start += 1


def parse_text(text: str, cut_prefix: bool) -> Tuple[str, List[str], str]:
    '(команда, список аргументов, нагрузка)'
    matches = re.findall(r'(\S+)|\n(.*)', text)
    if not matches:
        cmd = ''
    else:
        if cut_prefix:
            del matches[0]
        cmd = matches.pop(0)[0].lower()
    args = []
    payload = ''
    for i, match in enumerate(matches, 1):
        if match[0]:
            args.append(match[0])
        else:
            payload += match[1] + ('\n' if i < len(matches) else '')
    return cmd, args, payload


def parse_to_name_and_cat(string: str) -> Union[Tuple[str, str], Tuple[None, None]]:  # noqa
    '(имя, категория) или None'
    name = re.findall(r"([^|]+)\|?([^|]*)", string)
    if not name:
        return None, None
    return name[0][0].lower().strip(), name[0][1].lower().strip() or 'без категории'  # noqa
