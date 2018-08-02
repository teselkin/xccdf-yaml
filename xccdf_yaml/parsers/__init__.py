from xccdf_yaml.parsers.sample import YamlParserSample
from xccdf_yaml.parsers.cmd_exec import CmdExecParser
from xccdf_yaml.parsers.dpkginfo import DpkginfoParser
from xccdf_yaml.parsers.file import FileParser
from xccdf_yaml.parsers.sysctl import SysctlParser
from xccdf_yaml.parsers.textfilecontent import TextfilecontentParser
from xccdf_yaml.parsers.systemd import SystemdParser
from xccdf_yaml.parsers.sce import ScriptCheckEngineParser
from xccdf_yaml.parsers.inetlisteningservers import InetlisteningserversParser


PARSERS = {
    'cmd_exec': CmdExecParser,
    'sample': YamlParserSample,
    'pkg': DpkginfoParser,
    'file': FileParser,
    'pattern_match': TextfilecontentParser,
    'sysctl': SysctlParser,
    'systemd': SystemdParser,
    'sce': ScriptCheckEngineParser,
    'listen': InetlisteningserversParser,
}
