from flask import Flask, render_template, request, redirect, url_for, session
import json, os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

USERS_FILE = 'users.json'
CONTACTS_FILE = 'contacts.json'

class Storage:
    def __init__(self, path):
        self.path = path

    def load(self):
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def save(self, data):
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=4)

class UserManager:
    def __init__(self, storage):
        self.store = storage
        self.users = self.load()

    def load(self):
        users = self.store.load()
        return {u: {'password': p} if isinstance(p, str) else p for u, p in users.items()}

    def save(self):
        self.store.save(self.users)

    def register(self, username, password):
        if username in self.users:
            return False
        self.users[username] = {'password': password}
        self.save()
        return True

    def auth(self, username, password):
        return username in self.users and self.users[username]['password'] == password

class ContactManager:
    def __init__(self, storage):
        self.store = storage
        self.data = self.store.load()

    def save(self):
        self.store.save(self.data)

    def list(self, user):
        return self.data.get(user, [])

    def add(self, user, contact):
        self.data.setdefault(user, []).append(contact)
        self.save()

    def update(self, user, index, contact):
        self.data[user][index] = contact
        self.save()

    def delete(self, user, index):
        del self.data[user][index]
        self.save()

users = UserManager(Storage(USERS_FILE))
contacts = ContactManager(Storage(CONTACTS_FILE))

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    query = request.args.get('q', '').lower()
    contact_list = contacts.list(username)
    if query:
        contact_list = [c for c in contact_list if query in c['first_name'].lower() or query in c['last_name'].lower()]
    contact_list.sort(key=lambda c: c['first_name'].lower())
    return render_template('home.html', username=username, contacts=contact_list, query=query)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not users.register(username, password):
            return 'Username already exists!'
        contacts.data[username] = []
        contacts.save()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if users.auth(username, password):
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
    if request.method == 'POST':
        contact = {k: request.form[k] for k in ['first_name', 'last_name', 'phone', 'email', 'address', 'linkedin', 'category']}
        contacts.add(session['username'], contact)
        return redirect(url_for('home'))
    return render_template('add_contact.html')

@app.route('/edit/<int:index>', methods=['GET', 'POST'])
def edit_contact(index):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    contact_list = contacts.list(username)
    if index >= len(contact_list):
        return 'Invalid contact index'
    if request.method == 'POST':
        contact = {k: request.form[k] for k in ['first_name', 'last_name', 'phone', 'email', 'address', 'linkedin', 'category']}
        contacts.update(username, index, contact)
        return redirect(url_for('home'))
    return render_template('edit_contact.html', contact=contact_list[index], index=index)

@app.route('/delete/<int:index>')
def delete_contact(index):
    if 'username' not in session:
        return redirect(url_for('login'))
    contacts.delete(session['username'], index)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
