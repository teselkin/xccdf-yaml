from xccdf_yaml.xccdf.check.common import GenericParser

import re


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


class CmdExecParser(GenericParser):
    def parse(self, rule, metadata):
        id = rule.get_attr('id')

        if 'cmd' in metadata:
            self.shared_files.new('wrapper-head.sh',
                                  content=SHELL_WRAPPER_HEAD)\
                .set_executable()
            self.shared_files.new('wrapper-tail.sh',
                                  content=SHELL_WRAPPER_TAIL)\
                .set_executable()
            filename = '{}.sh'.format(id)
            content = []
            content.append('#!/bin/bash')
            content.append('source wrapper-head.sh')
            content.append(metadata['cmd'])
            content.append('source wrapper-tail.sh')
        elif 'python' in metadata:
            filename = '{}.py'.format(id)
            content = []
            content.append(PYTHON_WRAPPER_HEAD1)
            content.extend(metadata['python'].get('imports', []))
            content.append(PYTHON_WRAPPER_HEAD2)
            content.append(metadata['python'].get('raw', '# No raw section'))
            if 'main' in metadata['python']:
                content.append('def main():')
                for line in metadata['python']['main'].split('\n'):
                    if line.rstrip():
                        content.append('    {}'.format(line))
                    else:
                        content.append('')
            content.append(PYTHON_WRAPPER_TAIL)
        else:
            raise Exception('No script or cmdline found')

        self.shared_files.new(filename,
                              content='\n'.join(content)).set_executable()

        check = rule.add_check(system_ns='sce')\
            .check_import(import_name='stdout')\
            .check_import(import_name='stderr')\
            .check_content_ref(href=filename)

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
