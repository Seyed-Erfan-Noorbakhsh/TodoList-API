from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
app = Flask(__name__)

# Database configuration - SQL Server
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mssql+pyodbc://@localhost/todo_db?'
    'trusted_connection=yes&'
    'driver=ODBC+Driver+17+for+SQL+Server'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Task Model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))

    def __repr__(self):
        return f'<Task {self.title}>'

# Create tables (run once)
with app.app_context():
    db.create_all()

# API Endpoints
@app.route('/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks"""
    tasks = Task.query.all()
    task_list = [{
        "id": task.id,
        "title": task.title,
        "description": task.description
    } for task in tasks]
    return jsonify(task_list), 200

@app.route('/tasks', methods=['POST'])
def add_task():
    """Add a new task"""
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({"error": "Title is required"}), 400
    
    new_task = Task(
        title=data['title'],
        description=data.get('description', '')
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({
        "id": new_task.id,
        "title": new_task.title,
        "description": new_task.description
    }), 201

@app.route('/tasks/<int:id>', methods=['GET'])
def get_task(id):
    """Get a specific task"""
    task = Task.query.get_or_404(id)
    return jsonify({
        "id": task.id,
        "title": task.title,
        "description": task.description
    }), 200

@app.route('/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    """Update a task"""
    task = Task.query.get_or_404(id)
    data = request.get_json()
    
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    
    db.session.commit()
    return jsonify({
        "id": task.id,
        "title": task.title,
        "description": task.description
    }), 200

@app.route('/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    """Delete a task"""
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)


with app.app_context():
    db.create_all()  # این خط باید فقط یک بار اجرا شود