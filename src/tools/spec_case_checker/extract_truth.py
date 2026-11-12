"""从tune_domain各子模块rules提取type_id基准真值"""
from domains.tune_domain.plant.rules import TYPE_MAP as PLANT_TYPE_MAP
from domains.tune_domain.pet.rules import PET_TYPE_MAP
from domains.good_domain.cloth.rules import CLOTH_TYPE_MAP
from domains.good_domain.wall.rules import GOODWALL_TYPE_MAP


def get_plant_truth():
    return {
        "domain": "tune_domain",
        "module": "plant",
        "valid_type_ids": list(PLANT_TYPE_MAP.keys()),
        "type_desc": PLANT_TYPE_MAP
    }

def get_pet_truth():
    return {
        "domain": "tune_domain",
        "module": "pet",
        "valid_type_ids": list(PET_TYPE_MAP.keys()),
        "type_desc": PET_TYPE_MAP
    }

# extract_truth.py 追加
def get_fruit_truth():
    from domains.tune_domain.fruit.rules import FRUIT_TYPE_MAP
    return {
        "domain": "tune_domain",
        "module": "fruit",
        "valid_type_ids": list(FRUIT_TYPE_MAP.keys()),
        "type_desc": FRUIT_TYPE_MAP
    }

def get_cloth_truth():
    return {
        "domain": "tune_domain",
        "module": "cloth",
        "valid_type_ids": list(CLOTH_TYPE_MAP.keys()),
        "type_desc": CLOTH_TYPE_MAP
    }

def get_wall_truth():
    from domains.good_domain.wall.rules import GOODWALL_TYPE_MAP
    return {
        "domain": "good_domain",
        "module": "wall",
        "valid_type_ids": list(GOODWALL_TYPE_MAP.keys()),
        "type_desc": GOODWALL_TYPE_MAP
    }

def get_all_truth():
    return [get_plant_truth(), get_pet_truth(), get_fruit_truth(), get_cloth_truth(), get_wall_truth()]
