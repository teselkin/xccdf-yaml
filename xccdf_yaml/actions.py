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

        benchmark = Benchmark(benchmark_id)
        title = data.get('title')
        if title:
            benchmark.set_title(title.rstrip())

        description = data.get('description')
        if description:
            benchmark.set_description(description.rstrip())

        platform = data.get('platform')
        if platform:
            benchmark.add_platform(platform.rstrip())

        profile = benchmark\
            .add_profile('default')\
            .set_title('Default profile')

        group = benchmark.add_group('default')

        for item in data.get('rules', []):
            id, metadata = next(iter(item.items()))
            parser = PARSERS[metadata['type']](parsed_args)
            rule = parser.parse(id, metadata)
            group.append_rule(rule)
            profile.append_rule(rule)

        filename = os.path.join(parsed_args.output_dir,
                                '{}-xccdf.yaml'.format(benchmark_id))
        with open(filename, 'w') as f:
            f.write(str(benchmark))

        return