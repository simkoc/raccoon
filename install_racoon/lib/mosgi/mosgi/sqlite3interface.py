import base64
import sqlite3


def get_sqlite3_connection(path):
    raise 'this stuff is deprecated. DO NOT USE'
    return sqlite3.connect(path)


def save_session(db_conn, id, session_path, session_string, logger=None):
    raise 'this stuff is deprecated. DO NOT USE'
    query = "INSERT INTO SESSIONS VALUES(?,?,?)"
    values = (id, session_path, base64.b64encode(session_string))
    db_conn.execute(query, values)
    db_conn.commit()


def save_xdebug(db_conn, id, xdebug_string):
    raise 'this stuff is deprecated. DO NOT USE'
    query = "INSERT INTO XDEBUG_DUMPS VALUES (?,?)"
    values = (id, base64.b64encode(xdebug_string))
    db_conn.execute(query, values)
    db_conn.commit()
