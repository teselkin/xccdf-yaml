import os
import html
import shutil
import yaml
import lxml.etree as etree

from xccdf_yaml.yaml import YamlLoader
from xccdf_yaml.xccdf import Benchmark

from xccdf_yaml.parsers import PARSERS


def unlist(seq):
    if isinstance(seq, list):
        for x in seq:
            for y in unlist(x):
                yield y
    else:
        yield seq


class ConvertYamlAction(object):
    def __init__(self):
        pass

    def take_action(self, parsed_args):
        data = yaml.load(open(parsed_args.filename), YamlLoader)
        data = data.get('benchmark')
        if data is None:
            raise Exception('No benchmark section found')

        benchmark_id = data.get('id') or parsed_args.filename

        output_dir = os.path.join(parsed_args.output_dir, benchmark_id)
        os.makedirs(output_dir, exist_ok=True)

        benchmark = Benchmark(benchmark_id)\
            .set_title(data.get('title'))\
            .set_description(data.get('description'))

        platform = data.get('platform')
        if platform:
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

        shared_files = {}
        for item in data.get('shared-files', []):
            filename = os.path.join(
                os.path.dirname(parsed_args.filename), item)
            if not os.path.exists(filename):
                raise Exception("Shared file '{}' not found"
                                .format(filename))
            shared_files[os.path.basename(filename)] = {'source': filename,}

        for item in unlist(data.get('rules', [])):
            id, metadata = next(iter(item.items()))
            parser_type = metadata.get('type', 'cmd_exec')
            parser = PARSERS[parser_type](parsed_args, output_dir)
            res = parser.parse(id, metadata)
            for shared_file, data in res.shared_files:
                shared_files.setdefault(shared_file, {})
                shared_files[shared_file].update(data)
            group.append_rule(res.rule)
            profile.append_rule(res.rule, selected=True)

        for shared_file, data in shared_files.items():
            target = os.path.join(output_dir, os.path.basename(shared_file))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            if 'source' in data:
                shutil.copyfile(data['source'], target)
            elif 'content' in data:
                with open(target, 'w') as f:
                    f.write(data['content'])

        filename = os.path.join(output_dir,
                                '{}-xccdf.xml'.format(benchmark_id))

        xml = benchmark.xml()
        xml_str = etree.tostring(xml, pretty_print=True).decode()

        if parsed_args.unescape:
            xml_str = html.unescape(xml_str)

        with open(filename, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(xml_str)

        return
