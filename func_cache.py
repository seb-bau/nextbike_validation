import os
import sqlite3

from dotenv import load_dotenv
from datetime import datetime
from func_openwowi import *


def preload_contractors():
    load_dotenv(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".env"), encoding='utf-8')
    wowi_url = os.environ.get("openwowi_url")
    wowi_user = os.environ.get("openwowi_user")
    wowi_pass = os.environ.get("openwowi_pass")
    wowi_api_key = os.environ.get("openwowi_api_key")

    wowi_token = openwowi_create_token(wowi_url, wowi_user, wowi_pass, wowi_api_key)

    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "cache.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    query = 'create table contractors (id integer constraint contractors_pk primary key autoincrement, lastname TEXT' \
            ' not null, firstname TEXT, contract_idnum integer not null);'
    cur.execute(query)
    con.commit()

    contractors = openwowi_get_all_contractors(wowi_url, wowi_token, wowi_api_key)

    for contractor in contractors:
        lastname = contractor['PersonLastName']
        firstname = contractor['PersonFirstName']
        contract_idnum = contractor['LicenseAgreement']
        contract_end = contractor['EndOfContract']

        if lastname is None:
            continue

        if contract_end is not None:
            contract_end_dt = datetime.strptime(contract_end, "%Y-%m-%d")
            now = datetime.now()
            if now > contract_end_dt:
                continue

        query = f"INSERT INTO contractors (lastname, firstname, contract_idnum) VALUES (?, ?, ?)"
        query_args = (lastname, firstname, contract_idnum)
        cur.execute(query, query_args)
        con.commit()

    con.close()


preload_contractors()
