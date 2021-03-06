import datetime

from collections import OrderedDict
from xccdf_yaml.xml import XmlCommon

NSMAP = {
    None: "http://oval.mitre.org/XMLSchema/oval-definitions-5",
    'oval-common': "http://oval.mitre.org/XMLSchema/oval-common-5",
    'oval-def-indep': "http://oval.mitre.org/XMLSchema/oval-definitions-5#independent",
    'oval-def-linux': "http://oval.mitre.org/XMLSchema/oval-definitions-5#linux",
    'oval-def-unix': "http://oval.mitre.org/XMLSchema/oval-definitions-5#unix",
    'xsi': "http://www.w3.org/2001/XMLSchema-instance",
}


class XmlBase(XmlCommon):
    def __init__(self, name, ns=None):
        super().__init__(name, ns=ns, nsmap=NSMAP)


class OvalDefinitions(XmlBase):
    __elements_order__ = (
        'generator',
        'definitions',
        'tests',
        'objects',
        'states',
        'variables'
    )

    def __init__(self):
        super().__init__('oval_definitions')
        generator = OvalGenerator()
        self.append(generator)

        self._definitions = OrderedDict()
        self._tests = OrderedDict()
        self._objects = OrderedDict()
        self._states = OrderedDict()
        self._variables = OrderedDict()

    def is_empty(self):
        return not any([self._definitions, self._tests,
                        self._objects, self._states])

    def add_definition(self, id):
        return self._definitions.setdefault(id, Definition(id))

    def add_test(self, name, ns=None):
        return self._tests.setdefault(name, OvalTest(name, ns))

    def add_object(self, id, name, ns=None):
        return self._objects.setdefault(id, OvalObject(id, name, ns))

    def add_state(self, id, name, ns=None):
        return self._states.setdefault(id, OvalState(id, name, ns))

    def append_definition(self, item):
        if item:
            self._definitions.setdefault(item.get_attr('id'), item)
        return self

    def append_test(self, item):
        if item:
            self._tests.setdefault(item.get_attr('id'), item)
        return self

    def append_object(self, item):
        if item:
            self._objects.setdefault(item.get_attr('id'), item)
        return self

    def append_state(self, item):
        if item:
            self._states.setdefault(item.get_attr('id'), item)
        return self

    def append_variable(self, item):
        if item:
            self._variables.setdefault(item.get_attr('id'), item)
        return self

    def extend_definitions(self, items):
        for item in items:
            self.append_definition(item)
        return self

    def extend_tests(self, items):
        for item in items:
            self.append_test(item)
        return self

    def extend_objects(self, items):
        for item in items:
            self.append_object(item)
        return self

    def extend_states(self, items):
        for item in items:
            self.append_state(item)
        return self

    def extend_variables(self, items):
        for item in items:
            self.append_variable(item)
        return self

    def update_elements(self):
        self.remove_elements(name='definitions')
        if len(self._definitions) > 0:
            definitions = self.sub_element('definitions')
            for x in self._definitions.values():
                definitions.append(x)

        self.remove_elements(name='tests')
        if len(self._tests) > 0:
            tests = self.sub_element('tests')
            for x in self._tests.values():
                tests.append(x)

        self.remove_elements(name='objects')
        if len(self._objects) > 0:
            objects = self.sub_element('objects')
            for x in self._objects.values():
                objects.append(x)

        self.remove_elements(name='states')
        if len(self._states) > 0:
            states = self.sub_element('states')
            for x in self._states.values():
                states.append(x)

        self.remove_elements(name='variables')
        if len(self._variables) > 0:
            variables = self.sub_element('variables')
            for x in self._variables.values():
                variables.append(x)


class OvalGenerator(XmlBase):
    __elements_order__ = (
        'product_name',
        'product_version',
        'schema_version',
        'timestamp',
    )

    def __init__(self):
        super().__init__('generator')

        self.sub_element('product_name', ns='oval-common')\
            .set_text('xccdf_yaml generator')
        self.sub_element('product_version', ns='oval-common').set_text('0.1')
        self.sub_element('schema_version', ns='oval-common').set_text('5.11')
        self.sub_element('timestamp', ns='oval-common')\
            .set_text(datetime.datetime.now().isoformat())


