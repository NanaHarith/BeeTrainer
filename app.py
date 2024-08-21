from flask import Flask, render_template, request, redirect, url_for, session
import csv
import pyttsx3
import threading


app = Flask(__name__)
app.secret_key = 'your_secret_key'

#@app.before_request
#def clear_session():
 #   session.clear()
# Load words from CSV file
def load_words():
    with open('c:/temp/WordList.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        words = [row['word'] for row in reader]
    return words


# Text-to-Speech Function
def speak(word):
    engine = pyttsx3.init()
    engine.say(word)
    engine.runAndWait()


@app.route('/')
def index():
    if 'words' not in session:
        session['words'] = load_words()
        session['current_word_index'] = 0
        session['correct_words'] = []
        session['incorrect_words'] = []
        session['current_word_index'] = 0
        session['total_correct'] = 0
        session['total_incorrect'] = 0

    current_word = session['words'][session['current_word_index']]

    # Use threading to avoid blocking the main thread
    threading.Thread(target=speak, args=(current_word,)).start()

    return render_template('index.html',
                           total_words=len(session['words']),
                           total_correct=session['total_correct'],
                           total_incorrect=session['total_incorrect'],
                           current_index=session['current_word_index'] + 1)


@app.route('/submit', methods=['POST'])
def submit():
    user_input = request.form['spelling'].strip().lower()
    current_word = session['words'][session['current_word_index']].strip().lower()

    if user_input == current_word:
        session['total_correct'] += 1
        session['correct_words'].append(current_word)
    else:
        session['total_incorrect'] += 1
        session['incorrect_words'].append(current_word)

    # Move to the next word
    session['current_word_index'] += 1

    if session['current_word_index'] < len(session['words']):
        return redirect(url_for('index'))
    else:
        return redirect(url_for('results'))


@app.route('/next_word', methods=['POST'])
def next_word():
    session['current_word_index'] += 1

    if session['current_word_index'] < len(session['words']):
        return redirect(url_for('index'))
    else:
        return redirect(url_for('results'))


@app.route('/repeat', methods=['POST'])
def repeat():
    current_word = session['words'][session['current_word_index']]
    threading.Thread(target=speak, args=(current_word,)).start()
    return redirect(url_for('index'))


@app.route('/results')
def results():
    return render_template('results.html',
                           total_correct=session['total_correct'],
                           total_incorrect=session['total_incorrect'],
                           correct_words=session['correct_words'],
                           incorrect_words=session['incorrect_words'])


if __name__ == '__main__':
    app.run(debug=True)
