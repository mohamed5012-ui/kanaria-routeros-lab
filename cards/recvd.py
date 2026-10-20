#!/usr/bin/env python3
"""Lab HTTPS receiver (CI only) for the cards report: logs every POST (path, token header, body). usage: recvd.py <cert> <key> <log>"""
import json, ssl, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
cert, key, logp = sys.argv[1:4]
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get('Content-Length') or 0))
        open(logp, 'a').write(json.dumps({'path': self.path, 'token': self.headers.get('X-Kanaria-Token', ''), 'ctype': self.headers.get('Content-Type', ''), 'body': raw.decode('utf-8', 'replace')}) + '\n')
        self.send_response(200); self.send_header('Content-Length', '2'); self.end_headers(); self.wfile.write(b'ok')
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(cert, key)
s = HTTPServer(('0.0.0.0', 8443), H); s.socket = ctx.wrap_socket(s.socket, server_side=True); s.serve_forever()
