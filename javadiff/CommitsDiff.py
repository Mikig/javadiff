from difflib import restore
from javalang.parser import JavaParserBaseException
try:
    from .FileDiff import FileDiff, FormatPatchFileDiff
except:
    from FileDiff import FileDiff, FormatPatchFileDiff


class CommitsDiff(object):
    def __init__(self, child, parent, analyze_source_lines=True):
        self.diffs = list(CommitsDiff.diffs(child, parent, analyze_source_lines=analyze_source_lines))

    @staticmethod
    def diffs(child, parent, analyze_source_lines=True):
        for d in parent.tree.diff(child.tree, ignore_blank_lines=True, ignore_space_at_eol=True):
            try:
                yield FileDiff(d, child.hexsha, analyze_source_lines=analyze_source_lines)
            except Exception as e:
                pass


class FormatPatchDiff(object):
    DEV_NULL = '/dev/null'

    def __init__(self, lines):
        assert lines[0].startswith('--- '), lines[0]
        assert lines[1].startswith('+++ '), lines[1]
        self.a_path = lines[0][4:].replace('\n', '').replace('a/', '')
        self.b_path = lines[1][4:].replace('\n', '').replace('b/', '')
        self.new_file = self.a_path == FormatPatchDiff.DEV_NULL
        self.deleted_file = self.b_path == FormatPatchDiff.DEV_NULL
        self.file_name = self.a_path if self.deleted_file else self.b_path
        self.before_contents = ['']
        self.after_contents = ['']
        if not '.java' in self.a_path and not '.java' in self.b_path:
            return
        self.normal_diff = list(map(lambda x: x[0] + " " + x[1:], lines[3:]))
        if not self.new_file:
            self.before_contents = list(restore(self.normal_diff, 1))
        if not self.deleted_file:
            self.after_contents = list(restore(self.normal_diff, 2))



class FormatPatchCommitsDiff(object):
    def __init__(self, file_name, analyze_source_lines=True):
        self.commit = FormatPatchCommitsDiff.read_commit_sha(file_name)
        self.diffs = list(FormatPatchCommitsDiff.diffs(file_name, analyze_source_lines=analyze_source_lines))


    @staticmethod
    def read_commit_sha(file_name):
        with open(file_name) as f:
            lines = f.readlines()[:-3]
        if len(lines) == 0:
            return ''
        return str(lines[0].split()[1])  # line 0 word 1

    @staticmethod
    def diffs(file_name, analyze_source_lines):
        with open(file_name) as f:
            lines = list(filter(lambda l: 'new file mode' not in l and 'new mode' not in l, f.readlines()[:-3]))
        if len(lines) == 0:
            raise StopIteration()
        commit_sha = str(lines[0].split()[1])  # line 0 word 1
        diff_inds = map(lambda x: x[0], filter(lambda x: x[1].startswith("diff --git"), enumerate(lines))) + [len(lines)]
        for i1, i2 in zip(diff_inds, diff_inds[1:]):
            try:
                if 'GIT binary' in lines[i1 + 2]:
                    continue
                fd = FormatPatchDiff(lines[i1 + 2: i2])
                if fd.file_name.endswith(".java"):
                    yield FormatPatchFileDiff(fd, commit_sha, analyze_source_lines=analyze_source_lines)
            except IndexError as e:
                pass
            except JavaParserBaseException as e:
                pass
