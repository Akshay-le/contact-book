from flask import Flask, render_template, request, redirect, url_for, session
import json, os

app = Flask(__name__)
app.secret_key = 'secret-key'
USER_DATA = 'users.json'
CONTACT_DATA = 'contacts.json'

# General file storage handler
class JSONHandler:
    def __init__(self, filename):
        self.filename = filename

    def read(self):
        if not os.path.exists(self.filename):
            return {}
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except:
            return {}

    def write(self, content):
        with open(self.filename, 'w') as f:
            json.dump(content, f, indent=4)

# User account manager
class AccountService:
    def __init__(self, db):
        self.db = db
        self.users = self._load()

    def _load(self):
        data = self.db.read()
        return {u: {'password': p} if isinstance(p, str) else p for u, p in data.items()}

    def save(self):
        self.db.write(self.users)

    def add_user(self, username, password):
        if username in self.users:
            return False
        self.users[username] = {'password': password}
        self.save()
        return True

    def verify(self, username, password):
        return username in self.users and self.users[username]['password'] == password

# Contact list manager
class ContactService:
    def __init__(self, db):
        self.db = db
        self.records = self.db.read()

    def save(self):
        self.db.write(self.records)

    def get_all(self, username):
        return self.records.get(username, [])

    def create(self, username, contact):
        self.records.setdefault(username, []).append(contact)
        self.save()

    def modify(self, username, idx, contact):
        self.records[username][idx] = contact
        self.save()

    def remove(self, username, idx):
        del self.records[username][idx]
        self.save()

# Initialize services
users = AccountService(JSONHandler(USER_DATA))
contacts = ContactService(JSONHandler(CONTACT_DATA))

# Routes
@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    username = session['user']
    query = request.args.get('q', '').lower()
    contact_list = contacts.get_all(username)
    if query:
        contact_list = [c for c in contact_list if query in c['first_name'].lower() or query in c['last_name'].lower()]
    return render_template('home.html', username=username, contacts=contact_list, query=query)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not users.add_user(username, password):
            return 'Username already taken'
        contacts.records[username] = []
        contacts.save()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        if users.verify(uname, pwd):
            session['user'] = uname
            return redirect(url_for('index'))
        return 'Incorrect username or password'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        fields = ['first_name', 'last_name', 'phone', 'email', 'address', 'linkedin', 'category']
        new_entry = {f: request.form[f] for f in fields}
        contacts.create(session['user'], new_entry)
        return redirect(url_for('index'))
    return render_template('add_contact.html')

@app.route('/edit/<int:idx>', methods=['GET', 'POST'])
def edit(idx):
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']
    all_contacts = contacts.get_all(user)
    if idx >= len(all_contacts):
        return 'Contact not found'
    if request.method == 'POST':
        updated = {f: request.form[f] for f in ['first_name', 'last_name', 'phone', 'email', 'address', 'linkedin', 'category']}
        contacts.modify(user, idx, updated)
        return redirect(url_for('index'))
    return render_template('edit_contact.html', contact=all_contacts[idx])

@app.route('/delete/<int:idx>')
def delete(idx):
    if 'user' not in session:
        return redirect(url_for('login'))
    contacts.remove(session['user'], idx)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=False)
