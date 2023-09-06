import logging
import os
import requests
import sys
import graypy

from flask import Flask, request, redirect
from dotenv import dotenv_values


def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    app.logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))


app = Flask(__name__)
settings = dotenv_values(os.path.join(app.root_path, '.env'))

log_method = settings.get("log_method", "file").lower()
log_level = settings.get("log_level", "info").lower()
log_levels = {'debug': 10, 'info': 20, 'warning': 30, 'error': 40, 'critical': 50}
app.logger.setLevel(log_levels.get(log_level, 20))
sys.excepthook = handle_unhandled_exception
if log_method == "file":
    logging.basicConfig(filename=os.path.join(app.root_path, "log", "nextbike_validation"))
elif log_method == "graylog":
    graylog_host = settings.get("graylog_host", "127.0.0.1")
    graylog_port = int(settings.get("graylog_port", 12201))
    handler = graypy.GELFUDPHandler(graylog_host, graylog_port)
    app.logger.addHandler(handler)


def normalize_idnum(input_contract):
    # Get only digits from input
    ret_contract = ''.join(filter(str.isdigit, input_contract))
    mask = settings.get("contract_mask").lower()
    mask_delimiter = mask.replace("x", "")[0]

    mask_without_delim = mask.replace(mask_delimiter, "")
    ret_contract = ret_contract.zfill(len(mask_without_delim))

    delim_positions = [pos for pos, char in enumerate(mask) if char == mask_delimiter]
    for pos in delim_positions:
        ret_contract = ret_contract[:pos] + mask_delimiter + ret_contract[pos:]

    return ret_contract


def openwowi_create_token(base_url, user, password, refresh_token=3600, user_agent="nextbike"):
    url = f"{base_url}/oauth2/token"

    payload = f"grant_type=password&" \
              f"username={user}&" \
              f"password={password}&" \
              f"refresh_token={refresh_token}"

    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/plain',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code != 200:
        errmsg = f"OPEN WOWI Auth Error. Status {response.status_code}:{response.text}"
        app.logger.error(errmsg)
        raise ConnectionError(errmsg)

    response_json = response.json()
    return response_json["access_token"]


def openwowi_get_contract(base_url, token, api_key, contract_idnum, user_agent="nextbike"):
    url = f"{base_url}/openwowi/v1.2/RentAccounting/LicenseAgreements" \
          f"?apiKey={api_key}" \
          f"&licenseAgreementIdNum={contract_idnum}" \
          f"&limit=1"

    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/plain',
        'Authorization': f'Bearer {token}'
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code == 200:
        tret = response.json()
        if type(tret) is list and len(tret) > 0:
            return tret
        return None
    else:
        errmsg = f"Request error. Code {response.status_code}: {response.text}"
        app.logger.error(errmsg)
        raise ConnectionError(errmsg)


@app.route('/')
def redirect_request():
    return redirect(settings.get("redirect_url"), code=302)


@app.route('/nextbike/v1/validate')
def validate_request():
    # Setup environment
    wowi_url = settings.get("openwowi_url")
    wowi_user = settings.get("openwowi_user")
    wowi_pass = settings.get("openwowi_pass")
    wowi_api_key = settings.get("openwowi_api_key")
    user_agent = settings.get("user_agent")
    if user_agent is None or len(user_agent.strip()) == 0:
        user_agent = "nextbike_validation/1.0"

    contract_idnum = request.args.get("contract", "")
    contract_idnum = normalize_idnum(contract_idnum)
    print(contract_idnum)
    if len(contract_idnum) == 0:
        return "Arguments_missing", 400
    else:
        wowi_token = openwowi_create_token(wowi_url, wowi_user, wowi_pass, user_agent=user_agent)
        tcontract = openwowi_get_contract(wowi_url, wowi_token, wowi_api_key, contract_idnum, user_agent=user_agent)

        if tcontract is not None:
            app.logger.info(f"nextbike_access: {contract_idnum} is valid. Caller {request.remote_addr}")
            return "valid", 200
        else:
            app.logger.info(f"nextbike_access: {contract_idnum} IS INVALID. Caller {request.remote_addr}")
            return "contract_not_found", 404


if __name__ == '__main__':
    app.run()


@app.before_request
def check_api_key():
    headers = request.headers
    key = headers.get("Authorization", "")
    if len(key) > 0:
        expected_key = settings.get("api_key", "")
        if len(expected_key) > 0:
            if key != f"Bearer {expected_key}":
                return "Unauthorized", 401
        else:
            return "Server error", 500
    else:
        return "API-Key missing", 401
