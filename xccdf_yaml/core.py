import os
import html
import json
import yaml
import lxml.etree as etree
import cgi
import textwrap
import tempfile
import subprocess
import traceback

from lxml.isoschematron import Schematron

from xccdf_yaml.misc import deepmerge, unlist
from xccdf_yaml.yaml import YamlLoader
from xccdf_yaml.xccdf.elements import XccdfGenerator
from xccdf_yaml.oval.elements import OvalDefinitions
from xccdf_yaml.common import SharedFiles

from xccdf_yaml.oval.parsers import PARSERS
from xccdf_yaml.xccdf.parsers import XccdfYamlBenchmarkParser,\
    XccdfYamlTailoringParser

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
        workdir = os.path.dirname(filename)
        generator = XccdfGenerator('mirantis.com')
        benchmark = XccdfYamlBenchmarkParser(generator, self.basedir, workdir)
        data = yaml.load(open(filename), YamlLoader)
        benchmark.parse(None, data['benchmark'])
        benchmark.export(output_dir=output_dir, output_file=output_file,
                         unescape=unescape)

    def tailoring(self, filename=None, output_dir=None, output_file=None,
                  unescape=False, **kwargs):

        workdir = os.path.dirname(filename)
        generator = XccdfGenerator('mirantis.com')
        parser = XccdfYamlTailoringParser(generator, self.basedir, workdir)
        data = yaml.load(open(filename), YamlLoader)
        parser.parse(None, data['tailoring'])
        parser.export(output_dir=output_dir, output_file=output_file,
                         unescape=unescape)

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
