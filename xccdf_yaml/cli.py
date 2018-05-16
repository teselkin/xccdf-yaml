import logging

from cliff.command import Command

class CliConvertYamlToXccdf(Command):
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        print('Hello World!')
