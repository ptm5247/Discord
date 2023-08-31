from http.server import BaseHTTPRequestHandler, HTTPServer

class Server(BaseHTTPRequestHandler):
  
  def do_GET(self):
    self.send_response(200)
    self.end_headers()
    with open('.' + self.path, 'rb') as file:
      self.wfile.write(file.read())

  def do_POST(self):
    self.send_response(200)
    self.end_headers()
    self.wfile.write(b'Button Clicked!')

if __name__ == '__main__':        
  server = HTTPServer(('localhost', 8080), Server)

  try:
    server.serve_forever()
  except KeyboardInterrupt:
    pass

  server.server_close()
