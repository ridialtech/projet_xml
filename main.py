"""Gestionnaire de bibliothèque simple basé sur un fichier XML.

Ce module permet d'ajouter des livres, des utilisateurs et de suivre les prêts
grâce à une interface en ligne de commande.
"""

import argparse
import datetime
import xml.etree.ElementTree as ET
from pathlib import Path


LIBRARY_FILE = Path("library.xml")


def load_library() -> ET.ElementTree:
    """Charge le fichier XML de la bibliothèque en le créant si besoin."""
    if not LIBRARY_FILE.exists():
        root = ET.Element("library")
        ET.SubElement(root, "books")
        ET.SubElement(root, "users")
        ET.SubElement(root, "loans")
        tree = ET.ElementTree(root)
        tree.write(LIBRARY_FILE, encoding="utf-8", xml_declaration=True)
    return ET.parse(LIBRARY_FILE)


def save_library(tree: ET.ElementTree) -> None:
    """Enregistre l'arbre XML dans le fichier de bibliothèque."""
    
    tree.write(LIBRARY_FILE, encoding="utf-8", xml_declaration=True)


def add_book(args) -> None:
    """Ajoute un nouvel ouvrage à la bibliothèque."""
    tree = load_library()
    root = tree.getroot()
    books = root.find("books")
    # determine next id
    ids = [int(book.get("id")) for book in books.findall("book")]
    next_id = max(ids, default=0) + 1

    book = ET.SubElement(books, "book", id=str(next_id))
    ET.SubElement(book, "title").text = args.title
    ET.SubElement(book, "author").text = args.author
    ET.SubElement(book, "genre").text = args.genre
    ET.SubElement(book, "year").text = str(args.year)

    save_library(tree)
    print(f"Book added with id {next_id}")


def list_books(_args) -> None:
    """Affiche la liste de tous les livres."""

    tree = load_library()
    for book in tree.getroot().findall("books/book"):
        print(f"[{book.get('id')}] {book.findtext('title')} by {book.findtext('author')}")


def search_books(args) -> None:
    """Recherche des livres selon différents critères."""

    tree = load_library()
    for book in tree.getroot().findall("books/book"):
        if args.author and args.author.lower() not in book.findtext("author").lower():
            continue
        if args.genre and args.genre.lower() not in book.findtext("genre").lower():
            continue
        if args.year and str(args.year) != book.findtext("year"):
            continue
        print(f"[{book.get('id')}] {book.findtext('title')} by {book.findtext('author')}")


def add_user(args) -> None:
    """Ajoute un utilisateur à la bibliothèque."""

    tree = load_library()
    users = tree.getroot().find("users")
    ids = [int(u.get("id")) for u in users.findall("user")]
    next_id = max(ids, default=0) + 1
    user = ET.SubElement(users, "user", id=str(next_id))
    ET.SubElement(user, "name").text = args.name
    save_library(tree)
    print(f"User added with id {next_id}")


def loan_book(args) -> None:
    """Enregistre le prêt d'un livre à un utilisateur."""

    tree = load_library()
    root = tree.getroot()
    # verify book and user exist
    book = root.find(f"books/book[@id='{args.book_id}']")
    user = root.find(f"users/user[@id='{args.user_id}']")
    if book is None:
        print("Book not found")
        return
    if user is None:
        print("User not found")
        return
    loans = root.find("loans")
    existing = loans.find(f"loan[@book_id='{args.book_id}'][@returned='false']")
    if existing is not None:
        print("Book already on loan")
        return
    loan = ET.SubElement(loans, "loan", book_id=str(args.book_id), user_id=str(args.user_id))
    loan.set("date_out", args.date_out)
    loan.set("date_due", args.date_due)
    loan.set("returned", "false")
    save_library(tree)
    print("Loan recorded")


def return_book(args) -> None:
    """Note le retour d'un livre emprunté."""

    tree = load_library()
    loans = tree.getroot().find("loans")
    loan = loans.find(f"loan[@book_id='{args.book_id}'][@returned='false']")
    if loan is None:
        print("Loan not found")
        return
    loan.set("returned", "true")
    loan.set("date_return", args.date_return)
    save_library(tree)
    print("Book returned")


def list_loans(_args) -> None:
    """Affiche l'ensemble des prêts enregistrés."""
    tree = load_library()
    for loan in tree.getroot().findall("loans/loan"):
        status = "returned" if loan.get("returned") == "true" else "on loan"
        print(
            f"Book {loan.get('book_id')} to user {loan.get('user_id')} "
            f"from {loan.get('date_out')} to {loan.get('date_due')} - {status}"
        )


def serve(_args) -> None:
    """Lance le serveur web et ouvre la page dans un navigateur."""
    import webbrowser
    from web_app import run

    webbrowser.open("http://localhost:8000")
    run()


def build_parser() -> argparse.ArgumentParser:
    """Construit l'analyseur de ligne de commande."""
    parser = argparse.ArgumentParser(description="Gestionnaire de bibliothèque XML")

    sub = parser.add_subparsers(dest="command")

    badd = sub.add_parser("add-book", help="Add a new book")
    badd.add_argument("title")
    badd.add_argument("author")
    badd.add_argument("genre")
    badd.add_argument("year", type=int)
    badd.set_defaults(func=add_book)

    blist = sub.add_parser("list-books", help="List all books")
    blist.set_defaults(func=list_books)

    bsearch = sub.add_parser("search-books", help="Search books")
    bsearch.add_argument("--author")
    bsearch.add_argument("--genre")
    bsearch.add_argument("--year", type=int)
    bsearch.set_defaults(func=search_books)

    uadd = sub.add_parser("add-user", help="Add a new user")
    uadd.add_argument("name")
    uadd.set_defaults(func=add_user)

    loan = sub.add_parser("loan-book", help="Loan a book to a user")
    loan.add_argument("book_id")
    loan.add_argument("user_id")
    loan.add_argument(
        "date_out", default=datetime.date.today().isoformat(), nargs="?"
    )
    loan.add_argument(
        "date_due",
        default=(datetime.date.today() + datetime.timedelta(days=30)).isoformat(),
        nargs="?",
    )
    loan.set_defaults(func=loan_book)

    ret = sub.add_parser("return-book", help="Return a book")
    ret.add_argument("book_id")
    ret.add_argument(
        "date_return", default=datetime.date.today().isoformat(), nargs="?"
    )
    ret.set_defaults(func=return_book)

    llist = sub.add_parser("list-loans", help="List loans")
    llist.set_defaults(func=list_loans)

    srv = sub.add_parser("serve", help="Lance l'interface web")
    srv.set_defaults(func=serve)


    return parser


def main(argv=None) -> None:
    """Point d'entrée du programme."""

    parser = build_parser()
    args = parser.parse_args(argv)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
