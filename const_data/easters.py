from typing import Dict
import json
import os


with open(os.path.join(os.path.dirname(__file__), 'easters.json'),
          encoding='utf-8') as anims:
    easters_common: Dict[str, str] = json.loads(anims.read())
