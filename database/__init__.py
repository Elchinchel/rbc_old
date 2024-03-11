from .driver import VkDB, owner_id, vk_users

__version__: str = "Unsetted"

def set_version(version: str):
    global __version__
    __version__ = version