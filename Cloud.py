from flask import Flask, request, redirect, url_for, render_template_string, send_from_directory, session
from werkzeug.utils import secure_filename
import sqlite3
import os 
app = Flask(__name__)
app.secret_key = 'your_secret_key'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploaded_files')
CODE_FOLDER = os.path.join(BASE_DIR, 'code_files')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CODE_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CODE_FOLDER'] = CODE_FOLDER

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'mp3', 'mp4', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect('users.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        conn.close()
        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid credentials'
    return render_template_string(login_template, error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = sqlite3.connect('users.db')
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            error = 'Username already exists'
    return render_template_string(signup_template, error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('dashboard'))

    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template_string(main_template, files=files, user=session['username'])

@app.route('/download', methods=['POST'])
def download_file():
    filename = request.form.get('filename')
    if filename:
        filename = secure_filename(filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(path):
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    return 'File not found', 404

@app.route('/delete', methods=['POST'])
def delete_file():
    filename = request.form.get('filename')
    if filename:
        filename = secure_filename(filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(path):
            os.remove(path)
    return redirect(url_for('dashboard'))

# Code Editor
@app.route('/codeeditor', methods=['GET', 'POST'])
def code_editor():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.form['action']
        filename = secure_filename(request.form['filename'])

        filepath = os.path.join(app.config['CODE_FOLDER'], filename)

        if action == 'save':
            content = request.form['content']
            with open(filepath, 'w') as f:
                f.write(content)
        elif action == 'delete' and os.path.exists(filepath):
            os.remove(filepath)

        return redirect(url_for('code_editor'))

    files = os.listdir(app.config['CODE_FOLDER'])
    selected_file = request.args.get('file')
    code_content = ''
    if selected_file:
        file_path = os.path.join(app.config['CODE_FOLDER'], secure_filename(selected_file))
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                code_content = f.read()

    return render_template_string(code_editor_template, files=files, content=code_content, selected_file=selected_file, user=session['username'])

# Templates
login_template = '''
<!DOCTYPE html>
<html>
<head>
  <title>Login</title>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css" rel="stylesheet">
</head>
<body class="container">
  <h3>Login</h3>
  <form method="POST">
    <input name="username" placeholder="Username" required>
    <input type="password" name="password" placeholder="Password" required>
    <button class="btn blue" type="submit">Login</button>
    <p class="red-text">{{ error }}</p>
  </form>
  <p>Don't have an account? <a href="/signup">Sign Up</a></p>
</body>
</html>
'''

signup_template = '''
<!DOCTYPE html>
<html>
<head>
  <title>Sign Up</title>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css" rel="stylesheet">
</head>
<body class="container">
  <h3>Sign Up</h3>
  <form method="POST">
    <input name="username" placeholder="Username" required>
    <input type="password" name="password" placeholder="Password" required>
    <button class="btn green" type="submit">Sign Up</button>
    <p class="red-text">{{ error }}</p>
  </form>
  <p>Already have an account? <a href="/login">Login</a></p>
</body>
</html>
'''

main_template = '''
<!DOCTYPE html>
<html>
<head>
  <title>Drive</title>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css" rel="stylesheet">
</head>
<body>
<nav>
  <div class="nav-wrapper blue">
    <a href="/" class="brand-logo" style="padding-left:10px;">clouders</a>
    <ul class="right ">
      <li><a href="/dashboard" class="white-text">Home</a></li>
      <li><a href="/codeeditor" class="white-text">Code Editor</a></li>
      <li><a href="/logout" class="white-text">Logout ({{ user }})</a></li>
    </ul>
  </div>
</nav>

<div class="container">
  <h4>Upload File</h4>
  <form method="post" enctype="multipart/form-data">
    <input type="file" name="file" required>
    <button type="submit" class="btn">Upload</button>
  </form>
  <h5>Files</h5>
  <ul class="collection">
    {% for file in files %}
      <li class="collection-item">
        {{ file }}
        <form action="/download" method="post" style="display:inline;">
          <input type="hidden" name="filename" value="{{ file }}">
          <button class="btn-small blue" type="submit">Download</button>
        </form>
        <form action="/delete" method="post" style="display:inline;">
          <input type="hidden" name="filename" value="{{ file }}">
          <button class="btn-small red" type="submit">Delete</button>
        </form>
      </li>
    {% endfor %}
  </ul>
</div>

<footer class="page-footer blue">
  <div class="container">
    <div class="center-align white-text"> clouders &copy; 2025</div>
  </div>
</footer>
</body>
</html>
'''

code_editor_template = '''
<!DOCTYPE html>
<html>
<head>
  <title>Code Editor</title>
  <link href="https://cdnjs.cloudflare.com/ajax/libs/materialize/1.0.0/css/materialize.min.css" rel="stylesheet">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/codemirror.min.css" rel="stylesheet">
</head>
<body>
<nav>
  <div class="nav-wrapper blue">
    <a href="/" class="brand-logo" style="padding-left:10px;">clouders</a>
    <ul class="right hide-on-med-and-down">
      <li><a href="/dashboard" class="white-text">Home</a></li>
      <li><a href="/codeeditor" class="white-text">Code Editor</a></li>
      <li><a href="/logout" class="white-text">Logout ({{ user }})</a></li>
    </ul>
  </div>
</nav>

<div class="container">
  <h4>Code Editor</h4>
  <form method="POST">
    <input name="filename" placeholder="Filename" required value="{{ selected_file or '' }}">
    <textarea id="code" name="content">{{ content }}</textarea>
    <input type="hidden" name="action" value="save">
    <button type="submit" class="btn green">Save</button>
  </form>

  <h5>Saved Files</h5>
  <ul class="collection">
    {% for file in files %}
      <li class="collection-item">
        <a href="/codeeditor?file={{ file }}">{{ file }}</a>
        <form method="POST" style="display:inline;">
          <input type="hidden" name="filename" value="{{ file }}">
          <input type="hidden" name="action" value="delete">
          <button class="btn-small red" type="submit">Delete</button>
        </form>
      </li>
    {% endfor %}
  </ul>
</div>

<footer class="page-footer blue">
  <div class="container center-align white-text">
    Code Editor &copy; 2025
  </div>
</footer>

<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/codemirror.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/javascript/javascript.min.js"></script>
<script>
  var editor = CodeMirror.fromTextArea(document.getElementById("code"), {
    lineNumbers: true,
    mode: "javascript"
  });
</script>
</body>
</html>
'''

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

