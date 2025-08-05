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
        <a href='/add-book'>Ajouter livre</a>
        <a href='/users'>Utilisateurs</a>
        <a href='/add-user'>Ajouter utilisateur</a>
        <a href='/loans'>Prêts</a>
        <a href='/loan-book'>Emprunter</a>
        <a href='/return-book'>Retour</a>
        <a href='/extend-loan'>Prolonger</a>
        <a href='/search-books'>Recherche</a>
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


def list_users_html() -> str:
    tree = load_library()
    rows = []
    for user in tree.getroot().findall("users/user"):
        row = (
            f"<tr><td>{html.escape(user.get('id'))}</td>"
            f"<td>{html.escape(user.findtext('name'))}</td></tr>"
        )
        rows.append(row)
    table = "<table><tr><th>ID</th><th>Nom</th></tr>" + "".join(rows) + "</table>"
    return table


def add_user_params(params):
    if "name" not in params:
        return False
    tree = load_library()
    users = tree.getroot().find("users")
    ids = [int(u.get("id")) for u in users.findall("user")]
    next_id = max(ids, default=0) + 1
    user = ET.SubElement(users, "user", id=str(next_id))
    ET.SubElement(user, "name").text = params["name"][0]
    save_library(tree)
    return True


def update_book_params(params):
    if "id" not in params:
        return False
    tree = load_library()
    book = tree.getroot().find(f"books/book[@id='{params['id'][0]}']")
    if book is None:
        return False
    if "title" in params:
        book.find("title").text = params["title"][0]
    if "author" in params:
        book.find("author").text = params["author"][0]
    if "genre" in params:
        book.find("genre").text = params["genre"][0]
    if "year" in params:
        book.find("year").text = params["year"][0]
    save_library(tree)
    return True


def delete_book_params(params):
    if "id" not in params:
        return False
    tree = load_library()
    books = tree.getroot().find("books")
    book = books.find(f"book[@id='{params['id'][0]}']")
    if book is None:
        return False
    books.remove(book)
    save_library(tree)
    return True


def update_user_params(params):
    if "id" not in params or "name" not in params:
        return False
    tree = load_library()
    user = tree.getroot().find(f"users/user[@id='{params['id'][0]}']")
    if user is None:
        return False
    user.find("name").text = params["name"][0]
    save_library(tree)
    return True


def delete_user_params(params):
    if "id" not in params:
        return False
    tree = load_library()
    users = tree.getroot().find("users")
    user = users.find(f"user[@id='{params['id'][0]}']")
    if user is None:
        return False
    users.remove(user)
    save_library(tree)
    return True


def list_loans_html() -> str:
    tree = load_library()
    rows = []
    for loan in tree.getroot().findall("loans/loan"):
        status = "retourne" if loan.get("returned") == "true" else "en cours"
        row = (
            f"<tr><td>{html.escape(loan.get('book_id'))}</td>"
            f"<td>{html.escape(loan.get('user_id'))}</td>"
            f"<td>{html.escape(loan.get('date_out'))}</td>"
            f"<td>{html.escape(loan.get('date_due'))}</td>"
            f"<td>{status}</td></tr>"
        )
        rows.append(row)
    table = (
        "<table><tr><th>Livre</th><th>Utilisateur</th><th>Sortie</th>"
        "<th>Retour prévu</th><th>Statut</th></tr>" + "".join(rows) + "</table>"
    )
    return table


def loan_book_params(params):
    required = {"book_id", "user_id"}
    if not required.issubset(params.keys()):
        return False, "Paramètres manquants."
    tree = load_library()
    root = tree.getroot()
    book_id = params["book_id"][0]
    user_id = params["user_id"][0]

    book = root.find(f"books/book[@id='{book_id}']")
    if book is None:
        book = root.find(f"books/book[title='{book_id}']")
    user = root.find(f"users/user[@id='{user_id}']")
    if user is None:
        user = root.find(f"users/user[name='{user_id}']")
    if book is None:
        return False, "Livre introuvable."
    if user is None:
        return False, "Utilisateur introuvable."
    loans = root.find("loans")
    existing = loans.find(
        f"loan[@book_id='{book.get('id')}'][@returned='false']"
    )
    if existing is not None:
        return False, "Livre déjà emprunté."
    import datetime

    date_out = params.get("date_out", [datetime.date.today().isoformat()])[0]
    date_due = params.get(
        "date_due",
        [(datetime.date.today() + datetime.timedelta(days=30)).isoformat()],
    )[0]
    ET.SubElement(
        loans,
        "loan",
        book_id=book.get("id"),
        user_id=user.get("id"),
        date_out=date_out,
        date_due=date_due,
        returned="false",
    )
    save_library(tree)
    return True, "Prêt enregistré."


