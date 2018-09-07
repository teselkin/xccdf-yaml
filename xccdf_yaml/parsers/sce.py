from xccdf_yaml.parsers.common import GenericParser
from xccdf_yaml.parsers.common import ParsedObjects

import re


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
if [[ -f "${XCCDF_VALUE_FILENAME}" ]]; then
  set -o xtrace
  source "${XCCDF_VALUE_FILENAME}"
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
    filename = os.environ.get('XCCDF_VALUE_FILENAME')
    exec(compile(open(filename, "rb").read(), filename, 'exec'), globals(), locals())
    exit_pass()
except:
    traceback.print_exc(file=sys.stdout)
    exit_fail()
"""


class ScriptCheckEngineParser(GenericParser):
    def parse(self, id, metadata):
        res = ParsedObjects(self.xccdf)

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

        check = metadata['check']
        engine = check.get('engine', 'shell')
        entrypoint = check.get('entrypoint')

        if engine == 'shell':
            if entrypoint is None:
                entrypoint = 'entrypoint.sh'
            res.add_shared_file(entrypoint, SHELL_ENTRYPOINT)
        elif engine == 'python':
            if entrypoint is None:
                entrypoint = 'entrypoint.py'
            res.add_shared_file(entrypoint, PYTHON_ENTRYPOINT)
        else:
            raise Exception("Unsupported engine {}".format(engine))

        res.add_entrypoint(entrypoint)
        res.add_shared_file('{}.sh'.format(id), check['codeblock'])

        check = rule.add_check(system_ns='sce')\
            .check_import(import_name='stdout')\
            .check_import(import_name='stderr')\
            .check_content_ref(href=entrypoint)

        value = self.benchmark.new_value(
            '{}-filename'.format(rule.get_attr('id')))\
            .set_value('{}.sh'.format(id))
        check.check_export(value.get_attr('id'), 'FILENAME')

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
