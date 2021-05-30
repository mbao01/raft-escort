import json
import time

from src.states.base import BaseState


def uptime(created_at: int):
    seconds = int(time.time()) - created_at
    if seconds >= 86400:
        days = seconds // 86400
        return f'up {days} day{"s" if days > 1 else ""}'
    elif seconds >= 3600:
        hours = seconds // 3600
        return f'up {hours} hour{"s" if hours > 1 else ""}'
    elif seconds >= 60:
        minutes = seconds // 60
        return f'up {minutes} minute{"s" if minutes > 1 else ""}'
    else:
        return f'up {seconds} seconds'


def serialize(obj):
    default = lambda o: f"<<non-serializable: {type(o).__qualname__}>>" if isinstance(o, BaseState) else o.__dict__
    return json.loads(json.dumps(obj, default=default, sort_keys=True))


class Map(dict):
    """
    Example:
    m = Map({'first_name': 'Eduardo'}, last_name='Pool', age=24, sports=['Soccer'])
    """

    def __init__(self, *args, **kwargs):
        super(Map, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.items():
                self[k] = v

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(Map, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(Map, self).__delitem__(key)
        del self.__dict__[key]
