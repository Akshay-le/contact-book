from flask import Flask, render_template, request, redirect, url_for, session
import json, os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

USERS_FILE = 'users.json'
CONTACTS_FILE = 'contacts.json'

def load_users():
    if not os.path.exists(USERS_FILE): return {}
    with open(USERS_FILE, 'r') as f:
        try: data = json.load(f)
        except: return {}
    if not isinstance(data, dict): return {}
    fixed, changed = {}, False
    for u, info in data.items():
        if isinstance(info, str):
            fixed[u] = {'password': info}
            changed = True
        elif isinstance(info, dict) and 'password' in info:
            fixed[u] = info
        else:
            changed = True
    if changed: save_users(fixed)
    return fixed

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def load_contacts():
    if not os.path.exists(CONTACTS_FILE): return {}
    with open(CONTACTS_FILE, 'r') as f:
        try: data = json.load(f)
        except: return {}
    return data if isinstance(data, dict) else {}

def save_contacts(data):
    with open(CONTACTS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    query = request.args.get('q', '').lower()
    contacts = load_contacts().get(username, [])
    if query:
        contacts = [c for c in contacts if query in c['first_name'].lower() or query in c['last_name'].lower()]
    return render_template('home.html', username=username, contacts=contacts, query=query)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users:
            return 'Username already exists!'
        users[username] = {'password': password}
        save_users(users)
        contacts = load_contacts()
        contacts[username] = []
        save_contacts(contacts)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users and users[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('home'))
        return 'Invalid credentials!'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
def add_contact():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    if request.method == 'POST':
        new_contact = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'phone': request.form['phone'],
            'email': request.form['email'],
            'address': request.form['address'],
            'linkedin': request.form['linkedin'],
            'category': request.form['category']
        }
        data = load_contacts()
        data[username].append(new_contact)
        save_contacts(data)
        return redirect(url_for('home'))
    return render_template('add_contact.html')

@app.route('/edit/<int:index>', methods=['GET', 'POST'])
def edit_contact(index):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    data = load_contacts()
    user_contacts = data.get(username, [])
    if index >= len(user_contacts):
        return 'Invalid contact index'
    if request.method == 'POST':
        user_contacts[index] = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'phone': request.form['phone'],
            'email': request.form['email'],
            'address': request.form['address'],
            'linkedin': request.form['linkedin'],
            'category': request.form['category']
        }
        data[username] = user_contacts
        save_contacts(data)
        return redirect(url_for('home'))
    return render_template('edit_contact.html', contact=user_contacts[index])

@app.route('/delete/<int:index>')
def delete_contact(index):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    data = load_contacts()
    if username in data and 0 <= index < len(data[username]):
        del data[username][index]
        save_contacts(data)
    return redirect(url_for('home'))

if __name__ == '__main__':
    # For production, ensure app is not in debug mode
    app.run(debug=False)
