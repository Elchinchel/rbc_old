import json
import os


# у меня почему то падает python language server, когда я пихаю смайлики сюда
# поэтому пришлось их спрятать в json
with open(os.path.join(os.path.dirname(__file__), 'anims.json'),
          encoding='utf-8') as anims:
    data = json.loads(anims.read())
    animations: dict = data['animations']
    rotating_animations: dict = data['rotating_animations']
