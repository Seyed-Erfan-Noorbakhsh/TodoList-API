from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mssql+pyodbc://@localhost/todo_db?'
    'trusted_connection=yes&'
    'driver=ODBC+Driver+17+for+SQL+Server'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key'

# Extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Models
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Schemas
class TaskSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(validate=validate.Length(max=200))
    completed = fields.Bool()
    created_at = fields.DateTime(dump_only=True)

# Dummy user data
users = {"admin": "123456"}

# Routes
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    if users.get(username) == password:
        token = create_access_token(identity=username)
        return jsonify(access_token=token), 200
    return jsonify({"msg": "Bad credentials"}), 401

@app.route('/tasks', methods=['POST'])
@jwt_required()
def add_task():
    schema = TaskSchema()
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify(err.messages), 400
    task = Task(**data)
    db.session.add(task)
    db.session.commit()
    return schema.dump(task), 201

@app.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 5))
    sort_by = request.args.get('sort_by', 'created_at')
    sort_dir = request.args.get('sort_dir', 'desc')
    status = request.args.get('completed')

    query = Task.query
    if status in ['true', 'false']:
        query = query.filter_by(completed=(status == 'true'))
    if sort_by in ['created_at', 'title']:
        column = getattr(Task, sort_by)
        column = column.desc() if sort_dir == 'desc' else column.asc()
        query = query.order_by(column)

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    schema = TaskSchema(many=True)
    return jsonify({
        "tasks": schema.dump(paginated.items),
        "total": paginated.total,
        "pages": paginated.pages,
        "current_page": paginated.page
    })

@app.route('/tasks/<int:id>', methods=['GET'])
@jwt_required()
def get_task(id):
    task = Task.query.get_or_404(id)
    return TaskSchema().dump(task), 200

@app.route('/tasks/<int:id>', methods=['PUT'])
@jwt_required()
def update_task(id):
    task = Task.query.get_or_404(id)
    schema = TaskSchema(partial=True)
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify(err.messages), 400
    for key, value in data.items():
        setattr(task, key, value)
    db.session.commit()
    return schema.dump(task), 200

@app.route('/tasks/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_task(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted successfully"}), 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
