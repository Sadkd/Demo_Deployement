from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_migrate import Migrate
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import func


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todolist.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app,db)

# initilize Flask-login
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirects to login if the user isn't logged in

# Initialize Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
mail = Mail(app)

# resset password token generator
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

def generate_token(user_id):
    return serializer.dumps(user_id, salt='password-reset-salt')

def verify_token(token, expiration=3600):
    try:
        user_id = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
    except:
        return None
    return User.query.get(user_id)


# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    tasks = db.relationship('Task', backref='user', lazy=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)  # Added

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

# Task model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Message model
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    is_review = db.Column(db.Boolean, default=False)
    user = db.relationship('User', backref='messages')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home route - Welcome page
@app.route('/')
def home():
    messages = Message.query.filter_by(is_review=True).all()
    return render_template('home.html', messages=messages)

# Dashboard route - Displays user's tasks
@app.route('/dashboard')
@login_required
def index():
    sort_by = request.args.get('sort', 'date')  # Default sort by date
    search_query = request.args.get('search', '')  # Get search query

    # Base query
    tasks_query = Task.query.filter_by(user_id=current_user.id)

    # Apply search filter
    if search_query:
        tasks_query = tasks_query.filter(Task.content.ilike(f'%{search_query}%'))

    # Apply sorting
    if sort_by == 'name':
        tasks = tasks_query.order_by(Task.content).all()
    elif sort_by == 'complete':
        tasks = tasks_query.order_by(Task.completed).all()
    elif sort_by == 'priority':
        # Sort by deadline (ascending), then by name (ascending)
        tasks = tasks_query.order_by(
            Task.deadline.asc().nulls_last(),  # Tasks without deadlines come last
            Task.content.asc()
        ).all()
    else:
        tasks = tasks_query.order_by(Task.date_created).all()

    return render_template('index.html', tasks=tasks)

# Add new task route
@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        task_content = request.form['content']
        deadline_str = request.form['deadline']

        # Convert deadline string to datetime object (if provided)
        deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M') if deadline_str else None

        # Create new task
        new_task = Task(content=task_content, user_id=current_user.id, deadline=deadline)
        db.session.add(new_task)
        db.session.commit()
        flash('Task added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_task.html')

# Set time limit for a task
@app.route('/set_time_limit/<int:id>', methods=['POST'])
@login_required
def set_time_limit(id):
    task = Task.query.get_or_404(id)
    if task.user_id == current_user.id:
        task.deadline = datetime.strptime(request.form['time_limit'], '%Y-%m-%dT%H:%M')
        db.session.commit()
        flash('Time limit set successfully!', 'success')
    return redirect(url_for('index'))

# Delete task route
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    task_to_delete = Task.query.get_or_404(id)
    if task_to_delete.user_id == current_user.id:
        db.session.delete(task_to_delete)
        db.session.commit()
        flash('Task deleted successfully!', 'success')
    return redirect(url_for('index'))

