from xccdf_yaml.parsers.sample import YamlParserSample
from xccdf_yaml.parsers.cmd_exec import CmdExecParser
from xccdf_yaml.parsers.dpkginfo import DpkginfoParser
from xccdf_yaml.parsers.file import FileParser
from xccdf_yaml.parsers.sysctl import SysctlParser
from xccdf_yaml.parsers.textfilecontent import TextfilecontentParser


PARSERS = {
    'cmd_exec': CmdExecParser,
    'sample': YamlParserSample,
    'pkg': DpkginfoParser,
    'file': FileParser,
    'pattern_match': TextfilecontentParser,
    'sysctl': SysctlParser,
}
