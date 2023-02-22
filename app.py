import os
import sqlite3

from flask import Flask, request, redirect
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv(os.path.join(app.root_path, '.env'))


@app.route('/')
def redirect_request():
    return redirect(os.environ.get("redirect_url"), code=302)


@app.route('/nextbike/v1/validate')
def validate_request():
    nachname = request.args.get("lastname", "")
    contract_idnum = request.args.get("contract", "")
    if len(nachname) == 0 or len(contract_idnum) == 0:
        return "Arguments_missing", 400
    else:
        db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "cache.db")
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        query = "SELECT 1 FROM contractors WHERE lower(lastname)=? AND contract_idnum=? LIMIT 1"
        query_args = (nachname.lower(), contract_idnum)
        cur.execute(query, query_args)
        rows = cur.fetchall()
        if len(rows) > 0:
            return "valid", 200
        else:
            return "user not found", 404


if __name__ == '__main__':
    app.run()


@app.before_request
def check_api_key():
    headers = request.headers
    key = headers.get("Authorization", "")
    if len(key) > 0:
        expected_key = os.environ.get("api_key", "")
        if len(expected_key) > 0:
            if key != f"Bearer {expected_key}":
                return "Unauthorized", 401
        else:
            return "Server error", 500
    else:
        return "API-Key missing", 401
