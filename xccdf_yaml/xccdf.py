import lxml.etree as etree
import markdown
import re

from collections import OrderedDict
from xccdf_yaml.xml import XmlCommon
from xccdf_yaml.xml import DublinCoreElementBase
from xccdf_yaml.xml import set_default_ns


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
    def set_description(self, text):
        if text is not None:
            content = etree.fromstring(markdown.markdown(text.rstrip()))
            content = set_default_ns(
                content, default_ns='xhtml',
                nsmap={'xhtml': 'http://www.w3.org/1999/xhtml'})
            self.sub_element('description')\
                .set_text(etree.tostring(content, pretty_print=True))
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
        return XccdfBenchmark(self, *args, **kwargs)

    def profile(self, *args, **kwargs):
        return XccdfProfile(self, *args, **kwargs)

    def group(self, *args, **kwargs):
        return XccdfGroup(self, *args, **kwargs)

    def rule(self, *args, **kwargs):
        return XccdfRule(self, *args, **kwargs)

    def value(self, *args, **kwargs):
        return XccdfValue(self, *args, **kwargs)

    def check(self, *args, **kwargs):
        return XccdfCheck(self, *args, **kwargs)

    def dc_metadata(self, *args, **kwargs):
        return XccdfMetadata(self, *args, **kwargs)


class XccdfBenchmark(XmlBase, SetTitleMixin, SetDescriptionMixin):
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

    def __init__(self, xccdf, id, version='0.1', status='draft',
                 status_date=None):
        super().__init__('Benchmark')
        self.xccdf = xccdf
        self._profiles = OrderedDict()
        self._groups = OrderedDict()
        self._values = OrderedDict()
        self._dc_metadata = None
        self.set_attr('id', self.xccdf.id('benchmark', id))
        self.set_status(status, status_date)
        self.set_version(version)

    def set_status(self, status='draft', status_date=None):
        element = self.sub_element('status').set_text(status)
        if status_date:
            element.set_attr('date', status_date)
        return self

    def set_version(self, version):
        self.sub_element('version').set_text(version)

    def add_platform(self, name):
        self.sub_element('platform').set_attr('idref', name)
        return self

    def add_profile(self, id):
        return self._profiles.setdefault(id, self.xccdf.profile(id))

    def add_group(self, id):
        return self._groups.setdefault(id, self.xccdf.group(id))

    def new_value(self, id):
        return self._values.setdefault(id, self.xccdf.value(id))

    def add_dc_metadata(self):
        metadata = self.xccdf.dc_metadata()
        self._dc_metadata = metadata
        return metadata

    def update_elements(self):
        self.remove_elements(name='metadata')
        if self._dc_metadata:
            self.append(self._dc_metadata)

        self.remove_elements(name='Profile')
        for x in self._profiles.values():
            self.append(x)

        self.remove_elements(name='Value')
        for x in self._values.values():
            self.append(x)

        self.remove_elements(name='Group')
        for x in self._groups.values():
            self.append(x)


class XccdfProfile(XmlBase, SetTitleMixin, SetDescriptionMixin):
    __elements_order__ = (
        'title',
        'description',
        'select',
    )

    def __init__(self, xccdf, id):
        super().__init__('Profile')
        self.xccdf = xccdf
        self.set_attr('id', self.xccdf.id('profile', id))
        self._rules = []

    def append_rule(self, rule, selected=False):
        self._rules.append((rule, selected))
        return self

    def update_elements(self):
        self.remove_elements(name='select')
        for rule, selected in self._rules:
            self.sub_element('select')\
                .set_attr('idref', rule.get_attr('id'))\
                .set_attr('selected',
                          {True: '1', False: '0'}.get(selected, '0'))


class XccdfGroup(XmlBase, SetTitleMixin, SetDescriptionMixin):
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


class XccdfRule(XmlBase, SetTitleMixin, SetDescriptionMixin):
    __elements_order__ = (
        'title',
        'description',
        'reference',
        'ident',
        'rationale',
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
        ref = XccdfReference(self.xccdf)
        self._dc_references.append(ref)
        return ref

    def add_ident(self, name, system):
        ident = self.sub_element('ident')\
            .set_text(name)\
            .set_attr('system', system)
        return ident

    def update_elements(self):
        self.remove_elements(name='check')
        for x in self._checks:
            self.append(x)

        self.remove_elements(name='reference')
        for x in self._references:
            self.append(x)
        for x in self._dc_references:
            self.append(x)


class XccdfCheck(XmlBase):
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


class XccdfValue(XmlBase, SetTitleMixin, SetDescriptionMixin):
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
        self.set_title(self.get_attr('id'))
        self.set_description(self.get_attr('id'))

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


class XccdfReference(XccdfDublinCoreElement):
    def __init__(self, xccdf):
        super().__init__('reference')
        self.xccdf = xccdf


class XccdfMetadata(XccdfDublinCoreElement):
    def __init__(self, xccdf):
        super().__init__('metadata')
        self.xccdf = xccdf
