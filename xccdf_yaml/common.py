import os
import re
import shutil
import stat


class SharedFile(object):
    def __init__(self, filename, basedir):
        self.basedir = basedir
        self.filename = filename
        self._source = None
        self._content = None
        self._executable = False

    def __eq__(self, other):
        if self.filename != other.filename:
            return False

        if self.source and other.source:
            if os.path.abspath(self.source) != os.path.abspath(other.source):
                return False

        if self.content and other.content:
            if self.content != other.content:
                return False

        return True

    @classmethod
    def with_content(cls, filename, content):
        obj = cls(filename)
        obj.set_content(content)
        return obj

    @classmethod
    def from_source(cls, source, basedir=os.getcwd(), filename=None):
        if filename is None:
            filename = source

        obj = cls(basedir=basedir, filename=filename)
        obj.set_source(source)

        return obj

    @property
    def basename(self):
        return os.path.basename(self.filename)

    @property
    def content(self):
        return self._content

    @property
    def source(self):
        return self._source

    def set_executable(self, executable=True):
        if executable is True:
            self._executable = True
        else:
            self._executable = False

    def set_content(self, content):
        content = content.strip()
        if self._content is None:
            self._content = content
            return

        if self._content != content:
            raise Exception("Attempt to replace content of {}"
                            .format(self.filename))

    def set_source(self, source):
        if self._source is None:
            self._source = source
            return

        if os.path.abspath(self._source) != os.path.abspath(source):
            raise Exception("Attempt to replace source path of {}"
                            .format(self.filename))

    def export(self, workdir, output_dir):
        target = os.path.join(output_dir, self.filename)
        os.makedirs(os.path.dirname(target), exist_ok=True)

        if self._content:
            with open(target, 'w') as f:
                f.write(self._content)
        else:
            if self.source:
                if re.match(r'\.+\/', self.source):
                    source = os.path.join(workdir, self.source)
                else:
                    source = os.path.join(self.basedir, self.source)
            else:
                source = os.path.join(workdir, self.filename)

            if os.path.exists(source):
                shutil.copyfile(source, target)
            else:
                raise Exception("Shared file '{}' not found".format(source))

        if os.path.exists(target):
            if self._executable:
                x = os.stat(target)
                os.chmod(target, x.st_mode | stat.S_IEXEC)


class SharedFiles(object):
    def __init__(self, workdir, basedir=os.getcwd()):
        self.basedir = basedir
        self.workdir = workdir
        self._shared_files = {}

    def append(self, shared_file):
        if shared_file.filename in self._shared_files:
            if self._shared_files[shared_file.filename] != shared_file:
                raise Exception("Shared file {} already exists"
                                .format(shared_file.filename))

        self._shared_files[shared_file.filename] = shared_file
        return shared_file

    def from_source(self, source, filename=None):
        if filename is None:
            filename = source

        shared_file = SharedFile.from_source(
            basedir=self.basedir, source=source, filename=filename)
        self.append(shared_file)

        return shared_file

    def setdefault(self, shared_file):
        return self._shared_files.setdefault(shared_file.filename, shared_file)

    def export(self, output_dir):
        for shared_file in self._shared_files.values():
            shared_file.export(workdir=self.workdir, output_dir=output_dir)
