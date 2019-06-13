import datetime
import re

from collections import namedtuple, OrderedDict
from enum import Enum
from xccdf_yaml.xml import XmlCommon
from xccdf_yaml.xml import DublinCoreElementBase
from xccdf_yaml.markdown import MarkdownHtml


NSMAP = {
    None: "http://checklists.nist.gov/xccdf/1.2",
    'oval-def': "http://oval.mitre.org/XMLSchema/oval-definitions-5",
    'sce': "http://open-scap.org/page/SCE",
    'sceres': "http://open-scap.org/page/SCE_result_file",
    'xsi': "http://www.w3.org/2001/XMLSchema-instance",
}


class XccdfBoolean(Enum):
    TRUE = True
    FALSE = False

    @classmethod
    def parse(cls, value):
        if isinstance(value, bool):
            return cls.TRUE if value is True else cls.FALSE

        if isinstance(value, str):
            if value.isnumeric():
                value = int(value)
            else:
                value = value.lower()
                if re.match(r'^(y(es)?|true)$', value):
                    return cls.TRUE
                if re.match(r'^(n(o)?|false)$', value):
                    return cls.FALSE

        if isinstance(value, int):
            return cls.TRUE if value > 0 else cls.FALSE

        raise Exception("Can't convert '{}' to True / False".format(value))

    def __bool__(self):
        return self.value is True

    def __str__(self):
        return 'true' if self.value else 'false'


class XmlBase(XmlCommon):
    def __init__(self, name, ns=None):
        super().__init__(name, ns=ns, nsmap=NSMAP)


class XccdfBase(XmlBase):
    def __init__(self, generator, name, id=None, ns=None):
        super().__init__(name, ns=ns)
        self._id = id
        self._xccdf_id = None
        self._generator = generator

    @property
    def id(self):
        return self._id

    @property
    def xccdf(self):
        return self._generator

    @property
    def xccdf_id(self):
        if self._xccdf_id is None:
            self._xccdf_id = self._generator.id(self._name, self._id)
        return self._xccdf_id

    def update_elements(self):
        super().update_elements()
        self.set_attr('id', self.xccdf_id)


class XccdfDublinCoreElement(DublinCoreElementBase):
    def __init__(self, name):
        super().__init__(name, nsmap=NSMAP)


class SetTitleMixin(object):
    def set_title(self, text):
        if text is not None:
            content = text.rstrip()
            self.sub_element('title').set_text(content)
        return self


class SetDescriptionMixin(object):
    def set_description(self, text, plaintext=False):
        if text is not None:
            self.sub_element('description')\
                .set_object(MarkdownHtml(text, plaintext=plaintext))
        return self


class XccdfGenerator(object):
    def __init__(self, vendor):
        self.vendor = vendor
        namespace = re.sub(r'\.+', '.',
                           re.sub(r'[^\d\w\-\.]', '', vendor.lower()))
        self.namespace = '.'.join(reversed(namespace.split('.')))

    def id(self, element, name):
        if element.lower() not in ['benchmark', 'profile', 'group', 'rule',
                                   'value', 'testresult', 'tailoring']:
            raise Exception("Bad XCCDF element {}".format(element))
        return "xccdf_{}_{}_{}".format(self.namespace, element.lower(), name)

    def benchmark(self, *args, **kwargs):
        return XccdfBenchmarkElement(self, *args, **kwargs)

    def tailoring(self, *args, **kwargs):
        return XccdfTailoringElement(self, *args, **kwargs)

    def profile(self, *args, **kwargs):
        return XccdfProfileElement(self, *args, **kwargs)

    def group(self, *args, **kwargs):
        return XccdfGroupElement(self, *args, **kwargs)

    def rule(self, *args, **kwargs):
        return XccdfRuleElement(self, *args, **kwargs)

    def value(self, *args, **kwargs):
        return XccdfValueElement(self, *args, **kwargs)

    def check(self, *args, **kwargs):
        return XccdfCheckElement(self, *args, **kwargs)

    def dc_metadata(self, *args, **kwargs):
        return XccdfMetadataElement(self, *args, **kwargs)

    def status(self, *args, **kwargs):
        return XccdfStatusElement(self, *args, **kwargs)


