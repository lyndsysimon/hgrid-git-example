import os
import subprocess


class File(object):
    def __init__(self, repo, path):
        self.repo = repo
        self.path = path

        self.versions = []

        for sha in self._get_versions(path):
            self.versions.append(sha)

    def __getattr__(self, item):
        return getattr(self.versions[0], item)

    def __repr__(self):
        return '<File(path="{}">'.format(
            self.path
        )

    def __str__(self):
        return self.path
    __unicode__ = __str__

    _log_format = '--format="%H|%aD|%aN|<%ae>|%s"'

    def get_version_by_sha(self, sha):
        info = subprocess.check_output(
            (
                'git',
                'log',
                '--follow',
                self._log_format,
                '-n 1',
                sha,
                '--',
                self.path,
            ),
            cwd=self.repo.path
        )[1:-2]

        return self._get_version_from_log(info)

    def _get_versions(self, path):
        try:
            with open(os.devnull) as f:
                raw_commits = [
                    x[1:-1]
                    for x
                    in subprocess.check_output(
                        (
                            'git',
                             'log',
                             '--follow',
                             self._log_format,
                             '--',
                             path
                        ),
                        stderr=f,
                        cwd=self.repo.path,
                    ).strip().split('\n')[::-1]
                ]
        except subprocess.CalledProcessError:
            raise ValueError(
                'File "{}" not found in commit history'.format(path)
            )

        parsed_commits = []

        for line in raw_commits:
            parsed_commits.append(self._get_version_from_log(line))

        return parsed_commits

    def _get_version_from_log(self, log):
        pcs = log.split('|')
        return FileVersion(
            repo=self.repo,
            path=self.path,
            sha=pcs[0],
            date=pcs[1],
            author_name=pcs[2],
            author_email=pcs[3],
            message='|'.join(pcs[4:]),
        )


class FileVersion(object):
    def __init__(self, repo, path, sha, date, message, author_name, author_email):
        self.repo = repo
        self.path = path
        self.sha = sha
        self.date = date
        self.message = message.strip('" ')
        self.author_name = author_name
        self.author_email = author_email

    @property
    def content(self):
        return self.repo._get_file_content(self.path, self.sha)

    @property
    def author(self):
        return ' '.join((self.author_name, self.author_email))

    def __repr__(self):
        return '<FileVersion(path="{}" sha="{}")>'.format(
            self.path,
            self.sha[-7:]
        )

    def __str__(self):
        return '{} -- {}'.format(self.sha, self.path)

    __unicode__ = __str__