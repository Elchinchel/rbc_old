from lib.vkmini.exceptions import VkResponseException
from asyncio import sleep
from lib.microvk import VkApi
from lib.vkmini import VkApi as VkAsync


def execute_find_chat(chat_name: str) -> str:
    return """
    var i = 0;
    var items = API.messages.getConversations({"count":"200"}).items;
    while (i < items.length) {
        if (items[i].conversation.chat_settings.title == "%s"){
            return items[i].conversation.peer.id;
            };
        i = i + 1;
    };
    return null;
    """ % chat_name


async def async_requester(vk: VkAsync, method: str,
                          retries: int = 5, **kwargs):
    retry = 0
    while retry < retries:
        try:
            return await vk(method, **kwargs)
        except VkResponseException as e:
            if e.error_code != 6:
                break
            await sleep(0.5)
            retry += 1
