import logging

from cliff.command import Command
from cliff.lister import Lister
from xccdf_yaml.parsers import PARSERS


class CliConvertYamlToXccdf(Command):
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        print('Hello World!')


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
