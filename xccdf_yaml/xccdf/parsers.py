import base64
import html
import os
import textwrap
import zlib

import lxml.etree as etree


from collections import OrderedDict
from xccdf_yaml.common import SharedFiles
from xccdf_yaml.misc import unlist
# from xccdf_yaml.xccdf.elements import XccdfGenerator

from xccdf_yaml.oval.parsers import PARSERS as OVAL_PARSERS
from xccdf_yaml.xccdf.check import PARSERS as XCCDF_PARSERS


class StatusParserMixin(object):
    """
    status:
      - value: <status string>
        timestamp: "YYYY-MM-DD HH:MM:SS"

    """

    def _parse_status(self, data):
        items = []

        for list_item in data:
            items.append(
                self.generator.status(status=list_item['value'],
                                      timestamp=list_item.get('date')))

        return items


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


class XccdfYamlProfileParser(XccdfYamlParser, StatusParserMixin):
    def parse(self, data):
        profile = self.generator.profile(data['id'])
        self._parse(profile, data)
        self.append(profile)

    def _parse(self, profile, data):
        """
        id: <profile id>
        abstract: true | false
        extends: ''
        status:
          - value: <status string>
            timestamp: "YYYY-MM-DD HH:MM:SS"
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
              id: <item id>
              target: rule | ???
              selected: true | false
              remark:
                - ''
          - set-value:
              id: <item id>
              value: <item value>
          - set-complex-value:
              id: <item id>
              value: <item value>
          - refine-value:
              id: <item id>
              remark:
                - ''
              selector:
          - refine-rule:
              id: <item id>
              value: <item value>
        """

        if 'abstract' in data:
            profile.set_attr('abstract', data['abstract'])

        if 'extends' in data:
            profile.set_attr('extends',
                             self.generator.id('profile', data['extends']))

        for status in self._parse_status(data.get('status', [])):
            profile.append_status(status)

        if 'version' in data:
            profile.set_version(data['version'])

        if 'title' in data:
            profile.set_title(data['title'])

        if 'description' in data:
            profile.set_description(data['description'])

        for platform in data.get('platforms', []):
            profile.add_platform(platform.rstrip())

        for item in data.get('selectors', []):
            for selector_name, selector_params in item.items():
                if selector_name == 'select':
                    profile.selector(
                        'select',
                        self.generator.id(
                            selector_params.get('target', 'rule'),
                            selector_params['id']),
                        selected=selector_params.get('selected', False))
                elif selector_name == 'set-value':
                    profile.selector(
                        'set-value',
                        self.generator.id('value', selector_params['id']),
                        value=selector_params.get('value', ''))


class XccdfYamlGroupParser(XccdfYamlParser, StatusParserMixin):
    def parse(self, data):
        group = self.generator.group(data['id'])
        self._parse(group, data)
        self.append(group)

    def _parse(self, group, data):
        """
        id: <group id>
        title: ''
        description: ''
        selected: True
        profiles:
          - id: <profile id>
            selected: true | false
        """

        if 'title' in data:
            group.set_title(data['title'])

        if 'description' in data:
            group.set_description(data['description'])

        group.selected(data.get('selected', False))

        for profile in data.get('profiles', []):
            group.add_to_profile(
                name=profile['id'],
                selected=profile.get('selected', True)
            )