class XccdfBenchmarkElement(XccdfBase, SetTitleMixin, SetDescriptionMixin):
    __elements_order__ = (
        'status',
        'title',
        'description',
        'platform',
        'version',
        'metadata',
        'Profile',
        'Value',
        'Group',
        'Rule',
    )

    def __init__(self, xccdf, id, version='0.1'):
        super().__init__(generator=xccdf, name='Benchmark', id=id)
        self._id = id
        self._platforms = set()
        self._profiles = OrderedDict()
        self._groups = OrderedDict()
        self._values = OrderedDict()
        self._rules = OrderedDict()
        self._dc_metadata = None
        self._status = []
        self.version = version

    @property
    def platforms(self):
        return self._platforms

    def set_status(self, status_string='draft', status_date=None):
        status = XccdfStatusElement(self.xccdf,
                                    status=status_string,
                                    timestamp=status_date)
        self._status.append(status)
        return self

    def append_status(self, item):
        self._status.append(item)
        return self

    def set_version(self, version=None):
        if version is not None:
            self.version = str(version)
        return self

    def add_platform(self, name):
        self._platforms.add(name)
        return self

    def append_profile(self, item):
        self._profiles.setdefault(item.xccdf_id, item)
        return self

    def profile(self, id):
        return self._profiles[id]

    def get_profile(self, id):
        return self._profiles.get(id)

    def new_profile(self, id):
        return self._profiles.setdefault(id, self.xccdf.profile(id))

    def append_group(self, item):
        self._groups.setdefault(item.xccdf_id, item)
        return self

    def group(self, id):
        return self._groups[id]

    def get_group(self, id):
        return self._groups.get(id)

    def new_group(self, id):
        return self._groups.setdefault(id, self.xccdf.group(id))

    def append_rule(self, item):
        self._rules.setdefault(item.xccdf_id, item)
        return self

    def append_value(self, item):
        self._values.setdefault(item.xccdf_id, item)
        return self

    def new_value(self, id):
        return self._values.setdefault(id, self.xccdf.value(id))

    def get_value(self, id):
        return self._values.get(id)

    def add_dc_metadata(self):
        metadata = self.xccdf.dc_metadata()
        self._dc_metadata = metadata
        return metadata

    def update_elements(self):
        super().update_elements()

        self.remove_elements(name='platform')
        for x in self._platforms:
            self.sub_element('platform').set_attr('idref', x)

        self.remove_elements(name='metadata')
        if self._dc_metadata:
            self.append(self._dc_metadata)

        self.remove_elements(name='version')
        self.append(XccdfVersionElement(self.xccdf, self.version))

        self.remove_elements(name='status')
        for x in self._status:
            self.append(x)

        self.remove_elements(name='Profile')
        for x in self._profiles.values():
            self.append(x)

        self.remove_elements(name='Value')
        for x in self._values.values():
            self.append(x)

        self.remove_elements(name='Group')
        for x in self._groups.values():
            self.append(x)

        self.remove_elements(name='Rule')
        for x in self._rules.values():
            self.append(x)


class XccdfTailoringElement(XccdfBase):
    __elements_order__ = (
        'status',
        'version',
        'Profile',
    )

    def __init__(self, xccdf, id, version='0.1'):
        super().__init__(generator=xccdf, name='Tailoring', id=id)
        self._profiles = OrderedDict()
        self._status = []
        self.version = version

    def append_profile(self, item):
        self._profiles.setdefault(item.xccdf_id, item)
        return self

    def add_profile(self, id):
        return self._profiles.setdefault(id, self.xccdf.profile(id))

    def set_status(self, status_string='draft', status_date=None):
        status = XccdfStatusElement(self.xccdf,
                                    status=status_string,
                                    timestamp=status_date)
        self._status.append(status)
        return self

    def append_status(self, item):
        self._status.append(item)
        return self

    def set_version(self, version=None):
        if version is not None:
            self.version = str(version)
        return self

    def update_elements(self):
        super().update_elements()

        self.remove_elements(name='Profile')
        for x in self._profiles.values():
            self.append(x)

        self.remove_elements(name='version')
        self.append(XccdfVersionElement(self.xccdf, self.version))

        self.remove_elements(name='status')
        for x in self._status:
            self.append(x)


class XccdfProfileElement(XccdfBase, SetTitleMixin, SetDescriptionMixin):
    SelectorKey = namedtuple('Key', ['selector', 'idref'])

    __elements_order__ = (
        'title',
        'description',
        'platform',
        'status',
        'select',
        'set-value',
        'set-complex-value',
        'refine-value',
        'refine-rule',
    )

    def __init__(self, xccdf, id):
        super().__init__(generator=xccdf, name='Profile', id=id)
        self._selectors = OrderedDict()
        self._status = []
        self._platforms = set()

    @property
    def platforms(self):
        return self._platforms

    def add_platform(self, name):
        self._platforms.add(name)
        return self

    def set_status(self, status='draft', status_date=None):
        self._status.append(XccdfStatusElement(status=status,
                                               timestamp=status_date))
        return self

    def append_status(self, item):
        self._status.append(item)
        return self

    def set_version(self, version):
        self.sub_element('version').set_text(version)

    def selector(self, selector, idref, **kwargs):
        key = self.SelectorKey(selector, idref)
        if selector == 'select':
            self._selectors[key] = XccdfBoolean.parse(kwargs['selected'])
        elif selector == 'set-value':
            self._selectors[key] = kwargs['value']
        return self

    def select_item(self, rule, selected=False):
        return self.selector('select', rule.xccdf_id, selected=selected)

    def update_elements(self):
        super().update_elements()

        self.remove_elements(name='select')
        self.remove_elements(name='set-value')

        self.remove_elements(name='platform')
        for x in self._platforms:
            self.sub_element('platform').set_attr('idref', x)

        self.remove_elements(name='status')
        for x in self._status:
            self.append(x)

        for key, value in self._selectors.items():
            if key.selector == 'select':
                self.sub_element('select') \
                    .set_attr('idref', key.idref) \
                    .set_attr('selected', str(value))
            elif key.selector == 'set-value':
                self.sub_element('set-value') \
                    .set_attr('idref', key.idref) \
                    .set_text(value)


