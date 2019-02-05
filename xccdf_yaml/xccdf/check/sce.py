from xccdf_yaml.xccdf.check.common import GenericParser
from itertools import chain

import re
import base64
import zlib
import textwrap


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

PYTHON_ENTRYPOINT = """#!/usr/bin/python
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
    exec(compile(open(filename, "rb").read(), filename, 'exec'),
         globals(), locals())
    exit_pass()
except:
    traceback.print_exc(file=sys.stdout)
    exit_fail()
"""


class ScriptCheckEngineParser(GenericParser):
    def parse(self, rule, metadata):
        check_metadata = metadata['check']
        engine = check_metadata.get('engine', 'shell')
        entrypoint = check_metadata.get('entrypoint')

        if entrypoint is None:
            if engine == 'shell':
                entrypoint = 'entrypoint.sh'
                self.shared_files.new(entrypoint, content=SHELL_ENTRYPOINT)
            elif engine == 'python':
                entrypoint = 'entrypoint.py'
                self.shared_files.new(entrypoint, content=PYTHON_ENTRYPOINT)
            else:
                raise Exception("Unsupported engine {}".format(engine))

        self.shared_files[entrypoint].set_executable()

        check = rule.add_check(system_ns='sce')\
            .check_import(import_name='stdout')\
            .check_import(import_name='stderr')\
            .check_content_ref(href=entrypoint)

        codeblock = check_metadata['codeblock']
        if engine == 'python':
            compressed_codeblock = textwrap.fill(
                base64.b64encode(zlib.compress(codeblock.encode())).decode(),
                120
            )
        else:
            compressed_codeblock = textwrap.fill(
                base64.b64encode(codeblock.encode()).decode(), 120)

        value = self.benchmark.new_value(
            '{}-codeblock'.format(rule.xccdf_id))\
            .set_value(compressed_codeblock)\
            .set_description(codeblock, plaintext=True)
        check.check_export(value.xccdf_id, 'CODEBLOCK')

        index = 0
        for id in chain(check_metadata.get('snippets', []),
                        check_metadata.get('include', [])):
            value = self.benchmark.get_value(self.generator.id('value', id))
            if value:
                index += 1
                check.check_export(value.xccdf_id, 'INCLUDE_{}'
                                   .format(str(index).rjust(2, '0')))
            else:
                raise Exception("Value referenced by id '{}' not found"
                                .format(id))

        for item in check_metadata.get('values', []):
            if isinstance(item, dict):
                value_id = next(iter(item))
                export_name = item[value_id].upper()
            else:
                value_id = item
                export_name = re.sub(r'[^\w\d]', '_', item).upper()

            value_xccdf_id = self.generator.id('value', value_id)
            check.check_export(value_id=value_xccdf_id,
                               export_name=export_name)
