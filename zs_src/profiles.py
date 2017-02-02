import json
from os.path import join

from zs_src.events import Event


class Profile(Event):
    RESERVED = ("name", "id_num")

    def make_object(self, function):
        return function(self)

    def get_json_dict(self):
        d = {}

        ignore = ("timer", "trigger", "handlers", "id_num")

        for name in self.__dict__:
            if name not in ignore:
                item = self.get(name)

                if type(item) is Profile:
                    item = item.get_json_dict()

                if type(item) is list:
                    i = 0
                    for sub_item in item:
                        if type(sub_item) is Profile:
                            item[i] = sub_item.get_json_dict()

                        i += 1

                if type(item) is dict:
                    for key in item:
                        sub_item = item[key]
                        if type(sub_item) is Profile:
                            item[key] = sub_item.get_json_dict()

                d[name] = item

        return d

    @staticmethod
    def load_json_dict(path, filename):
        path = join(path, filename)

        file = open(path, "r")
        d = json.load(file)
        file.close()

        return d

    @classmethod
    def make_profile(cls, json_dict):
        p = cls.interpret(json_dict)

        for key in p.__dict__:
            item = p.__dict__[key]
            if type(item) is dict:
                p.set(key, cls.make_profile(item))

            if type(item) is list:
                i = 0
                for sub_item in item:
                    if type(sub_item) is dict:
                        item[i] = cls.make_profile(sub_item)
                    i += 1
        return p
