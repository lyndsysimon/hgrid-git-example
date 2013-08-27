import os
import shutil
import subprocess
import tempfile
import unittest

from git_subprocess import Repository, utils

AUTHOR_STRING = 'Test User <test@user.com>'
COMMIT_MESSAGE = 'Sample Commit Message'
FILE_NAME = 'foo.txt'
FILE_NAME_2 = 'bar.txt'
TEST_REPO = 'test_repository'
CLONED_REPO = 'cloned_repository'


class GitSubprocessTestCase(unittest.TestCase):
    def setUp(self):
        self.entry_path = os.getcwd()

        # base path containing all repos in test
        self.base_path = tempfile.mkdtemp()

        # path of the primary repo
        self.path = os.path.join(
            self.base_path,
            TEST_REPO,
        )

        # instantiate the repo's Repository object
        self.repo = Repository(self.path)

        # initialize the repo
        self.repo.init()

        # change directory to the repo's root
        os.chdir(self.path)

    @property
    def cloned_repo(self):
        return Repository(
            os.path.join(
                self.base_path,
                CLONED_REPO,
            )
        )

    def tearDown(self):
        shutil.rmtree(self.base_path)
        os.chdir(self.entry_path)

    def test_init(self):
        utils.silence(
            subprocess.check_call,
            ('git', 'status')
        )

    def test_stage_file(self):
        subprocess.call(('touch', FILE_NAME))
        self.repo._stage_file(FILE_NAME)

        self.assertIn(
            'A  {}'.format(FILE_NAME),
            subprocess.check_output(('git', 'status', '-s')),
        )

    def test_unstage_file(self):
        subprocess.call(('touch', FILE_NAME))
        self.repo._stage_file(FILE_NAME)
        self.repo._unstage_file(FILE_NAME)

        self.assertIn(
            '?? {}'.format(FILE_NAME),
            subprocess.check_output(('git', 'status', '-s'))
        )

    def test_commit(self):
        subprocess.call(('touch', FILE_NAME))
        self.repo._stage_file(FILE_NAME)
        self.repo.commit(AUTHOR_STRING, COMMIT_MESSAGE)

        self.assertNotIn(
            FILE_NAME,
            subprocess.check_output(('git', 'status', '-s')),
        )

    def test_add_file(self):
        subprocess.call(('touch', FILE_NAME))
        self.repo.add_file(
            file_path=FILE_NAME,
            commit_author=AUTHOR_STRING,
            commit_message=COMMIT_MESSAGE,
        )

        self.assertNotIn(
            FILE_NAME,
            subprocess.check_output(('git', 'status', '-s')),
        )

    def test_rm_file(self):
        subprocess.call(('touch', FILE_NAME))
        self.repo._stage_file(FILE_NAME)
        self.repo.commit(AUTHOR_STRING, COMMIT_MESSAGE)

        self.repo._rm_file(FILE_NAME)
        self.assertIn(
            'D  {}'.format(FILE_NAME),
            subprocess.check_output(('git', 'status', '-s')),
        )

    def test_delete_file(self):
        subprocess.call(('touch', FILE_NAME))
        self.repo._stage_file(FILE_NAME)
        self.repo.commit(AUTHOR_STRING, COMMIT_MESSAGE)

        self.repo.delete_file(
            file_path=FILE_NAME,
            commit_author=AUTHOR_STRING,
            commit_message=COMMIT_MESSAGE,
        )

        self.assertNotIn(
            FILE_NAME,
            subprocess.check_output(('git', 'status', '-s'))
        )

    def test_mv_file(self):
        subprocess.call(('touch', FILE_NAME))
        self.repo._stage_file(FILE_NAME)
        self.repo.commit(AUTHOR_STRING, COMMIT_MESSAGE)

        self.repo._mv_file(FILE_NAME, FILE_NAME_2)

        self.assertIn(
            'R  foo.txt -> bar.txt',
            subprocess.check_output(('git', 'status', '-s')),
        )

    def test_move_file(self):
        subprocess.call(('touch', FILE_NAME))
        self.repo._stage_file(FILE_NAME)
        self.repo.commit(AUTHOR_STRING, COMMIT_MESSAGE)

        self.repo.move_file(
            old_path=FILE_NAME,
            new_path=FILE_NAME_2,
            commit_author=AUTHOR_STRING,
            commit_message=COMMIT_MESSAGE,
        )

        self.assertNotIn(
            FILE_NAME,
            subprocess.check_output(('git', 'status', '-s'))
        )
        self.assertNotIn(
            FILE_NAME_2,
            subprocess.check_output(('git', 'status', '-s'))
        )

    def test_clone_repo(self):
        subprocess.call(
            ('touch', FILE_NAME),
            cwd=self.path,
        )
        self.repo._stage_file(FILE_NAME)
        self.repo.commit(AUTHOR_STRING, COMMIT_MESSAGE)

        self.cloned_repo.clone_from(self.path)

        self.assertNotEqual(
            os.path.abspath(self.cloned_repo.path),  # new repo
            os.path.abspath(self.repo.path)  # old repo
        )

        self.assertIn(
            FILE_NAME,
            subprocess.check_output('ls')
        )

    def test_staged_files(self):
        subprocess.call(('touch', FILE_NAME))
        self.repo.add_file(FILE_NAME, AUTHOR_STRING, COMMIT_MESSAGE)
        subprocess.call(('touch', FILE_NAME_2))
        self.repo._stage_file(FILE_NAME_2)

        self.assertEqual(
            set(self.repo.staged_files),
            set((FILE_NAME_2,)),
        )

    def test_unstaged_files(self):
        subprocess.call(('touch', FILE_NAME))
        self.repo.add_file(FILE_NAME, AUTHOR_STRING, COMMIT_MESSAGE)
        subprocess.call(('touch', FILE_NAME_2))

        self.assertEqual(
            set(self.repo.unstaged_files),
            set((FILE_NAME_2,)),
        )

    def test_untracked_files(self):
        subprocess.call(('touch', FILE_NAME))
        subprocess.call(('touch', FILE_NAME_2))

        self.assertEqual(
            set(self.repo.untracked_files),
            set((FILE_NAME, FILE_NAME_2,)),
        )

    def test_get_file_contents_by_sha(self):
        content_versions = ('0', '1', '2', '3', '4')
        for text in content_versions:
            with open(FILE_NAME, 'w') as f:
                f.write(text)
            self.repo.add_file(FILE_NAME, AUTHOR_STRING, COMMIT_MESSAGE)

        shas = self._get_shas(FILE_NAME)

        for i, text in enumerate(content_versions):
            self.assertEqual(
                self.repo._get_file_content(path=FILE_NAME, sha=shas[i]),
                text
            )

    def _get_shas(self, path):
        try:
            with open(os.devnull) as f:
                return [
                    x.strip('"')
                    for x
                    in subprocess.check_output(
                        ('git', 'log', '--format="%H"', '--', path),
                        stderr=f
                    ).strip().split('\n')[::-1]
                ]
        except subprocess.CalledProcessError:
            return []

    def test_get_file_invalid_path(self):
        with self.assertRaises(ValueError):
            self.repo.get_file('not_a_real_file.txt')

    def test_get_file(self):
        file_content = 'Center for Open Science'
        with open(FILE_NAME, 'w') as f:
            f.write(file_content)
        self.repo.add_file(FILE_NAME, AUTHOR_STRING, COMMIT_MESSAGE)

        self.assertRegexpMatches(
            repr(self.repo.get_file(FILE_NAME)),
            '^<File'
        )

    def test_get_file_content(self):
        file_content = 'Center for Open Science'
        with open(FILE_NAME, 'w') as f:
            f.write(file_content)
        self.repo.add_file(FILE_NAME, AUTHOR_STRING, COMMIT_MESSAGE)

        self.assertEqual(
            self.repo.get_file(FILE_NAME).content,
            file_content
        )

    def test_get_file_author(self):
        file_content = 'Center for Open Science'
        with open(FILE_NAME, 'w') as f:
            f.write(file_content)
        self.repo.add_file(FILE_NAME, AUTHOR_STRING, COMMIT_MESSAGE)

        self.assertEqual(
            self.repo.get_file(FILE_NAME).author,
            AUTHOR_STRING
        )

    def test_get_file_refspec(self):
        file_content = 'Center for Open Science'
        with open(FILE_NAME, 'w') as f:
            f.write(file_content)
        self.repo.add_file(FILE_NAME, AUTHOR_STRING, COMMIT_MESSAGE)

        self.assertEqual(
            str(self.repo.get_file(FILE_NAME)),
            FILE_NAME
        )

    def test_get_file_commit_message(self):
        file_content = 'Center for Open Science'
        with open(FILE_NAME, 'w') as f:
            f.write(file_content)
        self.repo.add_file(FILE_NAME, AUTHOR_STRING, COMMIT_MESSAGE)

        self.assertEqual(
            self.repo.get_file(FILE_NAME).message,
            COMMIT_MESSAGE
        )

    def test_get_file_version(self):
        file_content = 'Center for Open Science'
        with open(FILE_NAME, 'w') as f:
            f.write(file_content)
        self.repo.add_file(FILE_NAME, AUTHOR_STRING, COMMIT_MESSAGE)

        self.assertRegexpMatches(
            repr(self.repo.get_file(FILE_NAME).versions[0]),
            '^<FileVersion'
        )

    def test_get_file_version_refspec(self):
        file_content = 'Center for Open Science'
        with open(FILE_NAME, 'w') as f:
            f.write(file_content)
        self.repo.add_file(FILE_NAME, AUTHOR_STRING, COMMIT_MESSAGE)

        self.assertRegexpMatches(
            str(self.repo.get_file(FILE_NAME).versions[0]),
            '^(\w){40} -- foo\.txt$'
        )

    def test_get_file_version_by_sha(self):
        content_versions = ('0', '1', '2', '3', '4')
        for text in content_versions:
            with open(FILE_NAME, 'w') as f:
                f.write(text)
            self.repo.add_file(FILE_NAME, AUTHOR_STRING, COMMIT_MESSAGE)

        shas = self._get_shas(FILE_NAME)

        for i, text in enumerate(content_versions):
            self.assertEqual(
                self.repo.get_file(path=FILE_NAME).get_version_by_sha(shas[i]).content,
                str(i)
            )