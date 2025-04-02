from flask import Flask, render_template, request, redirect, url_for, session
import csv
import random
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper function to read CSV and return flashcards
def load_flashcards(file_path):
    flashcards = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) == 2:  # Ensure each row has a question and answer
                flashcards.append({'question': row[0], 'answer': row[1]})
    return flashcards

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        if file and file.filename.endswith('.csv'):
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            session['flashcards'] = load_flashcards(file_path)
            session['current_index'] = 0
            session['repetitions'] = {}
            session['completed'] = []  # Track completely finished cards
            return redirect(url_for('flashcards'))
    return render_template('index.html')

def display(x:str,y:str):
    print(x,type(x))
    print(y,type(y))

@app.route('/flashcards', methods=['GET', 'POST'])
def flashcards():
    if 'flashcards' not in session or not session['flashcards']:
        return redirect(url_for('index'))

    #print("Session Data:", session)  # Debug statement to inspect session data

    flashcards = session['flashcards']
    current_index = int(session.get('current_index', 0))  # Ensure current_index is an int
    
    # Convert repetitions keys back to integers
    repetitions = {}
    for key, value in session.get('repetitions', {}).items():
        repetitions[int(key)] = {'count': int(value['count']), 'correct': value['correct']}
    
    # Convert completed list to integers
    completed = [int(x) for x in session.get('completed', [])]

    #print(f"Session Data Before Processing: {session}")  # Debug session data

    if request.method == 'POST':
        user_answer = str(request.form.get('user_answer', '').strip())
        correct_answer = str(flashcards[current_index]['answer'].strip())
        display(user_answer.lower(), correct_answer.lower())
        is_correct = user_answer.lower() == correct_answer.lower()

        # Update repetition count
        if current_index not in repetitions:
            repetitions[current_index] = {'count': 0, 'correct': False}
        
        if is_correct:
            repetitions[current_index]['correct'] = True

        repetitions[current_index]['count'] = int(repetitions[current_index]['count']) + 1

        #print(f"Count after increment: {repetitions[current_index]['count']}")

        # Check if the card needs to be repeated more
        to_repeat = 2 if is_correct else 3
        
        # If we need more repetitions, keep the same card
        if repetitions[current_index]['count'] < to_repeat:
            # Save state and continue with the same card
            session['repetitions'] = {
                str(idx): {'count': int(data['count']), 'correct': data['correct']} 
                for idx, data in repetitions.items()
            }
            # Explicitly keep the same card by maintaining current_index
            session['current_index'] = current_index
            session['completed'] = [str(x) for x in completed]
            #print(f"Not enough repetitions yet. Keeping card {current_index}. Count: {repetitions[current_index]['count']}/{to_repeat}")
            return redirect(url_for('flashcards'))
        else:
            # Card is now fully completed
            completed.append(current_index)
            if current_index in repetitions:
                del repetitions[current_index]
            #print(f"Card {current_index} completed with {to_repeat} repetitions")

    # Randomize order of remaining cards
    remaining_indices = [i for i in range(len(flashcards)) if i not in completed]
    #print("Remaining indices:", remaining_indices)
    
    if not remaining_indices:
        session.clear()
        return "<h1>You've completed all flashcards!</h1>"

    # Choose a new card if we're not repeating the previous one
    next_index = random.choice(remaining_indices)
    session['current_index'] = next_index
    
    # Initialize repetition data for new card if needed
    if next_index not in repetitions:
        repetitions[next_index] = {'count': 0, 'correct': False}
    
    # Save state
    session['repetitions'] = {
        str(idx): {'count': int(data['count']), 'correct': data['correct']}
        for idx, data in repetitions.items()
    }
    session['completed'] = [str(x) for x in completed]
    
    #print(f"Next card: {next_index}, repetition count: {repetitions[next_index]['count']}")

    return render_template('flashcards.html', flashcard=flashcards[next_index])

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')