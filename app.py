from flask import Flask, render_template, request, redirect, url_for, session
import os, json

app = Flask(__name__)
app.secret_key = 'your_secret_key'

USERS_FILE = 'users.json'
CONTACTS_FILE = 'contacts.json'

class UserManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.users = self.load_users()

    def load_users(self):
        if not os.path.exists(self.file_path):
            return {}
        with open(self.file_path, 'r') as f:
            try:
                data = json.load(f)
            except:
                return {}
        if not isinstance(data, dict):
            return {}

        fixed, changed = {}, False
        for u, info in data.items():
            if isinstance(info, str):
                fixed[u] = {'password': info}
                changed = True
            elif isinstance(info, dict) and 'password' in info:
                fixed[u] = info
            else:
                changed = True
        if changed:
            self.save_users(fixed)
        return fixed

    def save_users(self, users=None):
        if users:
            self.users = users
        with open(self.file_path, 'w') as f:
            json.dump(self.users, f, indent=4)

    def register_user(self, username, password):
        if username in self.users:
            return False
        self.users[username] = {'password': password}
        self.save_users()
        return True

    def authenticate(self, username, password):
        return username in self.users and self.users[username]['password'] == password

class Contact:
    def __init__(self, first_name, last_name, phone, email, address, linkedin, category):
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.email = email
        self.address = address
        self.linkedin = linkedin
        self.category = category

    def to_dict(self):
        return self.__dict__

class ContactManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.contacts = self.load_contacts()

    def load_contacts(self):
        if not os.path.exists(self.file_path):
            return {}
        with open(self.file_path, 'r') as f:
            try:
                data = json.load(f)
            except:
                return {}
        return data if isinstance(data, dict) else {}

    def save_contacts(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.contacts, f, indent=4)

    def get_contacts(self, username):
        return self.contacts.get(username, [])

    def add_contact(self, username, contact: Contact):
        self.contacts.setdefault(username, []).append(contact.to_dict())
        self.save_contacts()

    def update_contact(self, username, index, contact: Contact):
        if username in self.contacts and 0 <= index < len(self.contacts[username]):
            self.contacts[username][index] = contact.to_dict()
            self.save_contacts()

    def delete_contact(self, username, index):
        if username in self.contacts and 0 <= index < len(self.contacts[username]):
            del self.contacts[username][index]
            self.save_contacts()

# Initialize managers
user_manager = UserManager(USERS_FILE)
contact_manager = ContactManager(CONTACTS_FILE)

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    query = request.args.get('q', '').lower()
    contacts = contact_manager.get_contacts(username)
    if query:
        contacts = [c for c in contacts if query in c['first_name'].lower() or query in c['last_name'].lower()]
    return render_template('home.html', username=username, contacts=contacts, query=query)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not user_manager.register_user(username, password):
            return 'Username already exists!'
        contact_manager.contacts[username] = []
        contact_manager.save_contacts()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if user_manager.authenticate(username, password):
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
        contact = Contact(
            request.form['first_name'],
            request.form['last_name'],
            request.form['phone'],
            request.form['email'],
            request.form['address'],
            request.form['linkedin'],
            request.form['category']
        )
        contact_manager.add_contact(username, contact)
        return redirect(url_for('home'))
    return render_template('add_contact.html')

@app.route('/edit/<int:index>', methods=['GET', 'POST'])
def edit_contact(index):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    contacts = contact_manager.get_contacts(username)
    if index >= len(contacts):
        return 'Invalid contact index'
    if request.method == 'POST':
        updated_contact = Contact(
            request.form['first_name'],
            request.form['last_name'],
            request.form['phone'],
            request.form['email'],
            request.form['address'],
            request.form['linkedin'],
            request.form['category']
        )
        contact_manager.update_contact(username, index, updated_contact)
        return redirect(url_for('home'))
    return render_template('edit_contact.html', contact=contacts[index])

@app.route('/delete/<int:index>')
def delete_contact(index):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    contact_manager.delete_contact(username, index)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=False)
