import psycopg2 as postgres


def get_postgres_connection(host, user, pwd, db_name):
    pars = {"database": db_name}

    if host:
        pars["host"] = host
    if user:
        pars["user"] = user
    if pwd:
        pars["password"] = pwd

    conn = postgres.connect(**pars)
    conn.autocommit = True
    return conn


def save_session(db_con, expid, selcmdctr, httprequestid, session, session_content):
    with db_con.cursor() as cur:
        query = """
        INSERT INTO SessionsView(expid, selcmdctr, httpreqctr, name, content)
        VALUES(%(expid)s, %(selcmdctr)s, %(httpreqctr)s, %(name)s, %(content)s);"""
        valuedict = {"expid": expid,
                     "selcmdctr": selcmdctr,
                     "httpreqctr": httprequestid,
                     "name": session,
                     "content": postgres.Binary(session_content)}
        cur.execute(query, valuedict)


def save_xdebug(db_con, expid, selcmdctr, httprequestid, name, xdebug_content):
    with db_con.cursor() as cur:
        query = """INSERT INTO XdebugDumpsRacoonView(expid, selcmdctr, httpreqctr, name, content)
        VALUES(%(expid)s, %(selcmdctr)s, %(httpreqctr)s, %(name)s, %(content)s);"""
        valuedict = {"expid": expid,
                     "selcmdctr": selcmdctr,
                     "httpreqctr": httprequestid,
                     "name": name,
                     "content": postgres.Binary(xdebug_content)}
        cur.execute(query, valuedict)
