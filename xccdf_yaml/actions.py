import os

from xccdf_yaml.common import YamlLoader
from xccdf_yaml.xccdf import Benchmark

from xccdf_yaml.parsers import PARSERS


class ConvertYamlAction(object):
    def __init__(self):
        pass

    def take_action(self, parsed_args):
        loader = YamlLoader()
        data = loader.load(parsed_args.filename).get('benchmark')
        if data is None:
            raise Exception('No benchmark section found')

        os.makedirs(parsed_args.output_dir, exist_ok=True)

        benchmark_id = data.get('id') or parsed_args.filename

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

        for item in data.get('rules', []):
            id, metadata = next(iter(item.items()))
            parser = PARSERS[metadata['type']](parsed_args)
            res = parser.parse(id, metadata)
            group.append_rule(res.rule)
            profile.append_rule(res.rule, selected=True)

        filename = os.path.join(parsed_args.output_dir,
                                '{}-xccdf.yaml'.format(benchmark_id))
        with open(filename, 'w') as f:
            f.write(str(benchmark))

        return