class XccdfGroupElement(XccdfBase, SetTitleMixin, SetDescriptionMixin):
    __elements_order__ = (
        'title',
        'description',
    )

    def __init__(self, xccdf, id):
        super().__init__(generator=xccdf, name='Group', id=id)
        self._selected = XccdfBoolean.FALSE
        self._rules = []
        self._profiles = OrderedDict()

    @property
    def profiles(self):
        return self._profiles.items()

    def add_to_profile(self, name, selected=False):
        profile = self._profiles.setdefault(name, {})
        profile['selected'] = selected
        return self

    def append_rule(self, rule):
        self._rules.append(rule)
        return rule

    def add_rule(self, id):
        rule = self.xccdf.rule(id)
        self._rules.append(rule)
        return rule

    def selected(self, selected=True):
        self._selected = XccdfBoolean.parse(selected)

    def update_elements(self):
        super().update_elements()
        self.set_attr('selected', str(self._selected))

        self.remove_elements(name='Rule')
        for x in self._rules:
            self.append(x)


class XccdfRuleElement(XccdfBase, SetTitleMixin, SetDescriptionMixin):
    __elements_order__ = (
        'title',
        'description',
        'reference',
        'rationale',
        'ident',
        'check',
    )

    def __init__(self, xccdf, id, severity='medium'):
        super().__init__(generator=xccdf, name='Rule', id=id)
        self.set_attr('severity', severity)
        self._selected = XccdfBoolean.FALSE
        self._checks = []
        self._references = []
        self._dc_references = []
        self._profiles = {}
        self.group = None

    @property
    def profiles(self):
        return self._profiles.items()

    def add_to_profile(self, name, selected=False):
        profile = self._profiles.setdefault(name, {})
        profile['selected'] = selected
        return self

    def add_check(self, **kwargs):
        check = self.xccdf.check(**kwargs)
        self._checks.append(check)
        return check

    def add_reference(self, name, href=None):
        ref = self.sub_element('reference').set_text(name)
        if href:
            ref.set_attr('href', href)
        self._references.append(ref)
        return ref

    def add_dc_reference(self):
        ref = XccdfReferenceElement(self.xccdf)
        self._dc_references.append(ref)
        return ref

    def add_ident(self, name, system):
        ident = self.sub_element('ident')\
            .set_text(name)\
            .set_attr('system', system)
        return ident

    def set_rationale(self, text):
        self.sub_element('rationale')\
            .set_object(MarkdownHtml(text))
        return self

    def selected(self, selected=True):
        self._selected = XccdfBoolean.parse(selected)

    def update_elements(self):
        self.set_attr('id', self.xccdf_id)
        self.set_attr('selected', str(self._selected))

        self.remove_elements(name='check')
        for x in self._checks:
            self.append(x)

        self.remove_elements(name='reference')
        for x in self._references:
            self.append(x)

        for x in self._dc_references:
            self.append(x)


class XccdfCheckElement(XmlBase):
    __elements_order__ = (
        'check-import',
        'check-export',
        'check-content',
        'check-content-ref',
    )

    def __init__(self, xccdf, id=None, system_ns='oval-def'):
        super().__init__('check')
        self.xccdf = xccdf
        if id:
            self.set_attr('id', id)
        self.set_attr('system', self.namespace(system_ns))

    def check_import(self, import_name, import_xpath=None):
        element = self.sub_element('check-import')\
            .set_attr('import-name', import_name)
        if import_xpath:
            element.set_attr('import-xpath', import_xpath)
        return self

    def check_export(self, value_id, export_name):
        self.sub_element('check-export')\
            .set_attr('value-id', value_id)\
            .set_attr('export-name', export_name)
        return self

    def check_content_ref(self, href, name=None):
        element = self.sub_element('check-content-ref')\
            .set_attr('href', href)
        if name:
            element.set_attr('name', name)
        return self


