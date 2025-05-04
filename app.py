from flask import Flask, render_template, request, redirect, url_for, session
import json, os

app = Flask(__name__)
app.secret_key = 'key'
USER_FILE, CONTACT_FILE = 'users.json', 'contacts.json'

class DB:
    def __init__(self, file): self.f = file
    def read(self): return json.load(open(self.f)) if os.path.exists(self.f) else {}
    def write(self, d): json.dump(d, open(self.f, 'w'), indent=4)

class Users:
    def __init__(self, db): self.db, self.data = db, self.load()
    def load(self): return {u: {'password': p} if isinstance(p, str) else p for u, p in self.db.read().items()}
    def save(self): self.db.write(self.data)
    def add(self, u, p): 
        if u in self.data: return False
        self.data[u] = {'password': p}; self.save(); return True
    def check(self, u, p): return u in self.data and self.data[u]['password'] == p

class Contacts:
    def __init__(self, db): self.db, self.data = db, db.read()
    def save(self): self.db.write(self.data)
    def all(self, u): return self.data.get(u, [])
    def add(self, u, c): self.data.setdefault(u, []).append(c); self.save()
    def edit(self, u, i, c): self.data[u][i] = c; self.save()
    def delete(self, u, i): del self.data[u][i]; self.save()

users = Users(DB(USER_FILE))
contacts = Contacts(DB(CONTACT_FILE))

@app.route('/')
def index():
    if 'user' not in session: return redirect('/login')
    u, q = session['user'], request.args.get('q', '').lower()
    cs = contacts.all(u)
    if q: cs = [c for c in cs if q in c['first_name'].lower() or q in c['last_name'].lower()]
    return render_template('home.html', username=u, contacts=cs, query=q)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        if not users.add(u, p): return 'User exists'
        contacts.data[u] = []; contacts.save()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        if users.check(u, p): session['user'] = u; return redirect('/')
        return 'Invalid login'
    return render_template('login.html')

@app.route('/logout')
def logout(): session.pop('user', None); return redirect('/login')

@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'user' not in session: return redirect('/login')
    if request.method == 'POST':
        f = ['first_name', 'last_name', 'phone', 'email', 'address', 'linkedin', 'category']
        c = {k: request.form[k] for k in f}
        contacts.add(session['user'], c)
        return redirect('/')
    return render_template('add_contact.html')

@app.route('/edit/<int:i>', methods=['GET', 'POST'])
def edit(i):
    if 'user' not in session: return redirect('/login')
    u, cs = session['user'], contacts.all(session['user'])
    if i >= len(cs): return 'Invalid index'
    if request.method == 'POST':
        f = ['first_name', 'last_name', 'phone', 'email', 'address', 'linkedin', 'category']
        contacts.edit(u, i, {k: request.form[k] for k in f})
        return redirect('/')
    return render_template('edit_contact.html', contact=cs[i])

@app.route('/delete/<int:i>')
def delete(i):
    if 'user' not in session: return redirect('/login')
    contacts.delete(session['user'], i)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=False)
