from xccdf_yaml.parsers.common import ParsedObjects

import os
import re
import stat


SHELL_WRAPPER_HEAD = """#!/bin/bash
set -o errtrace
set -o nounset
set -o pipefail
declare -A XCCDF_RESULT
XCCDF_RESULT[CONTINUE]=100
XCCDF_RESULT[PASS]=${XCCDF_RESULT_PASS:-101}
XCCDF_RESULT[FAIL]=${XCCDF_RESULT_FAIL:-102}
XCCDF_RESULT[ERROR]=${XCCDF_RESULT_ERROR:-103}
XCCDF_RESULT[UNKNOWN]=${XCCDF_RESULT_UNKNOWN:-104}
XCCDF_RESULT[NOT_APPLICABLE]=${XCCDF_RESULT_NOT_APPLICABLE:-105}
XCCDF_RESULT[NOT_CHECKED]=${XCCDF_RESULT_NOT_CHECKED:-106}
XCCDF_RESULT[NOT_SELECTED]=${XCCDF_RESULT_NOT_SELECTED:-107}
XCCDF_RESULT[INFORMATIONAL]=${XCCDF_RESULT_INFORMATIONAL:-108}
XCCDF_RESULT[FIXED]=${XCCDF_RESULT_FIXED:-109}
exit_with(){
  set +o xtrace
  local status=${1:-ERROR}
  local ec=${XCCDF_RESULT[${status}]:-${XCCDF_RESULT[ERROR]}}
  echo "Exiting with status ${status}(${ec})"
  exit ${ec}
}
trap_error(){
  local ec=${1:-0}
  if [[ ${ec} == 100 ]]; then
    return
  elif [[ ${ec} -gt 100 && ${ec} -lt 110 ]]; then
    exit ${ec}
  else
    exit ${XCCDF_RESULT[ERROR]}
  fi
}
trap 'trap_error $?' ERR
set -o xtrace
"""

SHELL_WRAPPER_TAIL = """
exit_with PASS
"""

PYTHON_WRAPPER_HEAD1 = """#!/usr/bin/python
import os
import sys
import traceback

"""

PYTHON_WRAPPER_HEAD2 = """
XCCDF_RESULT_PASS = os.environ.get('XCCDF_RESULT_PASS', 0)
XCCDF_RESULT_FAIL = os.environ.get('XCCDF_RESULT_FAIL', 1)

def exit_pass():
    sys.exit(XCCDF_RESULT_PASS)

def exit_fail():
    sys.exit(XCCDF_RESULT_FAIL)

"""

PYTHON_WRAPPER_TAIL = """
try:
    main()
    exit_pass()
except:
    traceback.print_exc(file=sys.stdout)
    exit_fail()

"""


class CmdExecParser(object):
    def __init__(self, parsed_args=None, output_dir=None):
        self.parsed_args = parsed_args
        self.output_dir = output_dir or parsed_args.output_dir

    def parse(self, id, metadata):
        res = ParsedObjects()

        rule = res.new_rule(id)

        if 'title' in metadata:
            rule.set_title(metadata['title'])

        if 'description' in metadata:
            rule.set_description(metadata['description'])

        for reference in metadata.get('reference', []):
            ref = rule.sub_element('reference')
            if isinstance(reference, dict):
                ref.set_text(reference['text'])
                if 'url' in reference:
                    ref.set_attr('href', reference['url'])
            else:
                ref.set_text(reference)

        if 'rationale' in metadata:
            rule.sub_element('rationale')\
                .set_text(metadata['rationale'].rstrip())

        if 'cmd' in metadata:
            res.add_shared_file('wrapper-head.sh', SHELL_WRAPPER_HEAD)
            res.add_shared_file('wrapper-tail.sh', SHELL_WRAPPER_TAIL)
            filename = '{}.sh'.format(id)
            target_filename = os.path.join(self.output_dir, filename)
            with open(target_filename, 'w') as f:
                f.write('#!/bin/bash')
                f.write('\nsource wrapper-head.sh\n')
                f.write(metadata['cmd'])
                f.write('\nsource wrapper-tail.sh\n')
        elif 'python' in metadata:
            filename = '{}.py'.format(id)
            target_filename = os.path.join(self.output_dir, filename)
            with open(target_filename, 'w') as f:
                f.write(PYTHON_WRAPPER_HEAD1)
                for line in metadata['python'].get('imports', []):
                    f.write('{}\n'.format(line))
                f.write(PYTHON_WRAPPER_HEAD2)
                if 'raw' in metadata['python']:
                    f.write('{}\n'.format(metadata['python']['raw']))
                if 'main' in metadata['python']:
                    f.write('def main():\n')
                    for line in metadata['python']['main'].split('\n'):
                        if line.rstrip():
                            f.write('    {}\n'.format(line))
                        else:
                            f.write('\n')
                f.write(PYTHON_WRAPPER_TAIL)
        else:
            raise Exception('No script or cmdline found')

        if os.path.exists(target_filename):
            x = os.stat(target_filename)
            os.chmod(target_filename, x.st_mode | stat.S_IEXEC)

        check = rule.add_check(system_ns='sce')\
            .check_import({'import-name': 'stdout'})\
            .check_content_ref({'href': filename})
        if 'export' in metadata:
            for item in metadata['export']:
                if isinstance(item, dict):
                    for value_id, export_name in item.items():
                        check.check_export(value_id=value_id,
                                           export_name=export_name)
                else:
                    export_name = re.sub(r'[^\w\d]', '_', item).upper()
                    check.check_export(value_id=item,
                                       export_name=export_name)

        return res
