import mimetypes
from pathlib import Path
import json
import logging
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from datetime import datetime
from threading import Thread

BASE_DIR = Path()
BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST = "0.0.0.0"
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 4000

users_data = {}

class SimpleFramework(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if BASE_DIR.joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        size = self.headers.get('Content-Length')
        data = self.rfile.read(int(size))
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST,SOCKET_PORT))
        client_socket.close()
        self.send_response(302)
        self.send_header('location', '/message')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

def save_data_form(data):
    parse_data = urllib.parse.unquote_plus(data.decode())
    msg_time = datetime.now()
    try:
        parse_dict = {key: value for key, value in [el.split('=', 1) for el in parse_data.split('&', 1)]}
        users_data[str(msg_time)] = parse_dict
        with open('storage/data.json', 'w+', encoding='utf-8') as file:
            json.dump(users_data, file, ensure_ascii=False, indent=4)
    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging.error(err)

def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    logging.info("soket server started")
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            logging.info(f"Socket received {address}: {msg}")
            save_data_form(msg)
    except KeyboardInterrupt:
        server_socket.close()

def run_http_server(host, port):
    server_address = (host, port)
    http_server = HTTPServer(server_address, SimpleFramework)
    logging.info("http server started")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

    server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    server.start()

    server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()