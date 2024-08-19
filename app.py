from flask import Flask, render_template, request, jsonify, session
import pandas as pd
import os
from werkzeug.utils import secure_filename
from multiprocessing import Process, Queue
import pyttsx3

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a real secret key

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Global variables
words = []
current_word_index = -1
tts_queue = Queue()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def tts_process(queue):
    engine = pyttsx3.init()
    while True:
        word = queue.get()
        if word is None:
            break
        engine.say(word)
        engine.runAndWait()


@app.route('/', methods=['GET', 'POST'])
def index():
    global words, current_word_index

    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No selected file'})

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Read the file
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath)

            words = df.iloc[:, 0].tolist()
            current_word_index = -1
            session['score'] = {'right': 0, 'wrong': 0}
            session['results'] = []

            return jsonify({'message': 'File uploaded successfully', 'word_count': len(words)})

    return render_template('index.html')


@app.route('/next_word', methods=['GET'])
def next_word():
    global current_word_index, tts_queue

    current_word_index += 1

    if current_word_index < len(words):
        word = words[current_word_index]
        tts_queue.put(word)
        return jsonify({'word': word, 'index': current_word_index + 1, 'total': len(words)})
    else:
        return jsonify({'message': 'No more words'})


@app.route('/repeat_word', methods=['GET'])
def repeat_word():
    global current_word_index, tts_queue

    if current_word_index >= 0 and current_word_index < len(words):
        word = words[current_word_index]
        tts_queue.put(word)
        return jsonify({'word': word, 'index': current_word_index + 1, 'total': len(words)})
    else:
        return jsonify({'message': 'No word to repeat'})


@app.route('/check_spelling', methods=['POST'])
def check_spelling():
    data = request.json
    user_spelling = data['spelling']
    correct_spelling = words[current_word_index]

    if user_spelling.lower() == correct_spelling.lower():
        session['score']['right'] += 1
        result = 'correct'
    else:
        session['score']['wrong'] += 1
        result = 'incorrect'

    session['results'].append({
        'word': correct_spelling,
        'user_spelling': user_spelling,
        'result': result
    })
    session.modified = True

    return jsonify({
        'result': result,
        'correct_spelling': correct_spelling,
        'score': session['score']
    })


@app.route('/results', methods=['GET'])
def results():
    return render_template('results.html', results=session.get('results', []),
                           score=session.get('score', {'right': 0, 'wrong': 0}))


if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    p = Process(target=tts_process, args=(tts_queue,))
    p.start()
    app.run(debug=False, use_reloader=False)
    tts_queue.put(None)
    p.join()