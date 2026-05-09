import json
import sqlite3
from typing import Any

from app.core.config import DB_PATH, ensure_directories


def get_connection():
    ensure_directories()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    ensure_directories()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        vector_id INTEGER PRIMARY KEY,
        item_id TEXT NOT NULL,
        item_type TEXT NOT NULL,
        vector_type TEXT,
        title TEXT NOT NULL,
        category TEXT,
        product_code TEXT,
        source TEXT,
        content TEXT,
        image_path TEXT,
        brand TEXT,
        part_group TEXT,
        metadata_json TEXT
    )
    """)

    for col in ["brand TEXT", "part_group TEXT", "vector_type TEXT"]:
        try:
            cur.execute(f"ALTER TABLE items ADD COLUMN {col}")
        except sqlite3.OperationalError:
            pass

    cur.execute("CREATE INDEX IF NOT EXISTS idx_items_item_id ON items(item_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_items_product_code ON items(product_code)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_items_category ON items(category)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_items_brand ON items(brand)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_items_part_group ON items(part_group)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_items_type ON items(item_type)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_items_vector_type ON items(vector_type)")

    conn.commit()
    conn.close()


def clear_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM items")
    conn.commit()
    conn.close()


def row_to_item(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None

    item = dict(row)
    item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
    return item


def insert_item(
    vector_id: int,
    item_id: str,
    item_type: str,
    vector_type: str,
    title: str,
    category: str | None,
    product_code: str | None,
    source: str | None,
    content: str | None,
    image_path: str | None,
    metadata: dict | None,
):
    metadata = metadata or {}

    brand = metadata.get("brand")
    part_group = metadata.get("part_group")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO items (
        vector_id,
        item_id,
        item_type,
        vector_type,
        title,
        category,
        product_code,
        source,
        content,
        image_path,
        brand,
        part_group,
        metadata_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        vector_id,
        item_id,
        item_type,
        vector_type,
        title,
        category,
        product_code,
        source,
        content,
        image_path,
        brand,
        part_group,
        json.dumps(metadata, ensure_ascii=False)
    ))

    conn.commit()
    conn.close()


def fetch_item_by_vector_id(vector_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM items WHERE vector_id = ?", (vector_id,))
    row = cur.fetchone()

    conn.close()
    return row_to_item(row)


def search_items_by_product_code(product_code: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM items
    WHERE UPPER(product_code) = UPPER(?)
    """, (product_code,))

    rows = cur.fetchall()
    conn.close()

    results = []

    for row in rows:
        item = row_to_item(row)
        item["score"] = 1.0
        item["match_type"] = "product_code_exact"
        results.append(item)

    return results


def search_items_by_filters(
    query_terms: list[str] | None = None,
    only_images: bool = False,
    brand: str | None = None,
    part_keywords: list[str] | None = None,
    limit: int = 20,
):
    query_terms = query_terms or []
    part_keywords = part_keywords or []

    conn = get_connection()
    cur = conn.cursor()

    where = []
    params = []

    if only_images:
        where.append("item_type = 'image'")

    if brand:
        where.append("UPPER(brand) = UPPER(?)")
        params.append(brand)

    if part_keywords:
        part_conditions = []

        for kw in part_keywords:
            like = f"%{kw}%"

            part_conditions.append("""
            (
                LOWER(title) LIKE LOWER(?)
                OR LOWER(category) LIKE LOWER(?)
                OR LOWER(product_code) LIKE LOWER(?)
                OR LOWER(content) LIKE LOWER(?)
                OR LOWER(part_group) LIKE LOWER(?)
                OR LOWER(metadata_json) LIKE LOWER(?)
            )
            """)

            params.extend([like, like, like, like, like, like])

        where.append("(" + " OR ".join(part_conditions) + ")")

    if query_terms:
        term_conditions = []

        for term in query_terms:
            like = f"%{term}%"

            term_conditions.append("""
            (
                LOWER(title) LIKE LOWER(?)
                OR LOWER(category) LIKE LOWER(?)
                OR LOWER(product_code) LIKE LOWER(?)
                OR LOWER(source) LIKE LOWER(?)
                OR LOWER(content) LIKE LOWER(?)
                OR LOWER(brand) LIKE LOWER(?)
                OR LOWER(part_group) LIKE LOWER(?)
                OR LOWER(metadata_json) LIKE LOWER(?)
            )
            """)

            params.extend([like, like, like, like, like, like, like, like])

        where.append("(" + " OR ".join(term_conditions) + ")")

    sql = "SELECT * FROM items"

    if where:
        sql += " WHERE " + " AND ".join(where)

    sql += " LIMIT ?"
    params.append(limit)

    cur.execute(sql, params)
    rows = cur.fetchall()

    conn.close()

    results = []

    for row in rows:
        item = row_to_item(row)
        item["score"] = 0.95
        item["match_type"] = "metadata_filter"
        results.append(item)

    return results


def search_items_by_metadata_like(
    query: str,
    only_images: bool = False,
    limit: int = 10,
):
    conn = get_connection()
    cur = conn.cursor()

    like_query = f"%{query}%"

    if only_images:
        cur.execute("""
        SELECT *
        FROM items
        WHERE item_type = 'image'
          AND (
              title LIKE ?
              OR category LIKE ?
              OR product_code LIKE ?
              OR source LIKE ?
              OR content LIKE ?
              OR brand LIKE ?
              OR part_group LIKE ?
              OR metadata_json LIKE ?
          )
        LIMIT ?
        """, (
            like_query,
            like_query,
            like_query,
            like_query,
            like_query,
            like_query,
            like_query,
            like_query,
            limit,
        ))
    else:
        cur.execute("""
        SELECT *
        FROM items
        WHERE title LIKE ?
           OR category LIKE ?
           OR product_code LIKE ?
           OR source LIKE ?
           OR content LIKE ?
           OR brand LIKE ?
           OR part_group LIKE ?
           OR metadata_json LIKE ?
        LIMIT ?
        """, (
            like_query,
            like_query,
            like_query,
            like_query,
            like_query,
            like_query,
            like_query,
            like_query,
            limit,
        ))

    rows = cur.fetchall()
    conn.close()

    results = []

    for row in rows:
        item = row_to_item(row)
        item["score"] = 0.95
        item["match_type"] = "metadata_like"
        results.append(item)

    return results


def search_items_by_type(item_type: str, limit: int = 20):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM items
    WHERE item_type = ?
    LIMIT ?
    """, (item_type, limit))

    rows = cur.fetchall()
    conn.close()

    results = []

    for row in rows:
        item = row_to_item(row)
        item["score"] = 0.5
        item["match_type"] = "type_filter"
        results.append(item)

    return results


def search_exact_by_product_code(product_code: str):
    return search_items_by_product_code(product_code)