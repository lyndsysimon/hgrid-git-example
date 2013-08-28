from flask import abort, Flask, jsonify, render_template, request
import json
import os
import tempfile
from distutils.dir_util import mkpath

app = Flask(__name__)

from git_subprocess import Repository

repo_path = '/tmp/test' #'/Users/lyndsysimon/Documents/Development/cos/hgrid-example/'

# Set up a git repository for a storage backend
repo = Repository(repo_path or tempfile.mkdtemp())
repo.init()

# Homepage - just render the template
@app.route('/')
def index():
    return render_template('index.html')

# DELETE verb
@app.route('/api/files/', methods=['DELETE', ])
def delete_files():
    # since multiple items could be deleted at once, iterate the list.
    for id in json.loads(request.form.get('ids', '[]')):
        repo._rm_file(id)
    repo.commit(
        author='Internet User <anon@inter.net>',
        message='Deleted file(s)',
    )

    return jsonify({'deleted': request.form.get('ids')})

# GET verb
@app.route('/api/files/', methods=['GET', ])
def get_files():
    nodes = []
    for root, dirs, files in os.walk(repo.path):
        files = [f for f in files if not _is_hidden(
            os.path.abspath(os.path.join(root, f))
        )]
        dirs = [d for d in dirs if not _is_hidden(
            os.path.abspath(os.path.join(root, d))
        )]
        path = os.path.relpath(root, repo.path)
        # add files
        for f in files:
            nodes.append({
                'uid': os.path.join(path, f) if path != os.path.curdir else f,
                'name': f,
                'type': 'file',
                'size': os.path.getsize(os.path.join(root, f)),
                'parent_uid': "null" if path == os.path.curdir else path,
                'depth': 0 if path == os.path.curdir else len(path.split('/')),
            })
        # add subdirectories
        for dir in dirs:
            nodes.append({
                'uid': os.path.join(path, dir) if path != os.path.curdir else dir,
                'name': dir,
                'type': 'folder',
                'parent_uid': "null" if path == os.path.curdir else path,
                'depth': 0 if path == os.path.curdir else len(path.split('/')),
            })

    return jsonify({'files': nodes})

# POST verb
@app.route('/api/files/', methods=['POST', ])
def add_file():
    if len(request.files) > 0:
        f = request.files.get('file')

        # write the file out to its new location
        new_path = os.path.join(repo.path, f.filename)
        with open(new_path, 'w') as outfile:
            outfile.write(f.read())

        # add it to git and commit
        repo.add_file(
            file_path=f.filename,
            commit_author='Internet User <anon@inter.net>',
            commit_message='Committed file {}'.format(f.filename)
        )

        return json.dumps([_file_dict(new_path), ])
    elif request.form.get('action'):
        if request.form.get('action') == 'add_folder':
            path = request.form.get('path')
            dirname = request.form.get('name')

            # if the user is trying to access something outside the repo
            if os.path.pardir in path:
                abort(400)


    else:
        abort(400)

def _file_dict(f):
    path = os.path.join(repo.path, f)

    return {
        'uid': f,
        'name': f,
        'size': os.path.getsize(os.path.join(repo.path, f)),
        'type': (
            'file' if os.path.isfile(path)
            else 'folder' if os.path.isdir(path)
            else ''
        ),
        'parent_uid': 'null'
    }


def _is_hidden(path):
    ''' Return True if a file is hidden, else false.

    This doesn't support anything except files beginning with "." for now.
    '''

    if os.path.basename(path).startswith('.'):
        return True
    else:
        dir = os.path.dirname(path)
        if dir == path:
            return False
        else:
            return _is_hidden(dir)


if __name__ == '__main__':
    app.run(debug=True, port=5000)


