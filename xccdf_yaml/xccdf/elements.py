import datetime
import re

from collections import namedtuple, OrderedDict
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


class XmlBase(XmlCommon):
    def __init__(self, name, ns=None):
        super().__init__(name, ns=ns, nsmap=NSMAP)


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
                .set_text(str(MarkdownHtml(text, plaintext=plaintext)))
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


class XccdfBenchmarkElement(XmlBase, SetTitleMixin, SetDescriptionMixin):
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
        super().__init__('Benchmark')
        self.xccdf = xccdf
        self.set_attr('id', self.xccdf.id('benchmark', id))
        self._platforms = set()
        self._profiles = OrderedDict()
        self._groups = OrderedDict()
        self._values = OrderedDict()
        self._dc_metadata = None
        self._version = XccdfVersionElement(self.xccdf, version)
        self._status = []

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
        if version:
            self._version = XccdfVersionElement(self.xccdf, version)
        return self

    def add_platform(self, name):
        self._platforms.add(name)
        # self.sub_element('platform').set_attr('idref', name)
        return self

    def append_profile(self, item):
        self._profiles.setdefault(item.get_attr('id'), item)
        return self

    def get_profile(self, id):
        return self._profiles.get(id)

    def new_profile(self, id):
        return self._profiles.setdefault(id, self.xccdf.profile(id))

    def new_group(self, id):
        return self._groups.setdefault(id, self.xccdf.group(id))

    def append_value(self, item):
        self._values.setdefault(item.get_attr('id'), item)
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
        self.remove_elements(name='platform')
        for x in self._platforms:
            self.sub_element('platform').set_attr('idref', x)

        self.remove_elements(name='metadata')
        if self._dc_metadata:
            self.append(self._dc_metadata)

        self.remove_elements(name='version')
        self.append(self._version)

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


class XccdfTailoringElement(XmlBase):
    __elements_order__ = (
        'status',
        'version',
        'Profile',
    )

    def __init__(self, xccdf, id, version='0.1'):
        super().__init__('Tailoring')
        self.xccdf = xccdf
        self.set_attr('id', self.xccdf.id('tailoring', id))
        self._profiles = OrderedDict()
        self._version = XccdfVersionElement(self.xccdf, version)
        self._status = []

    def append_profile(self, item):
        self._profiles.setdefault(item.get_attr('id'), item)
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
        if version:
            self._version = XccdfVersionElement(self.xccdf, version)
        return self

    def update_elements(self):
        self.remove_elements(name='Profile')
        for x in self._profiles.values():
            self.append(x)

        self.remove_elements(name='version')
        self.append(self._version)

        self.remove_elements(name='status')
        for x in self._status:
            self.append(x)


class XccdfProfileElement(XmlBase, SetTitleMixin, SetDescriptionMixin):
    SelectorKey = namedtuple('Key', ['selector', 'idref'])

    __elements_order__ = (
        'title',
        'description',
        'status',
        'select',
        'set-value',
        'set-complex-value',
        'refine-value',
        'refine-rule',
    )

    def __init__(self, xccdf, id):
        super().__init__('Profile')
        self.xccdf = xccdf
        self.set_attr('id', self.xccdf.id('profile', id))
        self._selectors = OrderedDict()
        self._status = []

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
            self._selectors[key] = kwargs['selected']
        elif selector == 'set-value':
            self._selectors[key] = kwargs['value']
        return self

    def append_rule(self, rule, selected=False):
        return self.selector('select', rule.get_attr('id'), selected=selected)

    def update_elements(self):
        self.remove_elements(name='select')
        self.remove_elements(name='set-value')

        self.remove_elements(name='status')
        for x in self._status:
            self.append(x)

        for key, value in self._selectors.items():
            if key.selector == 'select':
                self.sub_element('select') \
                    .set_attr('idref', key.idref) \
                    .set_attr('selected', {True: '1', False: '0'}
                              .get(value, '0'))
            elif key.selector == 'set-value':
                self.sub_element('set-value') \
                    .set_attr('idref', key.idref) \
                    .set_text(value)


class XccdfGroupElement(XmlBase, SetTitleMixin, SetDescriptionMixin):
    __elements_order__ = (
        'title',
        'description',
    )

    def __init__(self, xccdf, id):
        super().__init__('Group')
        self.xccdf = xccdf
        self.set_attr('id', self.xccdf.id('group', id))
        self._rules = []

    def append_rule(self, rule):
        self._rules.append(rule)
        return rule

    def add_rule(self, id):
        rule = self.xccdf.rule(id)
        self._rules.append(rule)
        return rule

    def update_elements(self):
        self.remove_elements(name='Rule')
        for x in self._rules:
            self.append(x)


class XccdfRuleElement(XmlBase, SetTitleMixin, SetDescriptionMixin):
    __elements_order__ = (
        'title',
        'description',
        'reference',
        'rationale',
        'ident',
        'check',
    )

    def __init__(self, xccdf, id, selected=False, severity='medium'):
        super().__init__('Rule')
        self.xccdf = xccdf
        self.set_attr('id', self.xccdf.id('rule', id))
        self.set_attr('selected', {True: '1', False: '0'}.get(selected, '0'))
        self.set_attr('severity', severity)
        self._checks = []
        self._references = []
        self._dc_references = []
        self._profiles = {}

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
            .set_text(str(MarkdownHtml(text)))
        return self

    def update_elements(self):
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


class XccdfValueElement(XmlBase, SetTitleMixin, SetDescriptionMixin):
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
        super().__init__('Value')
        self.xccdf = xccdf
        self._value = OrderedDict()
        self._default_value = OrderedDict()
        self._match = OrderedDict()
        self._lower_bound = OrderedDict()
        self._upper_bound = OrderedDict()
        self.set_attr('id', self.xccdf.id('value', id))
        # self.set_title(self.get_attr('id'))
        # self.set_description(self.get_attr('id'))

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
