import json
from vk.user_bot import dlp, ND
from vk.user_bot.utils import parseByID


@dlp.register('parse', receive=True)
def parse_message(nd: ND):
    if nd.msg['reply']:
        nd.msg = parseByID(nd.vk, nd.msg['reply']['id'], True)
    raw = nd.msg.pop('raw')
    if nd.msg['args']:
        if nd.msg['args'][0] == 'all':
            nd.msg['raw'] = raw
    nd.msg_op(
        2, json.dumps(nd.msg, indent=4, ensure_ascii=False).replace('    ', 'ᅠ')  # noqa
    )
