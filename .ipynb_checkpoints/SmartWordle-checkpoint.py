from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_cors import CORS
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import sqlite3
import os

app = Flask(__name__)
CORS(app)
secret_key = os.urandom(24)
app.secret_key = os.environ.get('SECRET_KEY') or 'optional_default_key'  # Necessary for session management and flashing messages

# conn = sqlite3.connect('data.db')
# query = ('''Create Word Database Per User
#             (WORD     TEXT     NOT NULL,
#              GUESS    INT      NOT NULL);''')
# conn.execute(query)
# conn.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Extract form data
        username = request.form['username']
        password = request.form['password']  # In production, ensure this is hashed

        # Insert into the database (example using SQLite)
        try:
            # Get the current directory of the script.
            basedir = os.path.abspath(os.path.dirname(__file__))
            
            # Adjust the path to the database file to include the db folder.
            database_path = os.path.join(basedir, 'db', 'users.db')
            
            # Now you can use this path in your SQLite connection
            conn = sqlite3.connect(database_path)
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password))
            conn.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('home'))  # Redirect to login page after successful registration
        except sqlite3.IntegrityError:
            flash('Username already exists!', 'error')
        finally:
            conn.close()
    return render_template('register.html')
    
@app.route('/')
def home():
    return render_template('SmartWordle.html')

@app.route('/choose_new_word', methods=['POST'])
def choose_new_word_api():
    content = request.json
    dic = content.get('dic', {})
    test_words = content.get('test', [])  # This should match the expected structure in `choose_new_word`
    letter_frequency = content.get('frequency', {})
    result_word = choose_new_word(dic, test_words, letter_frequency)
    return jsonify({'word': result_word})

def word_to_numbers(word):
    word = word.lower()
    # Convert each character in the word to a number and return as a 2D array
    return np.array([[ord(char) - ord('a') + 1 for char in word]])

def letter_frequency(word, letter_freqs):
    # Ensure the word is uppercase for consistency
    word = word.upper()
    sum_freq = sum(letter_freqs.get(letter, 0) for letter in word)
    return sum_freq * 0.05

def choose_new_word(dic, test_words, letter_freqs):
    # Prepare training data with updated features
    X_train = np.array([word_to_numbers(key)[0] for key in dic.keys()])
    y_train = np.array(list(dic.values()))
    
    # Prepare testing data
    X_test = np.array([word_to_numbers(word)[0] for word in test_words])  # This ensures it's a 2D array

    # Initialize and train the model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Make predictions and evaluate
    predictions = model.predict(X_test)
    
    hard_words = []

    # Associate the predictions with the corresponding words
    for word, prediction in zip(test_words, predictions):
        hard_words.append([round(prediction, 2), word])
        
    # Penalizes the difficulty of the words that uses more commonly guessed letters
    for word in hard_words:
        word[0] = word[0] - letter_frequency(word[1], letter_freqs)
        
    hard_words.sort(reverse=True)
    return hard_words[0][1]  # Return the word with the highest prediction value

if __name__ == '__main__':
    app.run(debug=True, port=5000)