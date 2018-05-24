from xccdf_yaml.xccdf import BenchmarkRule


class GenericParser(object):
    def __init__(self):
        pass

    @classmethod
    def name(cls):
        return cls.__id__

    @classmethod
    def about(cls):
        return ''


class ParsedObjects(object):
    def __init__(self):
        self.definition = None
        self.rule = None
        self.objects = []
        self.states = []
        self.tests = []

    def new_rule(self, id):
        self.rule = BenchmarkRule(id)
        return self.rule