# import logging
import argparse
import sys

import xccdf_yaml.cli.cli as cli

from cliff.app import App
from cliff.commandmanager import CommandManager
from xccdf_yaml.appdata import APPDATA


class XCCDF_YAML_Manager(CommandManager):
    SHELL_COMMANDS = {
        'convert': cli.CliConvertYaml,
        'load': cli.CliLoadYaml,
        'validate': cli.CliValidateYaml,
        'schematron': cli.CliSchematron,
        'datastream': cli.CliDatastream,
        'about-parser': cli.CliAboutParser,
        'list-parsers': cli.CliListParsers,
        'test-xccdf': cli.CliTestXccdf,
        'test-oval': cli.CliTestOval,
    }

    def load_commands(self, namespace):
        for name, cmd_class in self.SHELL_COMMANDS.items():
            self.add_command(name, cmd_class)


class XCCDF_YAML_App(App):
    def __init__(self):
        super().__init__(
            description='XCCDF from YAML convertion tool',
            version='0.1',
            command_manager=XCCDF_YAML_Manager('xccdf_yaml'),
            deferred_help=True,
        )

    def initialize_app(self, argv):
        parser = argparse.ArgumentParser()
        parser.add_argument('--workdir', default=None)
        args, _ = parser.parse_known_args()

        if args.workdir:
            APPDATA['workdir'] = args.workdir


def main():
    app = XCCDF_YAML_App()
    return app.run(sys.argv[1:])


if __name__ == '__main__':
    main()
