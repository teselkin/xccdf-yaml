import os
import operator
import html
import json
import yaml
import lxml.etree as etree
import cgi
import textwrap
import tempfile
import subprocess
import traceback
import zlib
import base64

from lxml.isoschematron import Schematron

from xccdf_yaml.misc import deepmerge, unlist
from xccdf_yaml.yaml import YamlLoader
from xccdf_yaml.xccdf import XccdfGenerator
from xccdf_yaml.oval import OvalDefinitions
from xccdf_yaml.common import SharedFiles

from xccdf_yaml.parsers import PARSERS

from jsonschema import validate
from urllib.request import urlopen


class XccdfYaml(object):
    def __init__(self, basedir=None):
        self.basedir = basedir

    def _extend_oval(self, oval, result):
        oval.append_definition(result.definition)
        oval.extend_tests(result.tests)
        oval.extend_objects(result.objects)
        oval.extend_states(result.states)
        oval.append_variable(result.variable)

    def convert(self, filename=None, output_dir=None, output_file=None,
                unescape=False, **kwargs):
        benchmark_source = filename
        data = yaml.load(open(filename), YamlLoader)
        templates = data.get('templates', {})
        data = data.get('benchmark')
        if data is None:
            raise Exception('No benchmark section found')
        variables_types = {}

        benchmark_id = data.get('id') or filename

        source_dir = os.path.dirname(filename)
        output_dir = os.path.join(output_dir, benchmark_id)
        os.makedirs(output_dir, exist_ok=True)

        generator = XccdfGenerator('mirantis.com')

        benchmark = generator.benchmark(benchmark_id)\
            .set_title(data.get('title'))\
            .set_description(data.get('description'))

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
                        metadata.sub_element(name).set_text(cgi.escape(value))
                else:
                    metadata.sub_element(name).set_text(cgi.escape(values))

        profile_info = data.get('profile', {
            'id': 'default',
            'title': 'Default Profile',
        })

        profile = benchmark\
            .add_profile(profile_info['id'])\
            .set_title(profile_info.get('title'))\
            .set_description(profile_info.get('description'))

        group_info = data.get('group', {
            'id': 'default',
            'title': 'Default Group'
        })

        group = benchmark\
            .add_group(group_info.get('id'))\
            .set_title(group_info.get('title'))

        for values in data.get('values', {}):
            for value_id, value_data in sorted(values.items(),
                                               key=operator.itemgetter(0)):
                variables_types[value_id] = value_data['type']

                value_element = benchmark.new_value(value_id)

                value_type = value_data.get('type', 'string')
                value = value_data.get('value')

                if 'title' in value_data:
                    value_element.set_title(value_data['title'])

                if 'description' in value_data:
                    value_element.set_description(value_data['description'])
                else:
                    if value_type == 'code':
                        value_element.set_description(value, plaintext=True)

                if value_type == 'code':
                    value_element.set_attr('type', 'string')
                    value = textwrap.fill(base64.b64encode(
                        zlib.compress(value.encode())).decode(), 120)
                else:
                    value_element.set_attr('type', value_type)

                value_element.set('value', value)

                for key in ['operator',]:
                    if key in value_data:
                        value_element.set_attr(key, value_data[key])

                for key in ['default', 'lower-bound', 'upper-bound']:
                    item = value_data.get(key)
                    if isinstance(item, list):
                        for x in item:
                            for selector, value in x.items():
                                value_element.set(key, value,
                                                  selector=selector)
                    elif item is not None:
                        value_element.set(key, str(item))

        shared_files = SharedFiles(
            basedir=self.basedir,
            workdir=os.path.dirname(os.path.abspath(benchmark_source)))

        oval = OvalDefinitions()
        oval_ref = '{}-oval.xml'.format(benchmark_id)

        for item in data.get('shared-files', []):
            if isinstance(item, dict):
                for filename, source in item.items():
                    shared_files.from_source(source=source, filename=filename)
            else:
                shared_files.from_source(source=item)

        for item in unlist(data.get('rules', [])):
            id, _metadata = next(iter(item.items()))
            template = _metadata.get('template')
            if template:
                metadata = deepmerge(_metadata,
                                     templates.get(template))
            else:
                metadata = _metadata
            parser_type = metadata.get('type', 'sce')
            parser = PARSERS[parser_type](benchmark,
                                          parsed_args=kwargs,
                                          output_dir=output_dir,
                                          shared_files=shared_files)
            if platform and not metadata.get('affected', False):
                metadata['affected'] = platform
            if 'variable' in metadata:
                metadata['external-variables'] = variables_types
            res = parser.parse(id, metadata)
            group.append_rule(res.rule)
            profile.append_rule(res.rule, selected=True)
            if res.has_oval_data:
                check = res.rule.add_check()
                if res.has_variable:
                    check.check_export(
                        # FIXME: Fix value id for variable
                        value_id=metadata['variable'],
                        export_name=res.variable.get_attr('id'),
                    )
                check.check_content_ref(
                    href=oval_ref,
                    name=res.definition.get_attr('id'),
                )
                self._extend_oval(oval, res)

        shared_files.export(output_dir)

        benchmark_xml = benchmark.xml()
        benchmark_xml_str = etree.tostring(benchmark_xml,
                                           pretty_print=True).decode()

        if unescape:
            benchmark_xml_str = html.unescape(benchmark_xml_str)

        if not oval.is_empty():
            oval_filename = os.path.join(output_dir, oval_ref)
            oval_xml = oval.xml()
            oval_xml_str = etree.tostring(oval_xml,
                                          pretty_print=True).decode()
            with open(oval_filename, 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(oval_xml_str)

        if output_file is None:
            output_file = os.path.join(output_dir,
                                '{}-xccdf.xml'.format(benchmark_id))
        else:
            output_file = os.path.join(output_dir, output_file)

        with open(output_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(benchmark_xml_str)

        return output_file

    def validate(self, filename=None, schema_type='auto', schema='',
                 skip_valid=False, **kwargs):
        if schema_type == 'auto':
            _, ext = os.path.splitext(schema.lower())
            if ext in ['.json', ]:
                schema_type = 'json'
            elif ext in ['.yaml', '.yml', ]:
                schema_type = 'yaml'
            elif ext in ['.xml', '.xsd', ]:
                schema_type = 'xml'
            else:
                raise Exception("Unable to detect schema type for '{}'"
                                .format(schema))

        if schema_type in ['json', 'yaml']:
            if schema_type == 'json':
                schema = json.load(open(schema))
            else:
                schema = yaml.load(open(schema))

            try:
                data = yaml.load(open(filename), YamlLoader)
                validate(data, schema)
            except:
                traceback.print_exc()
                if not skip_valid:
                    raise
            return

        if schema_type == 'xml':
            with open(schema) as f:
                schema_root = etree.parse(f)
                schema_doc = etree.XMLSchema(schema_root)

            with open(filename) as f:
                benchmark = etree.parse(f)

            success = schema_doc.validate(benchmark)
            if success:
                print("XMLSchema validation passed")
            else:
                print("XMLSchema validation errors:")
                for error in schema_doc.error_log:
                    print('---')
                    print(str(error))
                print('---')

            if skip_valid:
                return success

            if not success:
                raise Exception("XMLSchema validation failed")

            return success

        raise Exception("Bad schema type '{}'".format(schema_type))

    def load(self, filename=None, format='', pretty=False, indent=2,
             output=None, **kwargs):
        data = yaml.load(open(filename), YamlLoader)

        result = None
        if format == 'json':
            if pretty:
                result = json.dumps(data,
                                    indent=indent,
                                    sort_keys=True)
            else:
                result = json.dumps(data)
        elif format == 'yaml':
            if pretty:
                result = yaml.dump(data,
                                   default_flow_style=False,
                                   indent=indent)
            else:
                result = yaml.dump(data)

        if output:
            with open(output, 'w') as f:
                f.write(result)
            return

        return result

    def schematron(self, filename=None, schematron_file=None, skip_valid=False,
                   **kwargs):
        if schematron_file is None:
            schema_doc = etree.parse(urlopen(
                'https://csrc.nist.gov/schema/xccdf/1.2/xccdf_1.2.sch'))
        else:
            with open(schematron_file) as f:
                schema_doc = etree.parse(f)

        schema = Schematron(schema_doc, store_report=True)

        with open(filename) as f:
            benchmark = etree.parse(f)

        validation_result = schema.validate(benchmark)
        if validation_result:
            print('Benchmark {} PASSED schematron validation'.format(filename))
            return True
        else:
            print('Benchmark {} FAILED schematron validation'.format(filename))
            errors = schema.validation_report.xpath(
                'svrl:failed-assert/svrl:text',
                namespaces={'svrl': 'http://purl.oclc.org/dsdl/svrl'}
            )
            print('Schematron validation errors:')
            for element in errors:
                print("---")
                print(textwrap.fill(element.text))
            print("---")

            if skip_valid:
                return validation_result

            raise Exception("Schematron validation failed")

    def datastream(self, filename=None, skip_valid=False, output_file=None,
                   **kwargs):
        cmd = ['oscap', 'ds', 'sds-compose']
        if skip_valid:
            cmd.append('--skip-valid')
        cmd.append(filename)
        if output_file is None:
            output_file = "{}-ds.xml".format(
                filename.rsplit('.', maxsplit=1)[0])
        cmd.append(output_file)

        stderr_fd, stderr_filename = tempfile.mkstemp()
        try:
            stdout = subprocess.check_output(cmd, stderr=stderr_fd)
            exitcode = 0
        except subprocess.CalledProcessError as e:
            exitcode = e.returncode
            stdout = e.output

        if exitcode != 0:
            output_file = None
            print("EXITCODE: {}".format(str(exitcode)))
            print("----- STDOUT BEGIN -----")
            print(stdout.decode().strip())
            print("-----  STDOUT END  -----")

            print("----- STDERR BEGIN -----")
            with open(stderr_filename) as stderr:
                print(stderr.read().strip())
            print("-----  STDERR END  -----")

        os.remove(stderr_filename)

        print("Source datastream: {}".format(output_file))

        return output_file