class XccdfYamlValueParser(XccdfYamlParser):
    """
    id: <value id>
    type: string | code
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
    def parse(self, data):
        value = self.generator.value(data['id'])
        self._parse(value, data)
        self.append(value)

    def _parse(self, value_obj, data):
        value_str = data.get('value', '')
        value_type = data.get('type', 'string')

        if 'title' in data:
            value_obj.set_title(data['title'])

        if 'description' in data:
            value_obj.set_description(data['description'])
        else:
            if value_type == 'code':
                value_obj.set_description(value_str, plaintext=True)

        if value_type == 'code':
            value_obj.set_attr('type', 'string')
            value_str = textwrap.fill(base64.b64encode(
                zlib.compress(value_str.encode())).decode(), 120)
        else:
            value_obj.set_attr('type', value_type)

        value_obj.set('value', value_str)

        for key in ['operator', ]:
            if key in data:
                value_obj.set_attr(key, data[key])

        for key in ['default', 'lower-bound', 'upper-bound']:
            item = data.get(key)
            if isinstance(item, list):
                for x in item:
                    for selector, value_str in x.items():
                        value_obj.set(key, value_str, selector=selector)
            elif item is not None:
                value_obj.set(key, str(item))


class XccdfYamlRuleParser(XccdfYamlParser):
    """
    id: <rule id>
    type: sce
    template: <template name>
    title: "Test /bin/true"
    description: |
      This is a test script
    rationale: |
      Test script rationale
    profiles:
      - id: <profile id>
        selected: true | false
    reference:
      - text: reference text
        url: Optional URL in case it's a hyperlink
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

    def parse(self, data):
        rule = self.generator.rule(data['id'])
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
            rule.add_reference(reference['text'],
                               href=reference.get('url'))

        for reference in data.get('dc-reference', []):
            ref = rule.add_dc_reference()
            for element_name, element_value in reference.items():
                if element_name == 'href':
                    ref.set_attr('href', element_value)
                else:
                    ref.sub_element(element_name).set_text(element_value)

        group = data.get('group')

        # If rule belongs to a group it should be selected by default
        selected = group is not None
        selected = data.get('selected', selected)

        rule.group = group
        rule.selected(selected)

        for profile in data.get('profiles', []):
            rule.add_to_profile(
                name=profile['id'],
                selected=profile.get('selected', True)
            )

        platforms = list(self.benchmark.platforms)
        if platforms and not data.get('affected', False):
            data['affected'] = platforms

        # if 'variable' in data:
        #     data['external-variables'] = variables_types

        parser_type = data.get('type', 'sce')
        parser_cls = XCCDF_PARSERS.get(parser_type)
        if parser_cls is None:
            parser_cls = OVAL_PARSERS.get(parser_type)
        if parser_cls is None:
            raise Exception("Can't find parser for '{}'".format(parser_type))

        parser = parser_cls(self.generator, self.benchmark,
                            parsed_args=self.parsed_args,
                            shared_files=self.shared_files)

        parser.parse(rule, data)


