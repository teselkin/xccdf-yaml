from xccdf_yaml.parsers.common import ParsedObjects

import os
import stat


SHELL_WRAPPER_HEAD = """#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset
trap \'exit_fail\' ERR
exit_pass(){ exit ${XCCDF_RESULT_PASS:-0}; }
exit_fail(){ exit ${XCCDF_RESULT_FAIL:-1}; }
set -o xtrace

"""

SHELL_WRAPPER_TAIL = """
exit_pass
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
            filename = '{}.sh'.format(id)
            target_filename = os.path.join(self.output_dir, filename)
            with open(target_filename, 'w') as f:
                f.write(SHELL_WRAPPER_HEAD)
                f.write('{}\n'.format(metadata['cmd']))
                f.write(SHELL_WRAPPER_TAIL)
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

        rule.add_check(system_ns='sce')\
            .check_import({'import-name': 'stdout'})\
            .check_content_ref({'href': filename})

        return res
