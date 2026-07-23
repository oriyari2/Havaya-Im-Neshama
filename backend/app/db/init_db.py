from psycopg import Connection

from backend.app.db.schema import CREATE_EXTENSION_SQL, CREATE_INDEX_SQL, CREATE_TABLE_SQL


def initialize_database(conn: Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(CREATE_EXTENSION_SQL)
        for statement in CREATE_TABLE_SQL:
            cur.execute(statement)
        for statement in CREATE_INDEX_SQL:
            cur.execute(statement)
    conn.commit()
