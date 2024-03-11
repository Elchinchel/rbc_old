from time import sleep
from time import time
import requests
import json
from lib.microvk import VkApiResponseException
from . import dlp, ND

# IAM_TOKEN = ''

# IAM_TOKEN_LAST = 0

@dlp.register('перевод', receive=True)
def translate(nd: ND):
    def e():
        nd.msg_op(2, '❗ Необходим ответ на голосовое сообщение')
    if nd.msg['reply']:
        if nd.msg['reply']['attachments']:
            if nd.msg['reply']['attachments'][0]['type'] == 'audio_message':
                ts = None
                msg_id = nd.msg['reply']['id']
                for i in range(10):
                    ts = nd.msg['reply']['attachments'][0]['audio_message'].get('transcript')
                    if ts: break
                    if i == 0:
                        nd.msg_op(2, '⏱ Что ж, VK пока не перевел сообщение, ждем-с...')
                    nd.msg['reply'] = nd.vk('messages.getById', message_ids = msg_id)['items'][0]
                    sleep(1)
                if ts:
                    nd.msg_op(2, f'💬 Транскрипция VK:\n{ts}', keep_forward_messages = 1)
                else:
                    nd.msg_op(2, f'❎ Не дождались.\nМожешь попробовать еще раз, но скорее всего VK уже не будет его переводить...')
            else: e()
        else: e()
    else: e()


# @dlp.register('переводчик', receive=True)
# def translate(nd: ND):
#     global IAM_TOKEN_LAST
#     global IAM_TOKEN
#     if time() - IAM_TOKEN_LAST > 21600:
#         IAM_TOKEN = requests.post(f"https://iam.api.cloud.yandex.net/iam/v1/tokens",
#                          data = '''{\"yandexPassportOauthToken\":"\%s\"}''' % oauthtoken).json()['iamToken']
#         IAM_TOKEN_LAST = time()
#     data = requests.post(f"https://translate.api.cloud.yandex.net/translate/v2/translate",
#                          headers = {"Authorization": f'Bearer {IAM_TOKEN}'},
#                          data = json.dumps({
#                             "sourceLanguageCode": "ru",
#                             "targetLanguageCode": "en",
#                             "texts": [ nd.msg['reply']['text'] ]
#                          }, ensure_ascii=False)).text
#     print(data)