def _resolve_book_id(root: ET.Element, identifier: str) -> str | None:
    """Retourne l'identifiant du livre selon son id ou son titre."""
    book = root.find(f"books/book[@id='{identifier}']")
    if book is None:
        book = root.find(f"books/book[title='{identifier}']")
    return book.get("id") if book is not None else None


def return_book_params(params):
    if "book_id" not in params:
        return False
    tree = load_library()
    root = tree.getroot()
    book_id = _resolve_book_id(root, params["book_id"][0])
    if book_id is None:
        return False
    loans = root.find("loans")
    loan = loans.find(
        f"loan[@book_id='{book_id}'][@returned='false']"
    )
    if loan is None:
        return False
    import datetime

    loan.set(
        "date_return",
        params.get("date_return", [datetime.date.today().isoformat()])[0],
    )
    loan.set("returned", "true")
    save_library(tree)
    return True


def extend_loan_params(params):
    if "book_id" not in params or "new_date" not in params:
        return False
    tree = load_library()
    root = tree.getroot()
    book_id = _resolve_book_id(root, params["book_id"][0])
    if book_id is None:
        return False
    loans = root.find("loans")
    loan = loans.find(
        f"loan[@book_id='{book_id}'][@returned='false']"
    )
    if loan is None:
        return False
    loan.set("date_due", params["new_date"][0])
    save_library(tree)
    return True


