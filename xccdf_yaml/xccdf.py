import lxml.etree as etree
import markdown


from xccdf_yaml.xml import XmlCommon
from xccdf_yaml.xml import set_default_ns


NSMAP = {
    None: "http://checklists.nist.gov/xccdf/1.1",
    'oval-def': "http://oval.mitre.org/XMLSchema/oval-definitions-5",
    'sce': "http://open-scap.org/page/SCE",
    'sceres': "http://open-scap.org/page/SCE_result_file",
    'xsi': "http://www.w3.org/2001/XMLSchema-instance",
}


class XmlBase(XmlCommon):
    def __init__(self, name, ns=None):
        super().__init__(name, ns=ns, nsmap=NSMAP)


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


class Benchmark(XmlBase, SetTitleMixin, SetDescriptionMixin):
    __elements_order__ = (
        'status',
        'title',
        'description',
        'platform',
        'version',
        'metadata',
        'Profile',
        'Group',
        'Value',
        'Rule',
    )

    def __init__(self, id, version='0.1', status='draft', status_date=None):
        super().__init__('Benchmark')
        self._profiles = []
        self._groups = []
        self.set_attr('id', id)
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
        profile = BenchmarkProfile(id)
        self._profiles.append(profile)
        return profile

    def add_group(self, id):
        group = BenchmarkGroup(id)
        self._groups.append(group)
        return group

    def update_elements(self):
        self.remove_elements(name='Profile')
        for x in self._profiles:
            self.append(x)

        self.remove_elements(name='Group')
        for x in self._groups:
            self.append(x)


class BenchmarkProfile(XmlBase, SetTitleMixin, SetDescriptionMixin):
    __elements_order__ = (
        'title',
        'description',
        'select',
    )

    def __init__(self, id):
        super().__init__('Profile')
        self.set_attr('id', id)
        self._rules = []

    def append_rule(self, rule, selected=False):
        self._rules.append((rule, selected))
        return self

    def update_elements(self):
        self.remove_elements(name='select')
        for rule, selected in self._rules:
            self.sub_element('select').set_attrs({
                'idref': rule.get_attr('id'),
                'selected': {True: '1', False: '0'}.get(selected, '0')
            })


class BenchmarkGroup(XmlBase, SetTitleMixin, SetDescriptionMixin):
    __elements_order__ = (
        'title',
        'description',
    )

    def __init__(self, id):
        super().__init__('Group')
        self.set_attr('id', id)
        self._rules = []

    def append_rule(self, rule):
        self._rules.append(rule)
        return rule

    def add_rule(self, id):
        rule = BenchmarkRule(id)
        self._rules.append(rule)
        return rule

    def update_elements(self):
        self.remove_elements(name='Rule')
        for x in self._rules:
            self.append(x)


class BenchmarkRule(XmlBase, SetTitleMixin, SetDescriptionMixin):
    __elements_order__ = (
        'title',
        'description',
        'reference',
        'rationale',
        'check',
    )

    def __init__(self, id, selected=False, severity='medium'):
        super().__init__('Rule')
        self.set_attrs({
            'id': id,
            'severity': severity,
            'selected': {True: '1', False: '0'}.get(selected, '0'),
        })
        self._checks = []

    def add_check(self, **kwargs):
        check = XccdfCheck(**kwargs)
        self._checks.append(check)
        return check

    def update_elements(self):
        self.remove_elements(name='check')
        for x in self._checks:
            self.append(x)


class XccdfCheck(XmlBase):
    __elements_order__ = (
        'check-import',
        'check-content',
        'check-content-ref',
    )

    def __init__(self, id=None, system_ns='oval-def'):
        super().__init__('check')
        if id:
            self.set_attr('id', id)
        self.set_attr('system', self.namespace(system_ns))

    def check_import(self, *args, **kwargs):
        attrs = dict(zip(('attrs',), args)).get('attrs', {})
        attrs.update(kwargs)
        self.sub_element('check-import').set_attrs(attrs)
        return self

    def check_content_ref(self, *args, **kwargs):
        attrs = dict(zip(('attrs',), args)).get('attrs', {})
        attrs.update(kwargs)
        self.sub_element('check-content-ref').set_attrs(attrs)
        return self
