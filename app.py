from flask import Flask, jsonify, render_template, request
import json

app = Flask(__name__)

# Our "storage" is just an in-memory list of dicts.
files = [
    {
        'uid': 'foo',
        'name': 'foo.txt',
        'size': '124',
        'parent_uid': "null",
        'type': 'file'
    },
    {
        'uid': 'bar',
        'name': 'bar.txt',
        'size': '124',
        'parent_uid': "null",
        'type': 'file'
    },
    {
        'uid': 'baz',
        'name': 'baz.txt',
        'size': '124',
        'parent_uid': "null",
        'type': 'file'
    },
    {
        'uid': 'qiz',
        'name': 'qiz.txt',
        'size': '124',
        'parent_uid': "null",
        'type': 'file'
    },
]

# Homepage - just render the template
@app.route('/')
def index():
    return render_template('index.html')

# DELETE verb
@app.route('/api/files/', methods=['DELETE', ])
def delete_files():
    deleted = []

    # Contrived - remove each UID from the list of dicts
    for id in json.loads(request.form.get('ids')):
        for idx, f in enumerate(files):
            print id, f
            if f.get('uid') == id:
                deleted.append(id)
                del files[idx]

    return jsonify({'deleted': deleted})

# GET verb
@app.route('/api/files/', methods=['GET', ])
def get_files():
    return jsonify({'files': files})

# POST verb
@app.route('/api/files/', methods=['POST', ])
def add_file():
    f = request.files.get('file')
    f_d = {
        'uid': f.filename.split('.')[0],
        'name': f.filename,
        'size': 123,
        'parent_uid': "null",
        'type': 'file',
    }
    files.append(f_d)
    return json.dumps([f_d, ])



if __name__ == '__main__':
    app.run(debug=True, port=5000)