def search_books_html(params) -> str:
    tree = load_library()
    rows = []
    for book in tree.getroot().findall("books/book"):
        if "author" in params and params["author"][0].lower() not in book.findtext("author").lower():
            continue
        if "genre" in params and params["genre"][0].lower() not in book.findtext("genre").lower():
            continue
        if "year" in params and params["year"][0] != book.findtext("year"):
            continue
        row = (
            f"<tr><td>{html.escape(book.get('id'))}</td>"
            f"<td>{html.escape(book.findtext('title'))}</td>"
            f"<td>{html.escape(book.findtext('author'))}</td></tr>"
        )
        rows.append(row)
    if rows:
        table = "<table><tr><th>ID</th><th>Titre</th><th>Auteur</th></tr>" + "".join(rows) + "</table>"
    else:
        table = "<p>Aucun résultat.</p>"
    return table


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
        elif parsed.path == "/search-books":
            params = parse_qs(parsed.query)
            if params:
                table = search_books_html(params)
            else:
                form = (
                    "<form>"
                    "<label>Auteur: <input name='author'></label><br>"
                    "<label>Genre: <input name='genre'></label><br>"
                    "<label>Année: <input name='year'></label><br>"
                    "<input type='submit' value='Rechercher'>"
                    "</form>"
                )
                table = form
            html_page = page("Recherche de livres", table)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_page.encode("utf-8"))
        elif parsed.path == "/update-book":
            params = parse_qs(parsed.query)
            if params:
                updated = update_book_params(params)
                message = "Livre modifié." if updated else "Paramètres manquants."
                body = f"<p>{message}</p>"
            else:
                body = (
                    "<form>"
                    "<label>ID: <input name='id'></label><br>"
                    "<label>Titre: <input name='title'></label><br>"
                    "<label>Auteur: <input name='author'></label><br>"
                    "<label>Genre: <input name='genre'></label><br>"
                    "<label>Année: <input name='year'></label><br>"
                    "<input type='submit' value='Mettre à jour'>"
                    "</form>"
                )
            html_page = page("Modification d'un livre", body)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_page.encode("utf-8"))
        elif parsed.path == "/delete-book":
            params = parse_qs(parsed.query)
            deleted = delete_book_params(params)
            body = "<p>Livre supprimé.</p>" if deleted else "<p>Suppression impossible.</p>"
            html_page = page("Suppression d'un livre", body)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_page.encode("utf-8"))
        elif parsed.path == "/users":
            table = list_users_html()
            html_page = page("Liste des utilisateurs", table)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_page.encode("utf-8"))
        elif parsed.path == "/add-user":
            params = parse_qs(parsed.query)
            if params:
                added = add_user_params(params)
                message = "Utilisateur ajouté." if added else "Paramètres manquants."
                body = f"<p>{message}</p>"
            else:
                body = (
                    "<form>"
                    "<label>Nom: <input name='name'></label><br>"
                    "<input type='submit' value='Ajouter'>"
                    "</form>"
                )
            html_page = page("Ajout d'un utilisateur", body)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_page.encode("utf-8"))
        elif parsed.path == "/update-user":
            params = parse_qs(parsed.query)
            if params:
                updated = update_user_params(params)
                message = "Utilisateur modifié." if updated else "Paramètres manquants."
                body = f"<p>{message}</p>"
            else:
                body = (
                    "<form>"
                    "<label>ID: <input name='id'></label><br>"
                    "<label>Nom: <input name='name'></label><br>"
                    "<input type='submit' value='Mettre à jour'>"
                    "</form>"
                )
            html_page = page("Modification d'un utilisateur", body)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_page.encode("utf-8"))
        elif parsed.path == "/delete-user":
            params = parse_qs(parsed.query)
            deleted = delete_user_params(params)
            body = (
                "<p>Utilisateur supprimé.</p>" if deleted else "<p>Suppression impossible.</p>"
            )
            html_page = page("Suppression d'un utilisateur", body)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_page.encode("utf-8"))
        elif parsed.path == "/loans":
            table = list_loans_html()
            html_page = page("Liste des prêts", table)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_page.encode("utf-8"))
        elif parsed.path == "/loan-book":
            params = parse_qs(parsed.query)
            if params:
                done, message = loan_book_params(params)
                body = f"<p>{html.escape(message)}</p>"
            else:
                tree = load_library()
                root = tree.getroot()
                book_opts = "".join(
                    f"<option value='{b.get('id')}'>{html.escape(b.findtext('title'))}</option>"
                    for b in root.findall("books/book")
                )
                user_opts = "".join(
                    f"<option value='{u.get('id')}'>{html.escape(u.findtext('name'))}</option>"
                    for u in root.findall("users/user")
                )
                body = (
                    "<form>"
                    f"<label>Livre: <select name='book_id'>{book_opts}</select></label><br>"
                    f"<label>Utilisateur: <select name='user_id'>{user_opts}</select></label><br>"
                    "<label>Date sortie: <input name='date_out'></label><br>"
                    "<label>Date retour prévue: <input name='date_due'></label><br>"
                    "<input type='submit' value='Enregistrer'>"
                    "</form>"
                )
            html_page = page("Enregistrer un prêt", body)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_page.encode("utf-8"))
        elif parsed.path == "/return-book":
            params = parse_qs(parsed.query)
            if params:
                done = return_book_params(params)
                body = "<p>Livre rendu.</p>" if done else "<p>Opération impossible.</p>"
            else:
                tree = load_library()
                root = tree.getroot()
                loan_opts = "".join(
                    f"<option value='{l.get('book_id')}'>{html.escape(root.find("books/book[@id='%s']" % l.get('book_id')).findtext('title'))}</option>"
                    for l in root.findall("loans/loan[@returned='false']")
                )
                body = (
                    "<form>"
                    f"<label>Livre: <select name='book_id'>{loan_opts}</select></label><br>"
                    "<label>Date de retour: <input name='date_return'></label><br>"
                    "<input type='submit' value='Rendre'>"
                    "</form>"
                )
            html_page = page("Retour d'un livre", body)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_page.encode("utf-8"))
        elif parsed.path == "/extend-loan":
            params = parse_qs(parsed.query)
            if params:
                done = extend_loan_params(params)
                body = (
                    "<p>Prêt prolongé.</p>" if done else "<p>Opération impossible.</p>"
                )
            else:
                tree = load_library()
                root = tree.getroot()
                loan_opts = "".join(
                    f"<option value='{l.get('book_id')}'>{html.escape(root.find("books/book[@id='%s']" % l.get('book_id')).findtext('title'))}</option>"
                    for l in root.findall("loans/loan[@returned='false']")
                )
                body = (
                    "<form>"
                    f"<label>Livre: <select name='book_id'>{loan_opts}</select></label><br>"
                    "<label>Nouvelle date: <input name='new_date'></label><br>"
                    "<input type='submit' value='Prolonger'>"
                    "</form>"
                )
            html_page = page("Prolonger un prêt", body)
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
