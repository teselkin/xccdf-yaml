import base64
import html
import os
import textwrap
import zlib

import lxml.etree as etree


from collections import OrderedDict
from xccdf_yaml.common import SharedFiles
from xccdf_yaml.misc import unlist
from xccdf_yaml.xccdf.elements import XccdfGenerator

from xccdf_yaml.xccdf.check import PARSERS



class XccdfYamlParser(object):
    def __init__(self, generator, benchmark=None):
        self._items = OrderedDict()
        self.generator = generator
        self.benchmark = benchmark

    def __len__(self):
        return len(self._items)

    def __getitem__(self, key):
        if isinstance(key, int):
            key = list(self._items.keys())[key]
        return self._items[key]

    def __iter__(self):
        for item in self._items.values():
            yield item

    def append(self, item):
        item_id = item.get_attr('id')
        self._items.setdefault(item_id, item)


class XccdfYamlProfileParser(XccdfYamlParser):
    def parse(self, id, data):
        if id is None:
            id = data['id']

        profile = self.generator.profile(id)
        self._parse(profile, data)
        self.append(profile)

    def _parse(self, profile, data):
        """
        - profile_id:
            abstract: true | false
            extends: ''
            status: ''
            version: ''
            title: ''
            description: ''
            references:
              - ''
            platforms:
              - ''
            metadata:
              - ''
            selectors:
              - select:
                  'id':
                    selected: true | false
                    remark:
                      - ''
              - set-value:
                  'id': value
              - set-complex-value:
                  'id':
                    - value
              - refine-value:
                  'id':
                    remark:
                      - ''
                    selector:
              - refine-rule:
                  'id': value
        """

        if 'abstract' in data:
            profile.set_attr('abstract', data['abstract'])

        if 'extends' in data:
            profile.set_attr('extends', data['extends'])

        if 'status' in data:
            profile.set_status(data['status'])

        if 'version' in data:
            profile.set_version(data['version'])

        if 'title' in data:
            profile.set_title(data['title'])

        if 'description' in data:
            profile.set_description(data['description'])

        for item in data.get('selectors', []):
            for selector_name, selector_data in item.items():
                for idref, params in selector_data.items():
                    if selector_name == 'select':
                        target, idref = idref.split(':', 1)
                        if isinstance(params, dict):
                            profile.selector('select',
                                             self.generator.id(target, idref),
                                             selected=params['selected'])
                        else:
                            profile.selector('select',
                                             self.generator.id(target, idref),
                                             selected=params)
                    elif selector_name == 'set-value':
                        profile.selector('set-value',
                                         self.generator.id('value', idref),
                                         value=params)

class XccdfYamlValueParser(XccdfYamlParser):
    """
    - value_id:
        type: string
        operator: match
        value: value2_123
        default: value2_456
        title: value2_title
        description: value2_description
        lower-bound: value2_lower_bound
        lower-bound:
          low: value2_lower_bound_low
          high: value2_lower_bound_high
        upper-bound: value2_upper_bound
        upper-bound:
          low: value2_upper_bound_low
          high: value2_upper_bound_high

    """
    def parse(self, id, data):
        if id is None:
            id = data['id']

        value = self.generator.value(id)
        self._parse(value, data)
        self.append(value)

    def _parse(self, value_obj, data):
        value = data.get('value')
        value_type = data.get('type', 'string')

        if 'title' in data:
            value_obj.set_title(data['title'])

        if 'description' in data:
            value_obj.set_description(data['description'])
        else:
            if value_type == 'code':
                value_obj.set_description(value, plaintext=True)

        if value_type == 'code':
            value_obj.set_attr('type', 'string')
            value = textwrap.fill(base64.b64encode(
                zlib.compress(value.encode())).decode(), 120)
        else:
            value_obj.set_attr('type', value_type)

        value_obj.set('value', value)

        for key in ['operator',]:
            if key in data:
                value_obj.set_attr(key, data[key])

        for key in ['default', 'lower-bound', 'upper-bound']:
            item = data.get(key)
            if isinstance(item, list):
                for x in item:
                    for selector, value in x.items():
                        value_obj.set(key, value, selector=selector)
            elif item is not None:
                value_obj.set(key, str(item))


