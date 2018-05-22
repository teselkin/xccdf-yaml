from xccdf_yaml.parsers.sample import YamlParserSample
from xccdf_yaml.parsers.cmd_exec import CmdExecParser


PARSERS = {
    'cmd_exec': CmdExecParser,
    'sample': YamlParserSample,
}
