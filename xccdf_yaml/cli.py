import logging

from cliff.command import Command
from cliff.lister import Lister
from xccdf_yaml.parsers import PARSERS

from xccdf_yaml.xccdf import Benchmark
from xccdf_yaml.xccdf import BenchmarkRule


class CliConvertYamlToXccdf(Command):
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        print('Hello World!')


class CliTestXccdf(Command):
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        benchmark = Benchmark('test_benchmark')
        benchmark.set_description('<b>Description</b>')
        benchmark.add_platform('cpe:/o:canonical:ubuntu_linux:16.04')

        profile = benchmark.add_profile('mos')
        profile.set_title('Mirantis uberprofile')

        group = benchmark.add_group('common')
        rule = group.add_rule('etc_os_release_does_not_match_Xerus')
        check = rule.add_check()
        check.check_content_ref(href="mos-ubuntu1604-oval.xml",
                                name="oval:mos-etc_os_release_does_not_match_Xerus:def:1")
        profile.add_rule(rule, selected=True)

        rule = group.add_rule('bin_dash_has_mode_0755')
        check = rule.add_check()
        check.check_content_ref(href="mos-ubuntu1604-oval.xml",
                                name="oval:mos-bin_dash_has_mode_0755:def:1")
        profile.add_rule(rule, selected=True)

        rule = group.add_rule('aide_is_installed')
        check = rule.add_check()
        check.check_content_ref(href="mos-ubuntu1604-oval.xml",
                                name="oval:mos-aide_is_installed:def:1")
        profile.add_rule(rule, selected=True)

        rule = group.add_rule('sysctl_vm_laptop_mode_1')
        check = rule.add_check()
        check.check_content_ref(href="mos-ubuntu1604-oval.xml",
                                name="oval:mos-sysctl_vm_laptop_mode_1:def:1")
        profile.add_rule(rule, selected=True)

        return str(benchmark)


class CliAboutParser(Command):
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument('name')
        return parser

    def take_action(self, parsed_args):
        cls = PARSERS.get(parsed_args.name)
        print(cls.about())


class CliListParsers(Lister):
    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        cols = ('Name', 'About')
        rows = []
        for cls in PARSERS:
            rows.append((cls.name(), cls.about()))
        return cols, rows
