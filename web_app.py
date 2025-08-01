"""Serveur Web pour consulter et enrichir la bibliothèque."""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import html
import xml.etree.ElementTree as ET
from main import load_library, save_library

STYLE = """
body {font-family: Arial, sans-serif; margin:2em; background:#f5f5f5;}
header {background:#333; color:#fff; padding:1em; text-align:center;}
nav a {color:white; margin:0 1em; text-decoration:none;}
main {background:white; padding:1em; border-radius:4px;}
table {width:100%; border-collapse:collapse; margin-bottom:1em;}
th, td {border:1px solid #ccc; padding:8px; text-align:left;}
th {background:#eee;}
"""


def page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang='fr'>
<head>
    <meta charset='utf-8'>
    <title>{html.escape(title)}</title>
    <style>{STYLE}</style>
</head>
<body>
<header>
    <h1>Bibliothèque</h1>
    <nav>
        <a href='/'>Accueil</a>
        <a href='/books'>Livres</a>
        <a href='/add-book'>Ajouter</a>
    </nav>
</header>
<main>
{body}
</main>
</body>
</html>"""


def list_books_html() -> str:
    tree = load_library()
    rows = []
    for book in tree.getroot().findall("books/book"):
        row = (
            f"<tr><td>{html.escape(book.get('id'))}</td>"
            f"<td>{html.escape(book.findtext('title'))}</td>"
            f"<td>{html.escape(book.findtext('author'))}</td></tr>"
        )
        rows.append(row)
    table = "<table><tr><th>ID</th><th>Titre</th><th>Auteur</th></tr>" + "".join(rows) + "</table>"
    return table


def add_book_params(params):
    required = {"title", "author", "genre", "year"}
    if not required.issubset(params.keys()):
        return False
    tree = load_library()
    books = tree.getroot().find("books")
    ids = [int(b.get("id")) for b in books.findall("book")]
    next_id = max(ids, default=0) + 1
    book = ET.SubElement(books, "book", id=str(next_id))
    ET.SubElement(book, "title").text = params["title"][0]
    ET.SubElement(book, "author").text = params["author"][0]
    ET.SubElement(book, "genre").text = params["genre"][0]
    ET.SubElement(book, "year").text = params["year"][0]
    save_library(tree)
    return True


class LibraryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            body = "<p>Bienvenue dans la bibliothèque.</p>"
            html_page = page("Accueil", body)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_page.encode("utf-8"))
        elif parsed.path == "/books":
            table = list_books_html()
            html_page = page("Liste des livres", table)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_page.encode("utf-8"))
        elif parsed.path == "/add-book":
            params = parse_qs(parsed.query)
            if params:
                added = add_book_params(params)
                message = "Livre ajouté." if added else "Paramètres manquants." 
                body = f"<p>{message}</p>"
                html_page = page("Ajout d'un livre", body)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html_page.encode("utf-8"))
            else:
                form = (
                    "<form>"
                    "<label>Titre: <input name='title'></label><br>"
                    "<label>Auteur: <input name='author'></label><br>"
                    "<label>Genre: <input name='genre'></label><br>"
                    "<label>Année: <input name='year'></label><br>"
                    "<input type='submit' value='Ajouter'>"
                    "</form>"
                )
                html_page = page("Ajouter un livre", form)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html_page.encode("utf-8"))
        else:
            self.send_error(404)


def run(server_class=HTTPServer, handler_class=LibraryHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Serveur demarre sur le port {port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
