from flask import Flask, request, jsonify
import socket

# --- config ---
GUI_IP      = '127.0.0.1'
GUI_PORT    = 5100   # OpenBCI GUI marker UDP listener (porta fissa)
SERVER_PORT = 9000

app = Flask(__name__)

def send_udp(value: float):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(bytes([int(value) & 0xFF]), (GUI_IP, GUI_PORT))
    sock.close()

@app.after_request
def cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

@app.route('/marker', methods=['POST', 'OPTIONS'])
def marker():
    if request.method == 'OPTIONS':
        return jsonify({'ok': True})
    value = float(request.json.get('value', 1))
    send_udp(value)
    print(f'marker {value}')
    return jsonify({'ok': True})

@app.route('/ping')
def ping():
    return jsonify({'ok': True})

if __name__ == '__main__':
    print(f'sync_server → OpenBCI GUI {GUI_IP}:{GUI_PORT}')
    print(f'in ascolto su 0.0.0.0:{SERVER_PORT}')
    app.run(host='0.0.0.0', port=SERVER_PORT)