class ExternalVariable(XmlBase):
    __element_order__ = (
        'comment',
        'datatype',
        'id',
        'version'
    )

    def __init__(self, id, datatype, version='1', comment=None):
        super().__init__('external_variable')
        comment = 'External variable' if not comment else comment
        self.set_attr('comment', comment)
        self.set_attr('datatype', datatype)
        self.set_attr('id', id)
        self.set_attr('version', version)


class Definition(XmlBase):
    __elements_order__ = (
        'metadata',
        'criteria',
    )

    def __init__(self, id, version='1', class_name='compliance'):
        super().__init__('definition')
        self.set_attr('id', id)
        self.set_attr('version', version)
        self.set_attr('class', class_name)
        self._metadata = None
        self._criteria = []

    def add_metadata(self):
        metadata = Metadata()
        self._metadata = metadata
        return metadata

    def add_criteria(self, operator='OR'):
        criteria = Criteria(operator=operator)
        self._criteria.append(criteria)
        return criteria

    def update_elements(self):
        self.remove_elements(name='metadata')
        if self._metadata:
            self.append(self._metadata)

        self.remove_elements(name='criteria')
        for x in self._criteria:
            self.append(x)


class Metadata(XmlBase):
    __elements_order__ = (
        'title',
        'affected',
        'description',
    )

    def __init__(self):
        super().__init__('metadata')

    def set_title(self, text):
        self.sub_element('title').set_text(text)
        return self

    def set_description(self, text):
        self.sub_element('description').set_text(text)
        return self

    def set_affected(self, family, platform):
        affected = None
        for affected in self.elements('affected'):
            if affected.get_attr('family') == family:
                for x in affected.elements('platform'):
                    if x._text == platform:
                        return self
                break

        if affected is None:
            affected = self.sub_element('affected').set_attr('family', family)

        affected.sub_element('platform').set_text(platform)
        return self


class Criteria(XmlBase):
    def __init__(self, operator='OR'):
        super().__init__('criteria')
        self.set_attr('operator', operator)
        self._criterion = []
        self._criteria = []

    def add_criterion(self, instance):
        self._criterion.append(instance)
        return instance

    def new_criterion(self, test_ref):
        criterion = Criterion(test_ref=test_ref)
        self._criterion.append(criterion)
        return criterion

    def add_criteria(self, instance):
        self._criteria.append(instance)
        return instance

    def update_elements(self):
        self.remove_elements(name='criterion')
        for x in self._criterion:
            self.append(x)
        self.remove_elements(name='criteria')
        for x in self._criteria:
            self.append(x)


class Criterion(XmlBase):
    def __init__(self, test_ref):
        super().__init__('criterion')
        self.set_attr('test_ref', test_ref)


class OvalTest(XmlBase):
    def __init__(self, id, name, check='all', check_existence='all_exist',
                 version='1', ns=None):
        super().__init__(name, ns=ns)
        self.set_attrs({
            'id': id,
            'check': check,
            'check_existence': check_existence,
            'version': version,
        })
        self.set_attr('comment', 'Test {}'.format(id))
        # self.set_attr('id', id)
        self._objects = set()
        self._states = set()

    def add_object(self, instance):
        self._objects.add(instance)

    def add_state(self, instance):
        self._states.add(instance)

    def update_elements(self):
        self.remove_elements(name='object')
        for x in self._objects:
            self.sub_element('object')\
                .set_attr('object_ref', x.get_attr('id'))

        self.remove_elements(name='state')
        for x in self._states:
            self.sub_element('state')\
                .set_attr('state_ref', x.get_attr('id'))


class OvalObject(XmlBase):
    def __init__(self, id, name, ns=None, version='1'):
        super().__init__(name, ns=ns)
        self.set_attrs({
            'id': id,
            'version': version,
        })


class OvalState(XmlBase):
    def __init__(self, id, name, ns=None, version='1'):
        super().__init__(name, ns=ns)
        self.set_attrs({
            'id': id,
            'version': version,
        })
