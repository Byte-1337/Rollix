
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import sqlite3, random, os

app = Flask(__name__)
app.secret_key = 'demo_secret_key'
DB = 'database.db'

def init_db():
    if not os.path.exists(DB):
        with sqlite3.connect(DB) as conn:
            conn.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    balance INTEGER DEFAULT 1000
                )
            ''')
init_db()

def get_user(username):
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cur.fetchone()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect(DB) as conn:
        balance = conn.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],)).fetchone()[0]
    return render_template('index.html', balance=balance)

@app.route('/flip', methods=['POST'])
def flip():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    bet = int(request.form['bet'])
    choice = request.form['choice']
    result = random.choice(['heads', 'tails'])
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        balance = cur.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],)).fetchone()[0]
        if bet > balance:
            return redirect(url_for('index'))
        if choice == result:
            balance += bet
            message = f"You won! It was {result}."
        else:
            balance -= bet
            message = f"You lost! It was {result}."
        cur.execute("UPDATE users SET balance = ? WHERE id = ?", (balance, session['user_id']))
        conn.commit()
    return render_template('index.html', balance=balance, message=message, result=result)

@app.route('/mines')
def mines():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect(DB) as conn:
        balance = conn.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],)).fetchone()[0]
    return render_template('mines.html', balance=balance)

@app.route('/mines_start', methods=['POST'])
def mines_start():
    data = request.json
    mine_count = int(data['mines'])
    bet = int(data['bet'])
    size = 5
    total_cells = size * size

    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 403

    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        balance = cur.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],)).fetchone()[0]
        if bet > balance:
            return jsonify({"error": "Insufficient balance"}), 400
        balance -= bet
        cur.execute("UPDATE users SET balance = ? WHERE id = ?", (balance, session['user_id']))
        conn.commit()

    mines = random.sample(range(total_cells), mine_count)
    session['mines'] = mines
    session['revealed'] = []
    session['bet'] = bet
    session['mine_count'] = mine_count
    session['profit'] = 0

    return jsonify({"success": True, "balance": balance})

@app.route('/reveal_cell', methods=['POST'])
def reveal_cell():
    index = int(request.json['index'])
    if 'mines' not in session or 'revealed' not in session:
        return jsonify({"error": "Game not started"}), 400

    if index in session['revealed']:
        return jsonify({"error": "Cell already revealed"}), 400

    session['revealed'].append(index)

    if index in session['mines']:
        return jsonify({"mine": True, "mines": session['mines']})
    else:
        bet = session['bet']
        multiplier = 1 + (len(session['revealed']) * (session['mine_count'] / 25))
        profit = int(bet * multiplier) - bet
        session['profit'] = profit
        return jsonify({"safe": True, "profit": profit})

@app.route('/cashout')
def cashout():
    if 'user_id' not in session or 'profit' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect(DB) as conn:
        conn.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (session['bet'] + session['profit'], session['user_id']))
        conn.commit()
    mines = session['mines']
    session.pop('mines', None)
    session.pop('revealed', None)
    session.pop('bet', None)
    session.pop('mine_count', None)
    session.pop('profit', None)
    return jsonify({"success": True, "mines": mines})

@app.route('/reset')
def reset():
    if 'user_id' in session:
        with sqlite3.connect(DB) as conn:
            conn.execute("UPDATE users SET balance = 1000 WHERE id = ?", (session['user_id'],))
            conn.commit()
    return redirect(url_for('index'))

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        amount = int(request.form['amount'])
        with sqlite3.connect(DB) as conn:
            conn.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, session['user_id']))
            conn.commit()
        return redirect(url_for('index'))
    return render_template('deposit.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)
        if user and user[2] == password:
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            with sqlite3.connect(DB) as conn:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error="Username already exists")
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

