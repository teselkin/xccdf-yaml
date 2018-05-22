from xccdf_yaml.common import ClassLoader


class GenericParser(object):
    def __init__(self):
        pass

    @classmethod
    def name(cls):
        return cls.__id__

    @classmethod
    def about(cls):
        return ''


PARSERS = ClassLoader(__name__)
PARSERS.load(startswith='YamlParser')
