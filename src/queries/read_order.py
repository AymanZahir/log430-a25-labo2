"""
Orders (read-only model)
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, Ayman Zahir 2025
"""

from db import get_sqlalchemy_session, get_redis_conn
from sqlalchemy import desc
from models.order import Order

def get_order_by_id(order_id):
    """Get order by ID from Redis"""
    r = get_redis_conn()
    return r.hgetall(order_id)

def get_orders_from_mysql(limit=9999):
    """Get last X orders"""
    session = get_sqlalchemy_session()
    return session.query(Order).order_by(desc(Order.id)).limit(limit).all()

def get_orders_from_redis(limit=9999):
    """Get last X orders"""
    r = get_redis_conn()

    ids = r.smembers("orders:all")
    if not ids:
        return []

    try:
        ordered_ids = sorted(ids, key=lambda x: int(x), reverse=True)
    except (TypeError, ValueError):
        ordered_ids = list(ids)

    results = []
    for oid in ordered_ids[:limit]:
        data = r.hgetall(f"order:{oid}")
        if not data:
            data = r.hgetall(str(oid))
        if data:
            results.append(data)

    return results


def get_highest_spending_users():
    """Get report of best selling products"""
    r = get_redis_conn()

    ids = r.smembers("orders:all")
    if not ids:
        return []

    count_by_user = {}
    spent_by_user = {}

    for oid in ids:
        data = r.hgetall(f"order:{oid}") or r.hgetall(str(oid))
        if not data:
            continue
        uid = data.get("user_id")
        if not uid:
            continue

        count_by_user[uid] = count_by_user.get(uid, 0) + 1

        try:
            total = float(data.get("total", 0) or 0)
        except (TypeError, ValueError):
            total = 0.0
        spent_by_user[uid] = spent_by_user.get(uid, 0.0) + total

    ranked = sorted(
        ((uid, count_by_user.get(uid, 0), spent_by_user.get(uid, 0.0)) for uid in count_by_user),
        key=lambda t: (t[1], t[2]),
        reverse=True,
    )
    return ranked
