from zs_constants.paths import CONTROLLER_PROFILES
from os.path import join
import json


def save_controller_profile(file_name, devices):
    cpf = {}
    for device in devices:
        profile = device.get_profile()
        name = profile["device_name"]
        cpf[name] = profile

    path = join(CONTROLLER_PROFILES, file_name)
    file = open(path, "w")
    json.dump(cpf, file, indent=2)
    print(json.dumps(cpf, indent=2))
    file.close()
