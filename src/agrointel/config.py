from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[2]
CONFIG = yaml.safe_load((ROOT / 'configs/default.yaml').read_text())
CFEATURES = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
RFEATURES = ['state', 'district', 'crop', 'season', 'year', 'area']
CROP_MAP = {'rice':'rice', 'maize':'maize', 'chickpea':'gram', 'pigeonpeas':'arhar (tur)',
    'mungbean':'moong', 'blackgram':'urad', 'lentil':'masoor', 'mothbeans':'moth', 'banana':'banana'}
