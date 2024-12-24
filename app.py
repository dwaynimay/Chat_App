from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
from cryptography.fernet import Fernet

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey!'
socketio = SocketIO(app)

# Generate encryption key
encryption_key = Fernet.generate_key()
cipher = Fernet(encryption_key)

connected_users = {}  # Store username and room mapping
registered_users = set()  # To track unique usernames
user_colors = {}  # Map usernames to specific colors

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    room = request.form.get('room')

    if username in registered_users:
        return jsonify({"success": False, "message": "Name has been used"})

    registered_users.add(username)

    # Assign a random color for the username
    import random
    colors = ["#FF5733", "#33FF57", "#3357FF", "#F333FF", "#FF33A1", "#33FFF6"]
    user_colors[username] = random.choice(colors)

    return jsonify({"success": True, "username": username, "room": room})

@app.route('/chat')
def chat():
    username = request.args.get('username')
    room = request.args.get('room')
    return render_template('chat.html', username=username, room=room)

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']

    # Check if user is already in the room to prevent duplicate messages
    if username in [user[0] for user in connected_users.values()]:
        return  # Exit if user is already in the room

    # Assign or retrieve the user's color
    if username not in user_colors:
        import random
        colors = ["#FF5733", "#33FF57", "#3357FF", "#F333FF", "#FF33A1", "#33FFF6"]
        user_colors[username] = random.choice(colors)

    join_room(room)
    connected_users[request.sid] = (username, room)

    # Emit color to the user
    emit('user_color', user_colors[username], to=request.sid)

    # Notify the room
    emit('message', {
        "username": username,
        "color": user_colors.get(username, "#000000"),
        "text": "has entered the room."
    }, to=room)



@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    emit('message', {
        "username": username,
        "color": user_colors.get(username, "#000000"),
        "text": f"has left the room."
    }, to=room)
    connected_users.pop(request.sid, None)
    registered_users.discard(username)
    user_colors.pop(username, None)

@socketio.on('disconnect')
def on_disconnect():
    user_info = connected_users.pop(request.sid, None)
    if user_info:
        username, room = user_info
        emit('message', {
            "username": username,
            "color": user_colors.get(username, "#000000"),
            "text": f"has left the room."
        }, to=room)
        registered_users.discard(username)
        user_colors.pop(username, None)

@socketio.on('send_message')
def handle_message(data):
    username = data['username']
    room = data['room']
    message = data['message']
    color = user_colors.get(username, "#000000")  # Default to black if no color assigned
    emit('message', {
        "username": username,
        "color": color,
        "text": message
    }, to=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
