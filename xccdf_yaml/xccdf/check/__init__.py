from xccdf_yaml.xccdf.check.cmd_exec import CmdExecParser
from xccdf_yaml.xccdf.check.sce import ScriptCheckEngineParser


PARSERS = {
    'cmd_exec': CmdExecParser,
    'sce': ScriptCheckEngineParser,
}
