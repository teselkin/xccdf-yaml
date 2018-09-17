from xccdf_yaml.common import SharedFile

class GenericParser(object):
    def __init__(self, benchmark, parsed_args=None, output_dir=None,
                 shared_files=None):
        self.benchmark = benchmark
        self.parsed_args = parsed_args
        self.output_dir = output_dir or parsed_args.output_dir
        self.shared_files = shared_files

    @property
    def xccdf(self):
        return self.benchmark.xccdf

    @classmethod
    def name(cls):
        return cls.__id__

    @classmethod
    def about(cls):
        return ''

    def add_shared_file(self, filename, content=None):
        shared_file = self.shared_files.setdefault(
            SharedFile(basedir=self.shared_files.basedir,
                       filename=filename))

        if content:
            shared_file.set_content(content)

        self.shared_files.append(shared_file)

        return shared_file

    def parse(self, id, metadata):
        result = ParsedObjects(self.xccdf)

        rule = result.new_rule(id)

        if 'title' in metadata:
            rule.set_title(metadata['title'])

        if 'description' in metadata:
            rule.set_description(metadata['description'])

        if 'rationale' in metadata:
            rule.set_rationale(metadata['rationale'])

        for ident_name, ident_system in metadata.get('ident', {}).items():
            rule.add_ident(ident_name, ident_system)

        for reference in metadata.get('reference', []):
            if isinstance(reference, dict):
                rule.add_reference(reference['text'],
                                   href=reference.get('url'))
            else:
                rule.add_reference(reference)

        for reference in metadata.get('dc-reference', []):
            ref = rule.add_dc_reference()
            for element_name, element_value in reference.items():
                if element_name == 'href':
                    ref.set_attr('href', element_value)
                else:
                    ref.sub_element(element_name).set_text(element_value)

        return result


class ParsedObjects(object):
    def __init__(self, xccdf):
        self.xccdf = xccdf
        self.definition = None
        self.rule = None
        self.objects = []
        self.states = []
        self.tests = []
        self._shared_files = {}
        self._entrypoints = set()
        self.variable = None

    def new_rule(self, id):
        self.rule = self.xccdf.rule(id)
        return self.rule

    def add_shared_file(self, filename, content=None):
        shared_file = self._shared_files.setdefault(
            filename, SharedFile(filename))

        if content:
            shared_file.set_content(content)

        return shared_file

    def add_entrypoint(self, filename):
        self._entrypoints.add(filename)

    @property
    def entrypoints(self):
        return self._entrypoints

    @property
    def has_oval_data(self):
        return any([self.definition, self.states, self.states, self.tests])

    @property
    def has_variable(self):
        return True if self.variable else False
