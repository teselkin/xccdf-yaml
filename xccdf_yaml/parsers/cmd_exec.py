from xccdf_yaml.parsers.common import ParsedObjects

import os
import stat
import shutil


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
                for url, text in reference.items():
                    ref.set_attr('href', url).set_text(text)
            else:
                ref.set_text(reference)

        if 'rationale' in metadata:
            rule.sub_element('rationale')\
                .set_text(metadata['rationale'].rstrip())

        if 'cmd' in metadata:
            filename = '{}.sh'.format(id)
            target_filename = os.path.join(self.output_dir, filename)
            with open(target_filename, 'w') as f:
                f.write('#!/bin/bash\n')
                f.write('set -o errexit\n')
                f.write('set -o pipefail\n')
                f.write('set -o nounset\n')
                f.write('set -o xtrace\n')
                f.write('trap \'exit_fail\' ERR\n')
                f.write('exit_pass(){ exit ${XCCDF_RESULT_PASS:-0}; }\n')
                f.write('exit_fail(){ exit ${XCCDF_RESULT_FAIL:-1}; }\n')
                f.write('{}\n'.format(metadata['cmd']))
                f.write('exit_pass\n')
        elif 'filename' in metadata:
            filename = metadata['filename']
            target_filename = os.path.join(self.output_dir, filename)
            shutil.copyfile(filename, target_filename)
        else:
            raise Exception('No script or cmdline found')

        if os.path.exists(target_filename):
            x = os.stat(target_filename)
            os.chmod(target_filename, x.st_mode | stat.S_IEXEC)

        rule.add_check(system_ns='sce')\
            .check_import({'import-name': 'stdout'})\
            .check_content_ref({'href': filename})

        return res
