"""
Orders (read-only model)
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, Ayman Zahir 2025
"""

from db import get_sqlalchemy_session, get_redis_conn
from sqlalchemy import desc
from models.order import Order
from typing import List, Tuple

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

def get_best_selling_products(limit: int = 10) -> List[Tuple[str, int]]:
    """
    Retourne [(product_id, total_vendu)] trié décroissant.
    Lit les compteurs Redis: product:{id}
    """
    r = get_redis_conn()

    ids = r.smembers("products:all")
    keys = [f"product:{pid}" for pid in ids] if ids else r.keys("product:*")
    if not keys:
        return []

    pipe = r.pipeline()
    for k in keys:
        pipe.get(k)
    counts = pipe.execute()

    rows = []
    for k, c in zip(keys, counts):
        pid = k.split("product:", 1)[1]
        try:
            rows.append((pid, int(c or 0)))
        except (TypeError, ValueError):
            rows.append((pid, 0))

    rows.sort(key=lambda t: t[1], reverse=True)
    return rows[:limit]
