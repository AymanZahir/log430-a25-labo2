"""
Report view
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, Ayman Zahir  2025
"""
from views.template_view import get_template, get_param
from db import get_sqlalchemy_session
from models.user import User
from queries.read_order import get_highest_spending_users as get_highest_spenders

def show_highest_spending_users():
    """ Show report of highest spending users """
    session = get_sqlalchemy_session()

    rows = get_highest_spenders() or []
    user_ids = [int(uid) for (uid, _, _) in rows] if rows else []

    name_by_id = {}
    if user_ids:
        users = session.query(User).filter(User.id.in_(user_ids)).all()
        for u in users:
            name = getattr(u, "name", None)
            if not name:
                first = getattr(u, "first_name", "") or getattr(u, "firstname", "")
                last  = getattr(u, "last_name", "")  or getattr(u, "lastname", "")
                name = f"{first} {last}".strip()
            name_by_id[u.id] = name or str(u.id)

    items_html = []
    for uid, order_count, total_spent in rows:
        display_name = name_by_id.get(int(uid), str(uid))
        try:
            total_val = float(total_spent)
        except (TypeError, ValueError):
            total_val = 0.0
        items_html.append(
            f"<li>{display_name} — {order_count} commandes — {total_val:.2f} $</li>"
        )

    body = (
        "<h2>Les plus gros acheteurs</h2>"
        "<ul>" + ("".join(items_html) if items_html else "<li>(aucune commande)</li>") + "</ul>"
    )
    return get_template(body)


def show_best_sellers():
    """ Show report of best selling products """
    return get_template("<h2>Les articles les plus vendus</h2><p>(TODO: Liste avec nom, total vendu)</p>")