# Complete task route
@app.route('/complete/<int:id>')
@login_required
def complete(id):
    task = Task.query.get_or_404(id)
    if task.user_id == current_user.id:
        task.completed = not task.completed
        db.session.commit()
        flash('Task status updated!', 'success')
    return redirect(url_for('index'))

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('register'))

        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)  # Hash the password
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('login_register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):  # Verify the password
            login_user(user)
            return redirect(url_for('index'))  # Redirect to dashboard

        flash('Invalid username or password', 'danger')
        return render_template('login_register.html')

    return render_template('login_register.html')


# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Edit task route
@app.route('/edit_task/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        flash('You do not have permission to edit this task.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        task.content = request.form['content']
        deadline_str = request.form['deadline']

        # Convert deadline string to datetime object (if provided)
        task.deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M') if deadline_str else None

        db.session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('edit_task.html', task=task)


# admin route
@app.route('/admin', methods=['GET'])
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('index'))
    
    # User search functionality
    search_query = request.args.get('search', '')
    if search_query:
        users = User.query.filter(User.username.ilike(f"%{search_query}%")).all()
    else:
        users = User.query.all()
    
    # Performance metrics
    total_users = User.query.count()
    tasks_today = Task.query.filter(Task.date_created >= datetime.utcnow().date()).count()
    new_users_today = User.query.filter(func.date(User.date_created) == datetime.utcnow().date()).count()

    # Analytics data
    # User Growth (last 7 days)
    user_growth_data = []
    user_growth_labels = []
    for i in range(6, -1, -1):
        date = datetime.utcnow().date() - timedelta(days=i)
        count = User.query.filter(func.date(User.date_created) == date).count()
        user_growth_data.append(count)
        user_growth_labels.append(date.strftime('%Y-%m-%d'))

    # Task Completion Rate
    completed_tasks = Task.query.filter_by(completed=True).count()
    total_tasks = Task.query.count()
    task_completion_data = [completed_tasks, total_tasks - completed_tasks]

    # Active Users (Last 7 Days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    active_users_count = User.query.filter(User.id.in_(db.session.query(Task.user_id).filter(Task.date_created >= seven_days_ago))).count()

    # Average Tasks per User
    avg_tasks_per_user = db.session.query(func.avg(db.session.query(func.count(Task.id)).group_by(Task.user_id).as_scalar())).scalar() or 0
    avg_tasks_per_user = round(float(avg_tasks_per_user), 2)

    # Fetch messages for the admin dashboard
    messages = Message.query.order_by(Message.date_created.desc()).all()

    return render_template('admin_dashboard.html', 
                           users=users, 
                           total_users=total_users,
                           tasks_today=tasks_today, 
                           new_users_today=new_users_today,
                           user_growth_data=user_growth_data, 
                           user_growth_labels=user_growth_labels,
                           task_completion_data=task_completion_data,
                           active_users_count=active_users_count,
                           avg_tasks_per_user=avg_tasks_per_user,
                           messages=messages)

# Deleting users and tasks
@app.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('You cannot delete an admin user.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    # Delete the user and their tasks
    Task.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/delete_task/<int:task_id>')
@login_required
def delete_task(task_id):
    if not current_user.is_admin:
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('index'))
    
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash(f'Task "{task.content}" deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

# route for message submission
@app.route('/send_message', methods=['GET', 'POST'])
@login_required
def send_message():
    if request.method == 'POST':
        content = request.form.get('content')
        if not content:
            flash('Message content cannot be empty!', 'danger')
            return redirect(url_for('send_message'))
        
        # Debug logging
        app.logger.debug(f"User ID: {current_user.id}, Message Content: {content}")
        
        # Add the message to the database
        new_message = Message(content=content, user_id=current_user.id, is_review=False)
        db.session.add(new_message)
        db.session.commit()
        flash('Message sent successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('send_message.html')


# route for admin handling messages
@app.route('/post_review/<int:message_id>')
@login_required
def post_review(message_id):
    if not current_user.is_admin:
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('index'))

    message = Message.query.get_or_404(message_id)
    message.is_review = True
    db.session.commit()
    flash('Message posted as a review!', 'success')
    return redirect(url_for('admin_dashboard'))

# route for deleting msg
@app.route('/delete_message/<int:message_id>')
@login_required
def delete_message(message_id):
    if not current_user.is_admin:
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('index'))
    
    message = Message.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash('Message deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# route for admin to submit reviews
@app.route('/admin_write_review', methods=['POST'])
@login_required
def admin_write_review():
    if not current_user.is_admin:
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('index'))

    # Get the message_id from the form or request data
    message_id = request.form.get('message_id')
    
    # Fetch the original message and get the sender's user_id
    original_message = Message.query.get(message_id)
    
    if not original_message:
        flash('Message not found.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    # Create the review using the original message's user_id
    content = request.form['content']
    new_review = Message(content=content, user_id=original_message.user_id, is_review=True)
    
    db.session.add(new_review)
    db.session.commit()
    flash('Review posted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# route to forgot password
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate a token
            token = generate_token(user.id)
            # Send email with the token
            msg = Message(
                "Password Reset Request",  # Subject (positional argument)
                sender="your-email@example.com",  # Sender email
                recipients=[email]  # Recipient email(s)
            )
            msg.body = f'''To reset your password, visit the following link:
{url_for('reset_password', token=token, _external=True)}

If you did not make this request, simply ignore this email.
'''
            mail.send(msg)
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('login'))
        else:
            flash('Email address not found.', 'danger')
    return render_template('forgot_password.html')

# route to resset password
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = verify_token(token)
    if not user:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('reset_password', token=token))
        user.set_password(password)
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)