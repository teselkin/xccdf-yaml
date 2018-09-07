import os
import operator
import html
import shutil
import stat
import json
import yaml
import lxml.etree as etree

from xccdf_yaml.yaml import YamlLoader
from xccdf_yaml.xccdf import XccdfBenchmark
from xccdf_yaml.oval import OvalDefinitions

from xccdf_yaml.parsers import PARSERS

from jsonschema import validate


def unlist(seq):
    if isinstance(seq, list):
        for x in seq:
            for y in unlist(x):
                yield y
    else:
        yield seq


class ValidateYamlAction(object):
    def take_action(self, parsed_args):
        data = yaml.load(open(parsed_args.filename), YamlLoader)

        if parsed_args.schema_type == 'auto':
            _, ext = os.path.splitext(parsed_args.schema.lower())
            if ext in ['.json', ]:
                schema_type = 'json'
            elif ext in ['.yaml', '.yml', ]:
                schema_type = 'yaml'
            else:
                raise Exception("Unable to detect schema type for '{}'"
                                .format(parsed_args.schema))
        else:
            schema_type = parsed_args.schema_type

        if schema_type == 'json':
            schema = json.load(open(parsed_args.schema))
        elif schema_type == 'yaml':
            schema = yaml.load(open(parsed_args.schema))
        else:
            raise Exception("Bad schema type '{}'".format(schema_type))

        validate(data, schema)


class ConvertYamlAction(object):
    def __init__(self):
        pass

    def extend_oval(self, oval, result):
        oval.append_definition(result.definition)
        oval.extend_tests(result.tests)
        oval.extend_objects(result.objects)
        oval.extend_states(result.states)

    def take_action(self, parsed_args):
        data = yaml.load(open(parsed_args.filename), YamlLoader)
        data = data.get('benchmark')
        if data is None:
            raise Exception('No benchmark section found')

        benchmark_id = data.get('id') or parsed_args.filename

        output_dir = os.path.join(parsed_args.output_dir, benchmark_id)
        os.makedirs(output_dir, exist_ok=True)

        benchmark = XccdfBenchmark(benchmark_id)\
            .set_title(data.get('title'))\
            .set_description(data.get('description'))

        platform = data.get('platform')
        if platform:
            if isinstance(platform, list):
                for platform_str in platform:
                    benchmark.add_platform(platform_str.rstrip())
            else:
                benchmark.add_platform(platform.rstrip())

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
                value_element = benchmark.new_value(value_id)
                for key in ['type', 'operator']:
                    if key in value_data:
                        value_element.set_attr(key, value_data[key])
                if 'title' in value_data:
                    value_element.set_title(value_data['title'])
                if 'description' in value_data:
                    value_element.set_description(value_data['description'])

                for key in ['value', 'default', 'lower-bound', 'upper-bound']:
                    item = value_data.get(key)
                    if isinstance(item, list):
                        for x in item:
                            for selector, value in x.items():
                                value_element.set(key, value,
                                                  selector=selector)
                    elif item is not None:
                        value_element.set(key, str(item))

        shared_files = {}

        oval = OvalDefinitions()
        oval_ref = '{}-oval.xml'.format(benchmark_id)

        for item in data.get('shared-files', []):
            filename = os.path.join(
                os.path.dirname(parsed_args.filename), item)
            if not os.path.exists(filename):
                raise Exception("Shared file '{}' not found"
                                .format(filename))
            shared_files[os.path.basename(filename)] = {'source': filename,}

        entrypoints = set()
        for item in unlist(data.get('rules', [])):
            id, metadata = next(iter(item.items()))
            parser_type = metadata.get('type', 'cmd_exec')
            parser = PARSERS[parser_type](parsed_args=parsed_args,
                                          output_dir=output_dir,
                                          benchmark=benchmark)
            if platform and not metadata.get('affected', False):
                metadata['affected'] = platform
            res = parser.parse(id, metadata)
            for shared_file, data in res.shared_files:
                shared_files.setdefault(shared_file, {})
                shared_files[shared_file].update(data)
            group.append_rule(res.rule)
            profile.append_rule(res.rule, selected=True)
            if res.has_oval_data:
                res.rule.add_check()\
                    .check_content_ref(
                        href=oval_ref,
                        name=res.definition.get_attr('id'),
                    )
                self.extend_oval(oval, res)
            for entrypoint in res.entrypoints:
                entrypoints.add(entrypoint)

        for shared_file, data in shared_files.items():
            target = os.path.join(output_dir, os.path.basename(shared_file))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            if 'source' in data:
                shutil.copyfile(data['source'], target)
            elif 'content' in data:
                with open(target, 'w') as f:
                    f.write(data['content'])

        for entrypoint in entrypoints:
            target = os.path.join(output_dir, os.path.basename(entrypoint))
            if os.path.exists(target):
                x = os.stat(target)
                os.chmod(target, x.st_mode | stat.S_IEXEC)

        benchmark_filename = os.path.join(output_dir,
                                '{}-xccdf.xml'.format(benchmark_id))

        benchmark_xml = benchmark.xml()
        benchmark_xml_str = etree.tostring(benchmark_xml,
                                           pretty_print=True).decode()

        if parsed_args.unescape:
            benchmark_xml_str = html.unescape(benchmark_xml_str)

        if not oval.is_empty():
            oval_filename = os.path.join(output_dir, oval_ref)
            oval_xml = oval.xml()
            oval_xml_str = etree.tostring(oval_xml,
                                          pretty_print=True).decode()
            with open(oval_filename, 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(oval_xml_str)

        with open(benchmark_filename, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(benchmark_xml_str)

        return


class LoadYamlAction(object):
    def take_action(self, parsed_args):
        data = yaml.load(open(parsed_args.filename), YamlLoader)

        result = None
        if parsed_args.format == 'json':
            if parsed_args.pretty:
                result = json.dumps(data,
                                    indent=parsed_args.indent,
                                    sort_keys=True)
            else:
                result = json.dumps(data)
        elif parsed_args.format == 'yaml':
            if parsed_args.pretty:
                result = yaml.dump(data,
                                   default_flow_style=False,
                                   indent=parsed_args.indent)
            else:
                result = yaml.dump(data)

        if parsed_args.output:
            with open(parsed_args.output, 'w') as f:
                f.write(result)
            return

        return result
