"""Camera selection preferences; no GL or scene construction in the picker."""
from hashlib import sha256
from PySide6.QtCore import QSettings
from aureon_paths import settings_args

def _key(scene_id):
    return 'scene_camera/v1/'+sha256(scene_id.encode('utf-8')).hexdigest()

def camera_choice(scene_id,presets):
    value=str(QSettings(*settings_args()).value(_key(scene_id),'auto'))
    return value if value=='auto' or any(p[0]==value for p in presets) else 'auto'

def save_camera_choice(scene_id,presets,choice):
    if choice!='auto' and not any(p[0]==choice for p in presets):return False
    QSettings(*settings_args()).setValue(_key(scene_id),choice)
    return True
