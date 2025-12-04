import os
import json
import time # Added missing import for time
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
# --- THIS IS THE MISSING LINE THAT CAUSED THE ERROR ---
from werkzeug.utils import secure_filename 

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
UPLOAD_FOLDER = 'static/uploads'
ADMIN_PASSWORD = "admin"

DB_FILES = {
    'modules': 'courses.json',
    'assignments': 'assignments.json',
    'projects': 'project.json',
    'exams': 'exam.json'
}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- HELPER FUNCTIONS ---
def load_json(filename):
    if not os.path.exists(filename): return []
    with open(filename, 'r') as f: return json.load(f)

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f, indent=4)

# --- ROUTES ---

@app.route('/')
def home():
    return send_from_directory('.', 'FULL COMPELETE CSBS PORTAL.html')

@app.route('/admin')
def admin_page(): return send_from_directory('.', 'admin.html')

# 1. GET DATA
@app.route('/api/<category>')
def get_data(category):
    if category in DB_FILES:
        return jsonify(load_json(DB_FILES[category]))
    return jsonify([])

# 2. ADD DATA (Assignments, Projects, Exams)
@app.route('/add', methods=['POST'])
def add_item():
    if request.form.get('password') != ADMIN_PASSWORD: return "Wrong Password!", 403
    category = request.form.get('category')
    
    if category not in DB_FILES: return "Invalid Category"

    data = load_json(DB_FILES[category])
    new_item = request.form.to_dict()
    
    # Add a simple ID
    new_item['id'] = str(int(time.time()))
    
    # Clean up
    new_item.pop('password', None)
    new_item.pop('category', None)

    data.append(new_item)
    save_json(DB_FILES[category], data)
    
    return f"<h1>Success! Added to {category}.</h1><br><a href='/admin'>Back</a>"

# 3. DELETE DATA
@app.route('/delete', methods=['POST'])
def delete_item():
    data_in = request.json
    if data_in.get('password') != ADMIN_PASSWORD: return jsonify({"error": "Wrong Password"}), 403
    
    category = data_in.get('category')
    item_id = data_in.get('id')
    
    if category not in DB_FILES: return jsonify({"error": "Invalid Category"}), 400
    
    data = load_json(DB_FILES[category])
    new_data = [item for item in data if str(item.get('id', '')) != str(item_id)]
    
    save_json(DB_FILES[category], new_data)
    return jsonify({"success": True})

# 4. UPLOAD FILE (Modules)
@app.route('/upload', methods=['POST'])
def upload_file():
    if request.form.get('password') != ADMIN_PASSWORD: return "Wrong Password!", 403

    subject_code = request.form.get('subject_code')
    topic_name = request.form.get('topic_name')
    file = request.files.get('file') # Safer way to get file

    if file and file.filename != '':
        # THIS IS WHERE IT WAS FAILING BEFORE
        filename = secure_filename(file.filename) 
        
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        data = load_json(DB_FILES['modules'])
        found = False
        for subject in data:
            if subject['code'] == subject_code:
                for topic in subject['topics']:
                    t_name = topic['name'] if isinstance(topic, dict) else topic
                    if t_name == topic_name:
                        # Convert string topic to object if needed
                        if isinstance(topic, str):
                            index = subject['topics'].index(topic)
                            subject['topics'][index] = {"name": topic, "url": ""}
                            topic = subject['topics'][index]
                        
                        topic['url'] = f"/static/uploads/{filename}"
                        found = True
                        break
            if found: break
        
        if found:
            save_json(DB_FILES['modules'], data)
            return "<h1>Success! File Linked.</h1><br><a href='/admin'>Back</a>"
            
    return "Error: Topic not found or no file selected."

# 5. SERVE FILES
@app.route('/static/uploads/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    print("Restarting Server...")
    app.run(debug=True, port=5000)