from flask import Flask, jsonify, render_template, request
import json
import os
import tempfile

app = Flask(__name__)

from git_subprocess import Repository

repo_path = '/tmp/test/'

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
    return jsonify({
        'files': [
            _file_dict(f)
            for f in os.listdir(repo.path)
            if os.path.isfile(os.path.join(repo.path, f))
        ]
    })

# POST verb
@app.route('/api/files/', methods=['POST', ])
def add_file():
    f = request.files.get('file')

    # write the file out to its new location
    new_path = os.path.join(repo.path, f.filename)
    with open(new_path, 'w') as outfile:
        outfile.write(f.read())

    # add it to git and commit
    repo.add_file(
        file_path=f.filename,
        commit_author='Internet User <anon@inter.net>',
        commit_message='Commited file {}'.format(f.filename)
    )

    return json.dumps([_file_dict(new_path), ])

def _file_dict(f):
    return {
            'uid': f,
            'name': f,
            'size': os.path.getsize(os.path.join(repo.path, f)),
            'type': 'file',
            'parent_uid': 'null'
    }


if __name__ == '__main__':
    app.run(debug=True, port=5000)


