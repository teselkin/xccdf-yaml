from xccdf_yaml.parsers.common import GenericParser

import re
import base64


SHELL_ENTRYPOINT = """#!/bin/bash
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
if [[ -f "${XCCDF_VALUE_ENTRYPOINT}" ]]; then
  set -o xtrace
  source "${XCCDF_VALUE_ENTRYPOINT}"
fi
exit_with PASS
"""

PYTHON_ENTRYPOINT="""#!/usr/bin/python
import os
import sys
import traceback

XCCDF_RESULT_PASS = os.environ.get('XCCDF_RESULT_PASS', 0)
XCCDF_RESULT_FAIL = os.environ.get('XCCDF_RESULT_FAIL', 1)

def exit_pass():
    sys.exit(XCCDF_RESULT_PASS)

def exit_fail():
    sys.exit(XCCDF_RESULT_FAIL)

try:
    filename = os.environ.get('XCCDF_VALUE_ENTRYPOINT')
    exec(compile(open(filename, "rb").read(), filename, 'exec'), globals(), locals())
    exit_pass()
except:
    traceback.print_exc(file=sys.stdout)
    exit_fail()
"""


class ScriptCheckEngineParser(GenericParser):
    def parse(self, id, metadata):
        result = super(ScriptCheckEngineParser, self).parse(id, metadata)
        rule = result.rule

        check_metadata = metadata['check']
        engine = check_metadata.get('engine', 'shell')
        entrypoint = check_metadata.get('entrypoint')

        if entrypoint:
            self.add_shared_file(entrypoint).set_executable()

        if engine == 'shell':
            if entrypoint is None:
                entrypoint = 'entrypoint.sh'
                self.add_shared_file(entrypoint, content=SHELL_ENTRYPOINT)\
                    .set_executable()
            entrypoint_target = '{}.sh'.format(id)
        elif engine == 'python':
            if entrypoint is None:
                entrypoint = 'entrypoint.py'
                self.add_shared_file(entrypoint, content=PYTHON_ENTRYPOINT)\
                    .set_executable()
            entrypoint_target = '{}.py'.format(id)
        else:
            raise Exception("Unsupported engine {}".format(engine))

        check = rule.add_check(system_ns='sce')\
            .check_import(import_name='stdout')\
            .check_import(import_name='stderr')\
            .check_content_ref(href=entrypoint)

        # value = self.benchmark.new_value(
        #     '{}-entrypoint'.format(rule.get_attr('id')))\
        #     .set_value(entrypoint_target)
        # check.check_export(value.get_attr('id'), 'ENTRYPOINT')
        # self.add_shared_file(entrypoint_target,
        #                      content=check_metadata['codeblock'])

        marker = r'```'.encode()
        codeblock = check_metadata['codeblock'].encode()
        value = self.benchmark.new_value(
            '{}-codeblock'.format(rule.get_attr('id')))\
            .set_value(base64.b64encode(codeblock).decode())\
            .set_description((marker + codeblock + marker).decode())
        check.check_export(value.get_attr('id'), 'CODEBLOCK')

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

        return result
