from flask import Flask, render_template, request, redirect, url_for, session
import json, os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

USERS_FILE, CONTACTS_FILE = 'users.json', 'contacts.json'

class Storage:
    def __init__(self, path):
        self.path = path

    def load(self):
        if not os.path.exists(self.path):
            return {}
        try:
            return json.load(open(self.path))
        except:
            return {}

    def save(self, data):
        json.dump(data, open(self.path, 'w'), indent=4)

class UserManager:
    def __init__(self, storage):
        self.store = storage
        self.users = self.load()

    def load(self):
        users = self.store.load()
        return {u: {'password': p} if isinstance(p, str) else p for u, p in users.items()}

    def save(self):
        self.store.save(self.users)

    def register(self, u, p):
        if u in self.users:
            return False
        self.users[u] = {'password': p}
        self.save()
        return True

    def auth(self, u, p):
        return u in self.users and self.users[u]['password'] == p

class ContactManager:
    def __init__(self, storage):
        self.store = storage
        self.data = self.store.load()

    def save(self):
        self.store.save(self.data)

    def list(self, user):
        return self.data.get(user, [])

    def add(self, user, c):
        self.data.setdefault(user, []).append(c)
        self.save()

    def update(self, user, i, c):
        self.data[user][i] = c
        self.save()

    def delete(self, user, i):
        del self.data[user][i]
        self.save()

users = UserManager(Storage(USERS_FILE))
contacts = ContactManager(Storage(CONTACTS_FILE))

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    u = session['username']
    q = request.args.get('q', '').lower()
    cs = contacts.list(u)
    if q:
        cs = [c for c in cs if q in c['first_name'].lower() or q in c['last_name'].lower()]
    # Sort alphabetically by first name
    cs.sort(key=lambda c: c['first_name'].lower())
    return render_template('home.html', username=u, contacts=cs, query=q)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        if not users.register(u, p):
            return 'Username exists!'
        contacts.data[u] = []
        contacts.save()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        if users.auth(u, p):
            session['username'] = u
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
        c = {k: request.form[k] for k in ['first_name', 'last_name', 'phone', 'email', 'address', 'linkedin', 'category']}
        contacts.add(session['username'], c)
        return redirect(url_for('home'))
    return render_template('add_contact.html')

@app.route('/edit/<int:index>', methods=['GET', 'POST'])
def edit_contact(index):
    if 'username' not in session:
        return redirect(url_for('login'))
    u = session['username']
    cs = contacts.list(u)
    if index >= len(cs):
        return 'Invalid contact index'
    if request.method == 'POST':
        c = {k: request.form[k] for k in ['first_name', 'last_name', 'phone', 'email', 'address', 'linkedin', 'category']}
        contacts.update(u, index, c)
        return redirect(url_for('home'))
    return render_template('edit_contact.html', contact=cs[index])

@app.route('/delete/<int:index>')
def delete_contact(index):
    if 'username' not in session:
        return redirect(url_for('login'))
    contacts.delete(session['username'], index)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=False)
