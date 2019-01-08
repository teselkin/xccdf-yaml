import os
import shutil
import stat

from xccdf_yaml.misc import resolve_file_ref


class SharedFile(object):
    def __init__(self, name):
        self._name = name
        self._sourcepath = None
        self._sourcefile = None
        self._content = None
        self._executable = False

    def __eq__(self, other):
        if self.name != other.filename:
            return False

        if self.abspath and other.abspath:
            if os.path.abspath(self.abspath) \
                    != os.path.abspath(other.abspath):
                return False

        if self.content and other.content:
            if self.content != other.content:
                return False

        return True

    @classmethod
    def new(cls, name, sourcepath=None, sourcefile=None, content=None):
        obj = cls(name)
        if sourcepath and sourcefile:
            obj.set_source(sourcepath, sourcefile)

        if content:
            obj.set_content(content)

        return obj

    @property
    def name(self):
        return self._name

    @property
    def content(self):
        return self._content

    @property
    def abspath(self):
        if self._sourcepath and self._sourcefile:
            return os.path.abspath(os.path.join(self._sourcepath,
                                                self._sourcefile))

    def set_executable(self, executable=True):
        self._executable = executable == True

    def set_content(self, content):
        content = content.strip()
        if self._content is None:
            self._content = content
            return

        if self._content != content:
            raise Exception("Attempt to replace content of {}"
                            .format(self.name))

    def set_source(self, sourcepath, sourcefile):
        if self._sourcepath is None and self._sourcefile is None:
            self._sourcepath = sourcepath
            self._sourcefile = sourcefile
            return

        p1 = os.path.abspath(
            os.path.join(self._sourcepath, self._sourcefile))
        p2 = os.path.abspath(os.path.join(sourcepath, sourcefile))

        if p1 != p2:
            raise Exception("Attempt to replace source path of "
                            "'{}': '{}' --> '{}'"
                            .format(self.name, p1, p2))

    def export(self, output_dir=os.getcwd()):
        target = os.path.join(output_dir, self._name)
        os.makedirs(os.path.dirname(target), exist_ok=True)

        if self._content:
            with open(target, 'w') as f:
                f.write(self._content)
        else:
            sourcefile = self.abspath
            if sourcefile:
                if os.path.exists(sourcefile):
                    shutil.copyfile(sourcefile, target)
                else:
                    raise Exception("Shared file '{}' not found"
                                    .format(sourcefile))

        if os.path.exists(target):
            if self._executable:
                x = os.stat(target)
                os.chmod(target, x.st_mode | stat.S_IEXEC)


class SharedFiles(object):
    def __init__(self, workdir, basedir):
        self.basedir = basedir
        self.workdir = workdir
        self._shared_files = {}

    def new(self, name, sourceref=None, content=None):
        shared_file = SharedFile(name)

        if sourceref:
            sourcepath, sourcefile = resolve_file_ref(sourceref,
                                                      basedir=self.basedir,
                                                      workdir=self.workdir)
            shared_file.set_source(sourcepath=sourcepath,
                                   sourcefile=sourcefile)

        if content:
            shared_file.set_content(content)

        self.append(shared_file)

        return shared_file

    def append(self, shared_file):
        if shared_file.name in self._shared_files:
            if self._shared_files[shared_file.filename] != shared_file:
                raise Exception("Shared file {} already exists"
                                .format(shared_file.filename))

        self._shared_files[shared_file.name] = shared_file
        return shared_file

    def setdefault(self, shared_file):
        return self._shared_files.setdefault(shared_file.filename, shared_file)

    def export(self, output_dir):
        if not os.path.isabs(output_dir):
            output_dir = os.path.abspath(
                os.path.join(self.workdir, output_dir))

        for shared_file in self._shared_files.values():
            shared_file.export(output_dir)
