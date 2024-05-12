from waitress import serve
from app import app 
import socket
 # Make sure to import your Flask app correctly

# Set Flask app debugging features. Note: This does not affect Waitress behavior.
app.debug = True  # This enables Flask's debug mode, not Waitress

if __name__ == '__main__':
    host_ip = socket.gethostbyname(socket.gethostname())
    serve(app, host=host_ip, port=8080)