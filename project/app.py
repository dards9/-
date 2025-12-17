from flask import Flask, render_template, request, redirect, session
import sqlite3
import hashlib

app = Flask(__name__, template_folder='template', static_folder='static.css')
app.secret_key = 'secret123'

DB_NAME = 'database.db'


def get_db():
    return sqlite3.connect(DB_NAME)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        url TEXT,
        comment TEXT,
        user_id INTEGER
    )
    """)

    db.commit()
    db.close()


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            db = get_db()
            cur = db.cursor()
            cur.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (request.form['username'], hash_password(request.form['password']))
            )
            db.commit()
            db.close()
            return redirect('/login')
        except:
            return "Пользователь уже существует"
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "SELECT id FROM users WHERE username=? AND password=?",
            (request.form['username'], hash_password(request.form['password']))
        )
        user = cur.fetchone()
        db.close()

        if user:
            session['user_id'] = user[0]
            return redirect('/')
        return "Неверный логин или пароль"
    return render_template('login.html')


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        cur.execute(
            "INSERT INTO links (title, url, comment, user_id) VALUES (?, ?, ?, ?)",
            (request.form['title'], request.form['url'],
             request.form['comment'], session['user_id'])
        )
        db.commit()

    cur.execute(
        "SELECT id, title, url, comment FROM links WHERE user_id=?",
        (session['user_id'],)
    )
    links = cur.fetchall()
    db.close()

    return render_template('index.html', links=links)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/delete/<int:link_id>')
def delete(link_id):
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cur = db.cursor()

    cur.execute("DELETE FROM links WHERE id=? AND user_id=?", (link_id, session['user_id']))
    db.commit()
    db.close()

    return redirect('/')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
