from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate():
    model = request.json.get('model')
    prompt = request.json.get('prompt')
    images = request.json.get('images')
    format = request.json.get('format')
    options = request.json.get('options')
    system = request.json.get('system')
    template = request.json.get('template')
    context = request.json.get('context')
    stream = request.json.get('stream', True)
    raw = request.json.get('raw', False)
    keep_alive = request.json.get('keep_alive', 300)

    url = f'http://localhost:11434/api/generate'
    payload = {
        'model': model,
        'prompt': prompt,
        'images': images,
        'format': format,
        'options': options,
        'system': system,
        'template': template,
        'context': context,
        'stream': stream,
        'raw': raw,
        'keep_alive': keep_alive
    }
    response = requests.post(url, json=payload)
    return jsonify(response.json()), response.status_code

@app.route('/chat', methods=['POST'])
def chat():
    model = request.json.get('model')
    messages = request.json.get('messages')
    format = request.json.get('format')
    options = request.json.get('options')
    stream = request.json.get('stream', True)
    keep_alive = request.json.get('keep_alive', 300)

    url = f'http://localhost:11434/api/chat'
    payload = {
        'model': model,
        'messages': messages,
        'format': format,
        'options': options,
        'stream': stream,
        'keep_alive': keep_alive
    }
    response = requests.post(url, json=payload)
    return jsonify(response.json()), response.status_code

@app.route('/create', methods=['POST'])
def create():
    name = request.json.get('name')
    modelfile = request.json.get('modelfile')
    stream = request.json.get('stream', True)
    path = request.json.get('path')

    url = f'http://localhost:11434/api/create'
    payload = {
        'name': name,
        'modelfile': modelfile,
        'stream': stream,
        'path': path
    }
    response = requests.post(url, json=payload)
    return jsonify(response.json()), response.status_code

@app.route('/show', methods=['POST'])
def show():
    name = request.json.get('name')

    url = f'http://localhost:11434/api/show'
    payload = {
        'name': name
    }
    response = requests.post(url, json=payload)
    return jsonify(response.json()), response.status_code

@app.route('/copy', methods=['POST'])
def copy():
    source = request.json.get('source')
    destination = request.json.get('destination')

    url = f'http://localhost:11434/api/copy'
    payload = {
        'source': source,
        'destination': destination
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return jsonify({'message': 'Model copied successfully'}), 200
    else:
        return jsonify({'error': 'Model not found'}), 404

@app.route('/delete', methods=['DELETE'])
def delete():
    name = request.json.get('name')

    url = f'http://localhost:11434/api/delete'
    payload = {
        'name': name
    }
    response = requests.delete(url, json=payload)
    if response.status_code == 200:
        return jsonify({'message': 'Model deleted successfully'}), 200
    else:
        return jsonify({'error': 'Model not found'}), 404

@app.route('/pull', methods=['POST'])
def pull():
    name = request.json.get('name')
    insecure = request.json.get('insecure', False)
    stream = request.json.get('stream', True)

    url = f'http://localhost:11434/api/pull'
    payload = {
        'name': name,
        'insecure': insecure,
        'stream': stream
    }
    response = requests.post(url, json=payload)
    return jsonify(response.json()), response.status_code

@app.route('/push', methods=['POST'])
def push():
    name = request.json.get('name')
    insecure = request.json.get('insecure', False)
    stream = request.json.get('stream', True)

    url = f'http://localhost:11434/api/push'
    payload = {
        'name': name,
        'insecure': insecure,
        'stream': stream
    }
    response = requests.post(url, json=payload)
    return jsonify(response.json()), response.status_code

@app.route('/blobs/<digest>', methods=['HEAD'])
def check_blob(digest):
    url = f'http://localhost:11434/api/blobs/{digest}'
    response = requests.head(url)
    if response.status_code == 200:
        return jsonify({'message': 'Blob exists'}), 200
    else:
        return jsonify({'error': 'Blob not found'}), 404

@app.route('/blobs/<digest>', methods=['POST'])
def create_blob(digest):
    url = f'http://localhost:11434/api/blobs/{digest}'
    files = {'file': open('model.bin', 'rb')}
    response = requests.post(url, files=files)
    if response.status_code == 201:
        return jsonify({'message': 'Blob created successfully'}), 201
    else:
        return jsonify({'error': 'Blob creation failed'}), 400

@app.route('/tags', methods=['GET'])
def list_models():
    url = f'http://localhost:11434/api/tags'
    response = requests.get(url)
    return jsonify(response.json()), response.status_code

@app.route('/embeddings', methods=['POST'])
def generate_embeddings():
    model = request.json.get('model')
    prompt = request.json.get('prompt')
    options = request.json.get('options')
    keep_alive = request.json.get('keep_alive', 300)

    url = f'http://localhost:11434/api/embeddings'
    payload = {
        'model': model,
        'prompt': prompt,
        'options': options,
        'keep_alive': keep_alive
    }
    response = requests.post(url, json=payload)
    return jsonify(response.json()), response.status_code

if __name__ == '__main__':
    app.run()


