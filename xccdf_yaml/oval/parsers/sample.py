# from xccdf_yaml.oval.parsers.common import ParsedObjects
from xccdf_yaml.oval.parsers.common import GenericParser


class YamlParserSample(GenericParser):
    __id__ = 'sample'

    def __init__(self):
        super().__init__()

    @classmethod
    def about(cls):
        return "sample parser"