class XccdfYamlBenchmarkParser(XccdfYamlParser, StatusParserMixin):
    """
    id: 'sample_xccdf'
    version: 0.1

    title: Sample XCCDF Benchmark
    description: |
      Sample XCCDF Benchmark description [https://google.com](Google)

    status:
      - value: <status string>
        timestamp: "YYYY-MM-DD HH:MM:SS"

    # Target platform can be specified by CPE name if required.
    # If this parameter not defined, benchmark will run everywhere.
    platform: 'cpe:/o:canonical:ubuntu_linux:16.04'
    platforms:
      - 'cpe:/o:canonical:ubuntu_linux:16.04'

    # Files that should be copied to output directory in addition
    # to scripts generated from rules below.
    shared-files:
      - functions.sh

    values:
      - <value data>

    profiles:
      - <profile params>

    """
    def __init__(self, generator, basedir, workdir):
        super(XccdfYamlBenchmarkParser, self).__init__(generator)
        self.basedir = basedir
        self.workdir = workdir
        self.shared_files = SharedFiles(basedir=basedir, workdir=workdir)
        self.filename = None

    def parse(self, data):
        self.benchmark = self.generator.benchmark(data['id'])
        self._parse(self.benchmark, data)
        return self.benchmark

    def _parse(self, benchmark, data):
        benchmark.set_title(data.get('title'))
        benchmark.set_description(data.get('description'))

        for status in self._parse_status(
                data.get('status', [{'value': 'draft'}, ])):
            benchmark.append_status(status)

        if 'platform' in data:
            benchmark.add_platform(data['platform'].rstrip())

        for platform in data.get('platforms', []):
            benchmark.add_platform(platform.rstrip())

        dc_metadata = data.get('dc-metadata', {})
        if dc_metadata:
            metadata = benchmark.add_dc_metadata()
            for name, value_parser in dc_metadata.items():
                if isinstance(value_parser, list):
                    for value in value_parser:
                        metadata.sub_element(name).set_text(html.escape(value))
                else:
                    metadata.sub_element(name).set_text(html.escape(value_parser))

        # Import profiles

        profile_parser = XccdfYamlProfileParser(self.generator, benchmark)

        profiles = data.get('profiles', [{
            'id': 'default',
            'title': 'Default Profile',
        }, ])

        for profile_data in profiles:
            profile_parser.parse(profile_data)

        if len(profile_parser) > 1:
            default_profile = None
        else:
            default_profile = profile_parser[0]

        for profile in profile_parser:
            self.benchmark.append_profile(profile)

        # Import groups

        group_parser = XccdfYamlGroupParser(self.generator, benchmark)

        for group_data in data.get('groups', []):
            group_parser.parse(group_data)

        for group in group_parser:
            self.benchmark.append_group(group)

        # Import values

        value_parser = XccdfYamlValueParser(self.generator, benchmark)
        for value_data in data.get('values', []):
            value_parser.parse(value_data)

        for value in value_parser:
            benchmark.append_value(value)

        # Import shared files

        for item in data.get('shared-files', []):
            if isinstance(item, dict):
                for filename, sourceref in item.items():
                    self.shared_files.new(name=filename, sourceref=sourceref)
            else:
                self.shared_files.new(name=item, sourceref=item)

        # Import rules

        rule_parser = XccdfYamlRuleParser(self.generator, benchmark,
                                          shared_files=self.shared_files)
        for rule_data in unlist(data.get('rules', [])):
            rule_parser.parse(rule_data)

        for rule in rule_parser:
            if rule.group:
                group = benchmark.group(
                    self.generator.id('group', rule.group)
                )
                group.append_rule(rule)
            else:
                group = None
                benchmark.append_rule(rule)

            if group:
                profile = None
                for profile_name, profile_data in group.profiles:
                    profile = benchmark.profile(
                        self.generator.id('profile', profile_name))
                    profile.select_item(
                        group, selected=profile_data.get('selected', False))

                if profile is None and default_profile:
                    default_profile.select_item(group, selected=True)
            else:
                profile = None
                for profile_name, profile_data in rule.profiles:
                    profile = benchmark.profile(
                        self.generator.id('profile', profile_name))
                    profile.select_item(
                        rule, selected=profile_data.get('selected', False))

                if profile is None and default_profile:
                    default_profile.select_item(rule, selected=True)

    def export(self, output_dir, output_file=None, unescape=False):
        self.shared_files.export(output_dir)

        benchmark_xml = self.benchmark.xml()
        benchmark_xml_str = etree.tostring(benchmark_xml,
                                           encoding='utf-8',
                                           xml_declaration=True,
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
            f.write(benchmark_xml_str)

        return output_file


class XccdfYamlTailoringParser(XccdfYamlParser, StatusParserMixin):
    """
    id: 'external_variable_benchmark_tailoring'
    benchmark: 'external_variable_benchmark'
    status:
      - value: 'incomplete'
    version: '0.2'
    metadata:
      - ''
    profiles:
      - id: 'default-modified'
        extends: default
        title: Profile from tailoring
        selectors:
          - set-value:
             idref: 'sample_value'
             value: 'asd'
    """

    def __init__(self, generator, basedir, workdir):
        super(XccdfYamlTailoringParser, self).__init__(generator)
        self.basedir = basedir
        self.workdir = workdir
        self.shared_files = SharedFiles(basedir=basedir, workdir=workdir)
        self.filename = None

    def parse(self, data):
        self.tailoring = self.generator.tailoring(data['id'])
        self._parse(self.tailoring, data)
        return self.tailoring

    def _parse(self, tailoring, data):
        if 'version' in data:
            tailoring.set_version(data['version'])

        for status in self._parse_status(data.get('status', [])):
            tailoring.append_status(status)

        # Import profiles

        profile_parser = XccdfYamlProfileParser(self.generator, tailoring)

        profiles = data.get('profiles', [{
            'id': 'default',
            'title': 'Default Profile',
        }, ])

        for profile_data in profiles:
            profile_parser.parse(profile_data)

        for profile in profile_parser:
            self.tailoring.append_profile(profile)

    def export(self, output_dir, output_file=None, unescape=False):
        os.makedirs(output_dir, exist_ok=True)

        self.shared_files.export(output_dir)

        benchmark_xml = self.tailoring.xml()
        benchmark_xml_str = etree.tostring(benchmark_xml,
                                           encoding='utf-8',
                                           xml_declaration=True,
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
            f.write(benchmark_xml_str)

        return output_file
