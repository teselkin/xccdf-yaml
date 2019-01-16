from xccdf_yaml.oval.parsers.dpkginfo import DpkginfoParser
from xccdf_yaml.oval.parsers.file import FileParser
from xccdf_yaml.oval.parsers.sysctl import SysctlParser
from xccdf_yaml.oval.parsers.textfilecontent import TextfilecontentParser
from xccdf_yaml.oval.parsers.systemd import SystemdParser
from xccdf_yaml.oval.parsers.inetlisteningservers import InetlisteningserversParser


PARSERS = {
    'pkg': DpkginfoParser,
    'file': FileParser,
    'pattern_match': TextfilecontentParser,
    'sysctl': SysctlParser,
    'systemd': SystemdParser,
    'listen': InetlisteningserversParser,
}
