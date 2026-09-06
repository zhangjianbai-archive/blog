"""Local preview matching GitHub Pages /blog/ URLs: python preview.py."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

DIRECTORY = Path(__file__).resolve().parent / "docs"

class PreviewHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if urlsplit(self.path).path in ("/", "/blog"):
            self.send_response(302)
            self.send_header("Location", "/blog/")
            self.end_headers()
            return
        super().do_GET()

    def translate_path(self, path):
        # Keep the request path intact for directory redirects; map the mount only.
        if urlsplit(path).path.startswith("/blog/"):
            path = path[len("/blog"):]
        return super().translate_path(path)

if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8765), partial(PreviewHandler, directory=str(DIRECTORY)))
    print("Local preview: http://localhost:8765/blog/", flush=True)
    server.serve_forever()