class XccdfValueElement(XccdfBase, SetTitleMixin, SetDescriptionMixin):
    __elements_order__ = (
        'title',
        'description',
        'value',
        'default',
        'match',
        'lower-bound',
        'upper-bound',
    )

    def __init__(self, xccdf, id):
        super().__init__(generator=xccdf, name='Value', id=id)
        self._value = OrderedDict()
        self._default_value = OrderedDict()
        self._match = OrderedDict()
        self._lower_bound = OrderedDict()
        self._upper_bound = OrderedDict()

    def set_value(self, value, selector=None):
        if selector in self._value:
            raise Exception("Value with selector '{}' already set"
                            .format(selector))
        element = self.sub_element('value').set_text(str(value))
        if selector is not None:
            element.set_attr('selector', selector)
        self._value[selector] = element
        return self

    def set_default(self, value, selector=None):
        if selector in self._default_value:
            raise Exception("Default value with selector '{}' already set"
                            .format(selector))
        element = self.sub_element('default').set_text(str(value))
        if selector is not None:
            element.set_attr('selector', selector)
        self._default_value[selector] = element

    def set_match(self, value, selector=None):
        if selector in self._match:
            raise Exception("Match with selector '{}' already set"
                            .format(selector))
        element = self.sub_element('value').set_text(str(value))
        if selector is not None:
            element.set_attr('selector', selector)
        self._match[selector] = element

    def set_lower_bound(self, value, selector=None):
        if selector in self._lower_bound:
            raise Exception("Lower bound with selector '{}' already set"
                            .format(selector))
        element = self.sub_element('lower-bound').set_text(str(value))
        if selector is not None:
            element.set_attr('selector', selector)
        self._lower_bound[selector] = element

    def set_upper_bound(self, value, selector=None):
        if selector in self._upper_bound:
            raise Exception("Upper bound with selector '{}' already set"
                            .format(selector))
        element = self.sub_element('upper-bound').set_text(str(value))
        if selector is not None:
            element.set_attr('selector', selector)
        self._upper_bound[selector] = element

    def set_type(self, value):
        self.set_attr('type', value.lower())
        return self

    def set_operator(self, value):
        allowed_operator_values = ['equals', 'not equal', 'less than',
                                   'greater than', 'less than or equal',
                                   'greater than or equal', 'pattern match']
        if value in allowed_operator_values:
            self.set_attr('operator', value.lower())
        else:
            raise Exception("Bad operator {}, not in {}"
                            .format(value, allowed_operator_values))
        return self

    def update_elements(self):
        super().update_elements()

        self.remove_elements(name='value')
        for x in self._value.values():
            self.append(x)

        self.remove_elements(name='default')
        for x in self._default_value.values():
            self.append(x)

        self.remove_elements(name='match')
        for x in self._match.values():
            self.append(x)

        self.remove_elements(name='lower-bound')
        for x in self._lower_bound.values():
            self.append(x)

        self.remove_elements(name='upper-bound')
        for x in self._upper_bound.values():
            self.append(x)


class XccdfStatusElement(XmlBase):
    valid_statuses = (
        'incomplete', 'draft', 'interim', 'accepted', 'deprecated'
    )

    def __init__(self, xccdf, status='draft', timestamp=None):
        super().__init__('status')
        self.xccdf = xccdf
        self.set_attr('date', self._timestamp(timestamp))
        if status in self.valid_statuses:
            self.set_text(status)
        else:
            raise Exception("Status '{}' is not valid. "
                            "Valid statuses are {}"
                            .format(status, self.valid_statuses))

    def _timestamp(self, timestamp):
        if timestamp is None:
            timestamp = datetime.datetime.now()
        elif isinstance(timestamp, str):
            timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%d")

        return datetime.datetime.strftime(timestamp, "%Y-%m-%d")


class XccdfVersionElement(XmlBase):
    def __init__(self, xccdf, version, timestamp=None):
        super().__init__('version')
        self.xccdf = xccdf
        self.set_attr('time', self._timestamp(timestamp))
        self.set_text(version)

    def _timestamp(self, timestamp):
        if timestamp is None:
            timestamp = datetime.datetime.now()
        elif isinstance(timestamp, str):
            timestamp = datetime.datetime.strptime(timestamp,
                                                   "%Y-%m-%d %H:%M:%S")

        return datetime.datetime.strftime(timestamp, "%Y-%m-%dT%H:%M:%S")


class XccdfReferenceElement(XccdfDublinCoreElement):
    def __init__(self, xccdf):
        super().__init__('reference')
        self.xccdf = xccdf


class XccdfMetadataElement(XccdfDublinCoreElement):
    def __init__(self, xccdf):
        super().__init__('metadata')
        self.xccdf = xccdf
