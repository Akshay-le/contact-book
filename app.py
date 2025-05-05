from flask import Flask, render_template, request, redirect, url_for, session
import json, os, shutil

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change to your secret key
USERS_FILE = 'users.json'
USER_DATA_DIR = 'user_data'
DEFAULT_TEMPLATE = 'default_user_data/contacts.json'

# Ensure the user_data directory exists
if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

class Storage:
    def __init__(self, path): 
        self.path = path
        
    def load(self): 
        if not os.path.exists(self.path): return {}
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
        if u in self.users: return False
        self.users[u] = {'password': p}
        self.save()
        return True
    
    def auth(self, u, p): 
        return u in self.users and self.users[u]['password'] == p

class ContactManager:
    def __init__(self, path): 
        self.path = path
        
    def load(self): 
        if not os.path.exists(self.path): return []
        return json.load(open(self.path))
    
    def save(self, data): 
        json.dump(data, open(self.path, 'w'), indent=4)
    
    def list(self): 
        return self.load()
    
    def add(self, c): 
        cs = self.load()
        cs.append(c)
        self.save(cs)
    
    def update(self, i, c): 
        cs = self.load()
        cs[i] = c
        self.save(cs)
    
    def delete(self, i): 
        cs = self.load()
        del cs[i]
        self.save(cs)

users = UserManager(Storage(USERS_FILE))

@app.route('/')
def home():
    if 'username' not in session: 
        return redirect(url_for('login'))
    
    username = session['username']
    cm = ContactManager(get_user_contact_path(username))
    q = request.args.get('q', '').lower()
    contacts = [c for c in cm.list() if q in c['first_name'].lower() or q in c['last_name'].lower()] if q else cm.list()
    return render_template('home.html', username=username, contacts=contacts, query=q)

def get_user_contact_path(username):
    user_dir = os.path.join(USER_DATA_DIR, username)
    contact_file = os.path.join(user_dir, 'contacts.json')
    
    # Create the user's directory and copy the default template if the directory does not exist
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
        shutil.copy(DEFAULT_TEMPLATE, contact_file)
    
    return contact_file

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        if not users.register(u, p): 
            return 'Username exists!'
        get_user_contact_path(u)  # Create user's directory and copy default contacts
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        if users.auth(u, p):
            session['username'] = u
            get_user_contact_path(u)  # Ensure the user's directory exists
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
    
    cm = ContactManager(get_user_contact_path(session['username']))
    
    if request.method == 'POST':
        c = {k: request.form[k] for k in ['first_name', 'last_name', 'phone', 'email', 'address', 'linkedin', 'category']}
        cm.add(c)
        return redirect(url_for('home'))
    
    return render_template('add_contact.html')

@app.route('/edit/<int:index>', methods=['GET', 'POST'])
def edit_contact(index):
    if 'username' not in session: 
        return redirect(url_for('login'))
    
    cm = ContactManager(get_user_contact_path(session['username']))
    contacts = cm.list()
    if index >= len(contacts): 
        return 'Invalid contact index'
    
    if request.method == 'POST':
        c = {k: request.form[k] for k in ['first_name', 'last_name', 'phone', 'email', 'address', 'linkedin', 'category']}
        cm.update(index, c)
        return redirect(url_for('home'))
    
    return render_template('edit_contact.html', contact=contacts[index])

@app.route('/delete/<int:index>')
def delete_contact(index):
    if 'username' not in session: 
        return redirect(url_for('login'))
    
    cm = ContactManager(get_user_contact_path(session['username']))
    cm.delete(index)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
