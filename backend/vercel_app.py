from http.server import BaseHTTPRequestHandler
from main import app
import json

class VercelHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'ok'}).encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # Process the request using your FastAPI app
        response = app.post('/api/endpoint', data=post_data)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(response.body)

def handler(request):
    if request.method == 'GET':
        return {'status': 'ok'}
    elif request.method == 'POST':
        return app(request) 