class XccdfYamlRuleParser(XccdfYamlParser):
    """
    - test_bin_true:
        type: sce
        template: <template name>
        title: &test_bin_true_title
          "Test /bin/true"
        description: |
          This is a test script
        rationale: |
          Test script rationale
        reference:
          - ref1
          - text: Let me Google it for you
        url: 'http://google.com'
          -
            text: *test_bin_true_title
            url: 'https://www.google.ru/search?q=qwe'
        export:
          - value_1
          - value_2: value2
        check:
          engine: python
          codeblock: |
            <code>
    """
    def __init__(self, generator, benchmark, parsed_args=None,
                 shared_files=None):
        super(XccdfYamlRuleParser, self).__init__(generator, benchmark)
        self.parsed_args = parsed_args
        self.shared_files = shared_files

    def parse(self, id, data):
        if id is None:
            id = data['id']

        rule = self.generator.rule(id)
        self._parse(rule, data)
        self.append(rule)

    def _parse(self, rule, data):
        if 'title' in data:
            rule.set_title(data['title'])

        if 'description' in data:
            rule.set_description(data['description'])

        if 'rationale' in data:
            rule.set_rationale(data['rationale'])

        for ident_name, ident_system in data.get('ident', {}).items():
            rule.add_ident(ident_name, ident_system)

        for reference in data.get('reference', []):
            if isinstance(reference, dict):
                rule.add_reference(reference['text'],
                                   href=reference.get('url'))
            else:
                rule.add_reference(reference)

        for reference in data.get('dc-reference', []):
            ref = rule.add_dc_reference()
            for element_name, element_value in reference.items():
                if element_name == 'href':
                    ref.set_attr('href', element_value)
                else:
                    ref.sub_element(element_name).set_text(element_value)

        for profile in data.get('profiles', []):
            if isinstance(profile, dict):
                profile_name, profile_data = next(iter(profile.items()))
                rule.add_to_profile(
                    name=profile_name,
                    selected=profile_data.get('selected', False)
                )
            else:
                rule.add_to_profile(name=profile, selected=True)

        platforms = list(self.benchmark.platforms)
        if platforms and not data.get('affected', False):
            data['affected'] = platforms

        # if 'variable' in data:
        #     data['external-variables'] = variables_types

        parser = PARSERS[data.get('type', 'sce')](
            self.generator, self.benchmark,
            parsed_args=self.parsed_args, shared_files=self.shared_files)

        parser.parse(rule, data)


