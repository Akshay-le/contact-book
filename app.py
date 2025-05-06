from flask import Flask, render_template, request, redirect, url_for, session
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
from shutil import copytree

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# File paths
USERS_FILE = 'users.json'
USER_DATA_DIR = 'user_data'
DEFAULT_DATA_DIR = 'default_user_data'

# Ensure users.json exists
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)

# Ensure default directory exists
if not os.path.exists(DEFAULT_DATA_DIR):
    os.makedirs(DEFAULT_DATA_DIR)
    with open(os.path.join(DEFAULT_DATA_DIR, 'contacts.json'), 'w') as f:
        json.dump([], f)

# ---------- CLASSES ----------

class User:
    @staticmethod
    def register(username, password):
        users = User.load_users()
        if username in users:
            return False
        users[username] = generate_password_hash(password)
        User.save_users(users)
        User.create_user_data(username)
        return True

    @staticmethod
    def login(username, password):
        users = User.load_users()
        if username in users and check_password_hash(users[username], password):
            return True
        return False

    @staticmethod
    def load_users():
        with open(USERS_FILE, 'r') as f:
            return json.load(f)

    @staticmethod
    def save_users(users):
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)

    @staticmethod
    def create_user_data(username):
        user_dir = os.path.join(USER_DATA_DIR, username)
        if not os.path.exists(user_dir):
            copytree(DEFAULT_DATA_DIR, user_dir)

class Contact:
    def __init__(self, username):
        self.user_file = os.path.join(USER_DATA_DIR, username, 'contacts.json')
        if not os.path.exists(self.user_file):
            with open(self.user_file, 'w') as f:
                json.dump([], f)

    def load(self):
        with open(self.user_file, 'r') as f:
            return json.load(f)

    def save(self, contacts):
        with open(self.user_file, 'w') as f:
            json.dump(contacts, f)

    def list(self):
        return self.load()

    def add(self, contact):
        contacts = self.load()
        contacts.append(contact)
        self.save(contacts)

    def update(self, index, contact):
        contacts = self.load()
        contacts[index] = contact
        self.save(contacts)

    def delete(self, index):
        contacts = self.load()
        if 0 <= index < len(contacts):
            contacts.pop(index)
            self.save(contacts)

# ---------- ROUTES ----------

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    u = session['username']
    contacts = Contact(u)
    q = request.args.get('q', '').lower()

    contact_list = contacts.list()
    if q:
        contact_list = [c for c in contact_list if q in c['first_name'].lower() or q in c['last_name'].lower()]
    
    # Sort alphabetically by first name, then last name
    cs = sorted(contact_list, key=lambda c: (c['first_name'].lower(), c['last_name'].lower()))
    return render_template('home.html', contacts=cs, username=u)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        if User.login(u, p):
            session['username'] = u
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        if User.register(u, p):
            session['username'] = u
            return redirect(url_for('home'))
        else:
            return render_template('register.html', error='Username already exists')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'username' not in session:
        return redirect(url_for('login'))
    u = session['username']
    contacts = Contact(u)
    if request.method == 'POST':
        contact = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'phone': request.form['phone'],
            'email': request.form['email'],
            'address': request.form['address'],
            'linkedin': request.form['linkedin'],
            'category': request.form['category']
        }
        contacts.add(contact)
        return redirect(url_for('home'))
    return render_template('add.html')

@app.route('/edit/<int:index>', methods=['GET', 'POST'])
def edit(index):
    if 'username' not in session:
        return redirect(url_for('login'))
    u = session['username']
    contacts = Contact(u)
    contact_list = contacts.list()
    if request.method == 'POST':
        updated = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'phone': request.form['phone'],
            'email': request.form['email'],
            'address': request.form['address'],
            'linkedin': request.form['linkedin'],
            'category': request.form['category']
        }
        contacts.update(index, updated)
        return redirect(url_for('home'))
    return render_template('edit.html', contact=contact_list[index], index=index)

@app.route('/delete/<int:index>')
def delete(index):
    if 'username' not in session:
        return redirect(url_for('login'))
    u = session['username']
    contacts = Contact(u)
    contacts.delete(index)
    return redirect(url_for('home'))

# ---------- MAIN ----------

if __name__ == '__main__':
    app.run(debug=True)