class XccdfYamlBenchmarkParser(XccdfYamlParser):
    def __init__(self, generator, basedir, workdir):
        super(XccdfYamlBenchmarkParser, self).__init__(generator)
        self.basedir = basedir
        self.workdir = workdir
        self.shared_files = SharedFiles(basedir=basedir, workdir=workdir)
        self.filename = None

    def parse(self, id, data):
        if id is None:
            id = data['id']

        self.benchmark = self.generator.benchmark(id)
        self._parse(self.benchmark, data)
        return self.benchmark

    def _parse(self, benchmark, data):
        benchmark.set_title(data.get('title'))
        benchmark.set_description(data.get('description'))

        platform = data.get('platform')
        if platform:
            if isinstance(platform, list):
                for platform_str in platform:
                    benchmark.add_platform(platform_str.rstrip())
            else:
                benchmark.add_platform(platform.rstrip())

        dc_metadata = data.get('dc-metadata', {})
        if dc_metadata:
            metadata = benchmark.add_dc_metadata()
            for name, values in dc_metadata.items():
                if isinstance(values, list):
                    for value in values:
                        metadata.sub_element(name).set_text(html.escape(value))
                else:
                    metadata.sub_element(name).set_text(html.escape(values))

        # Import profiles

        profiles = XccdfYamlProfileParser(self.generator, benchmark)

        profiles_data = data.get('profiles', [{
            'default': {
                'title': 'Default Profile',
            }
        }, ])

        for profile_map in profiles_data:
            for profile_id, profile_data in profile_map.items():
                profiles.parse(profile_id, profile_data)

        if len(profiles) > 1:
            default_profile = None
        else:
            default_profile = profiles[0]

        for profile in profiles:
            self.benchmark.append_profile(profile)

        # Import groups

        group_info = data.get('group', {
            'id': 'default',
            'title': 'Default Group'
        })

        group = self.benchmark\
            .new_group(group_info.get('id'))\
            .set_title(group_info.get('title'))

        # Import values

        values = XccdfYamlValueParser(self.generator, benchmark)
        for value_map in data.get('values', []):
            for value_id, value_data in value_map.items():
                values.parse(value_id, value_data)
        for value in values:
            benchmark.append_value(value)

        # Import shared files

        for item in data.get('shared-files', []):
            if isinstance(item, dict):
                for filename, source in item.items():
                    self.shared_files.from_source(source=source,
                                                  filename=filename)
            else:
                self.shared_files.from_source(source=item)

        # Import rules

        rules = XccdfYamlRuleParser(self.generator, benchmark,
                                    shared_files=self.shared_files)
        for rule_map in unlist(data.get('rules', [])):
            for rule_id, rule_data in rule_map.items():
                rules.parse(rule_id, rule_data)

        for rule in rules:
            group.append_rule(rule)
            if default_profile:
                default_profile.append_rule(rule)
            else:
                for profile_name, profile_data in rule.profiles:
                    profile = benchmark.get_profile(
                        self.generator.id('profile', profile_name))
                    if profile:
                        profile.append_rule(
                            rule, selected=profile_data.get('selected', False))

    def export(self, output_dir, output_file=None, unescape=False):
        self.shared_files.export(output_dir)

        benchmark_xml = self.benchmark.xml()
        benchmark_xml_str = etree.tostring(benchmark_xml,
                                           pretty_print=True).decode()

        if unescape:
            benchmark_xml_str = html.unescape(benchmark_xml_str)

        # if not oval.is_empty():
        #     oval_filename = os.path.join(output_dir, oval_ref)
        #     oval_xml = oval.xml()
        #     oval_xml_str = etree.tostring(oval_xml,
        #                                   pretty_print=True).decode()
        #     with open(oval_filename, 'w') as f:
        #         f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        #         f.write(oval_xml_str)

        if output_file is None:
            output_file = os.path.join(
                output_dir,
                '{}-xccdf.xml'.format(self.benchmark.get_attr('id'))
            )
        else:
            output_file = os.path.join(output_dir, output_file)

        with open(output_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(benchmark_xml_str)

        return output_file


class XccdfYamlTailoringParser(XccdfYamlParser):
    def __init__(self, generator, basedir, workdir):
        super(XccdfYamlTailoringParser, self).__init__(generator)
        self.basedir = basedir
        self.workdir = workdir
        self.shared_files = SharedFiles(basedir=basedir, workdir=workdir)
        self.filename = None

    def parse(self, id, data):
        if id is None:
            id = data['id']

        self.tailoring = self.generator.tailoring(id)
        self._parse(self.tailoring, data)
        return self.tailoring

    def _parse(self, tailoring, data):
        if 'version' in data:
            tailoring.set_version(data['version'])

        for status in data.get('status', []):
            tailoring.set_status(status.get('status'), status.get('date'))

        # Import profiles

        profiles = XccdfYamlProfileParser(self.generator, tailoring)

        profiles_data = data.get('profiles', [{
            'default': {
                'title': 'Default Profile',
            }
        }, ])

        for profile_map in profiles_data:
            for profile_id, profile_data in profile_map.items():
                profiles.parse(profile_id, profile_data)

        for profile in profiles:
            self.tailoring.append_profile(profile)

    def export(self, output_dir, output_file=None, unescape=False):
        os.makedirs(output_dir, exist_ok=True)

        self.shared_files.export(output_dir)

        benchmark_xml = self.tailoring.xml()
        benchmark_xml_str = etree.tostring(benchmark_xml,
                                           pretty_print=True).decode()

        if unescape:
            benchmark_xml_str = html.unescape(benchmark_xml_str)

        if output_file is None:
            output_file = os.path.join(
                output_dir,
                '{}-xccdf.xml'.format(self.tailoring.get_attr('id'))
            )
        else:
            output_file = os.path.join(output_dir, output_file)

        with open(output_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(benchmark_xml_str)

        return output_file
