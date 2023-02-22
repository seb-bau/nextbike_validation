import requests
from jsonmerge import Merger
import json


def openwowi_create_token(base_url, user, password, refresh_token=3600):
    url = f"{base_url}/oauth2/token"

    payload = f"grant_type=password&" \
              f"username={user}&" \
              f"password={password}&" \
              f"refresh_token={refresh_token}"

    headers = {
        'Accept': 'text/plain',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code != 200:
        print(f"Fehler bei der Authentifizierung an OPEN WOWI. Status {response.status_code}:{response.text}")
        return False

    response_json = response.json()
    return response_json["access_token"]


def openwowi_get_all_economic_units(base_url, token, api_key, only_rental_buildings=False):
    url = f"{base_url}/openwowi/v1.0/CommercialInventory/EconomicUnits?apiKey={api_key}"

    headers = {
        'Accept': 'text/plain',
        'Authorization': f'Bearer {token}'
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200:
        print(f"Fehler beim Abruf der Wirtschaftseinheiten. Status {response.status_code}:{response.text}")
        return False

    if only_rental_buildings:
        ret_json = []
        for eco_unit in response.json():
            if eco_unit["IdNum"].startswith("00") or eco_unit["IdNum"].startswith("20"):
                ret_json.append(eco_unit)
        return ret_json
    else:
        return response.json()


def openwowi_get_all_buildings(base_url, token, api_key, wie=None):
    url = f"{base_url}/openwowi/v1.0/CommercialInventory/BuildingLands?apiKey={api_key}"

    headers = {
        'Accept': 'text/plain',
        'Authorization': f'Bearer {token}'
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200:
        print(f"Fehler beim Abruf der Gebäude. Status {response.status_code}:{response.text}")
        return False

    return response.json()


def openwowi_get_building(base_url, token, api_key, building_id):
    url = f"{base_url}/openwowi/v1.0/CommercialInventory/BuildingLands?apiKey={api_key}"

    headers = {
        'Accept': 'text/plain',
        'Authorization': f'Bearer {token}'
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200:
        print(f"Fehler beim Abruf der Gebäude. Status {response.status_code}:{response.text}")
        return None
    else:
        for t_building in response.json():
            if t_building['Id'] == building_id:
                return t_building
        return None


def openwowi_get_economic_unit(base_url, token, api_key, economic_unit_id):
    url = f"{base_url}/openwowi/v1.0/CommercialInventory/EconomicUnits?apiKey={api_key}"

    headers = {
        'Accept': 'text/plain',
        'Authorization': f'Bearer {token}'
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200:
        print(f"Fehler beim Abruf der Economic Units. Status {response.status_code}:{response.text}")
        return None
    else:
        for t_economic_unit in response.json():
            if t_economic_unit['Id'] == economic_unit_id:
                return t_economic_unit
        return None


def openwowi_get_use_unit(base_url, token, api_key, use_unit_id):
    headers = {
        'Accept': 'text/plain',
        'Authorization': f'Bearer {token}'
    }
    inner_url = f"{base_url}/openwowi/v1.0/CommercialInventory/" \
                f"UseUnits?apiKey={api_key}&limit=100&useUnitId={use_unit_id}"
    inner_response = requests.request("GET", inner_url, headers=headers)
    if inner_response.status_code != 200:
        print(f"Fehler beei der Verbindung")
        return None
    complete_response = inner_response.json()
    return complete_response


def openwowi_get_all_use_units_via_offset(base_url, token, api_key):
    headers = {
        'Accept': 'text/plain',
        'Authorization': f'Bearer {token}'
    }
    complete_response = None
    merge_schema = {"mergeStrategy": "append"}
    merger = Merger(schema=merge_schema)

    t_offset = 0
    t_response_count = 100
    while t_response_count == 100:
        url = f"{base_url}/openwowi/v1.0/CommercialInventory/UseUnits" \
              f"?apiKey={api_key}" \
              f"&offset={t_offset}" \
              f"&limit=100" \
              f"&includeUseUnitTypes=true"

        response = requests.request("GET", url, headers=headers)

        if response.status_code != 200:
            print(f"Fehler in openwowi_get_all_use_units_via_offset: {response.status_code} - {response.text}")
            return None

        if complete_response is None:
            complete_response = response.json()
        else:
            complete_response = merger.merge(complete_response, response.json())

        t_response_count = len(response.json())
        t_total_contractors = len(complete_response)
        t_offset += 100
        print(f"Total: {t_total_contractors}")
    return complete_response


def openwowi_get_all_use_units(base_url, token, api_key, building=None):
    # url = f"{base_url}/openwowi/v1.0/CommercialInventory/UseUnits?apiKey={api_key}"
    headers = {
        'Accept': 'text/plain',
        'Authorization': f'Bearer {token}'
    }
    if building is None:
        complete_response = None
        merge_schema = {"mergeStrategy": "append"}
        merger = Merger(schema=merge_schema)
        eco_units = openwowi_get_all_economic_units(base_url, token, api_key)
        counter = 0
        for eco_unit in eco_units:
            # print(f"WIE {eco_unit['Id']}")
            url = f"{base_url}/openwowi/v1.0/CommercialInventory/" \
                  f"UseUnits?apiKey={api_key}&limit=100&economicUnitId={eco_unit['Id']}"
            response = requests.request("GET", url, headers=headers)

            # Maximale Anzahl 100
            response_json = response.json()
            if len(response_json) == 100:
                print(f"WIE {eco_unit['Id']} >= 100, Abfrage auf Objektebene")
                t_buildings = openwowi_get_all_buildings(base_url, token, api_key)
                for t_building in t_buildings:
                    if t_building["EconomicUnitId"] == eco_unit['Id']:
                        inner_url = f"{base_url}/openwowi/v1.0/CommercialInventory/" \
                                    f"UseUnits?apiKey={api_key}&limit=100&buildingId={t_building['Id']}"
                        # print(inner_url)

                        inner_response = requests.request("GET", inner_url, headers=headers)
                        # print(inner_response.status_code)
                        # print(inner_response.text)
                        if inner_response.status_code != 200:
                            print(f"Fehler beei der Verbindung")
                            continue

                        if complete_response is None:
                            complete_response = inner_response.json()
                        else:
                            complete_response = merger.merge(complete_response, inner_response.json())
                print("fertig, weiter")
                continue

            if complete_response is None:
                # print("is none")
                complete_response = response_json
            else:
                # print(f"is set, len {len(complete_response)}")
                complete_response = merger.merge(complete_response, response_json)

            print(f"response len: {len(complete_response)}")
            counter += 1

            if response.status_code != 200:
                print(f"Fehler beim Abruf der Gebäude. Status {response.status_code}:{response.text}")
                return False
    else:
        inner_url = f"{base_url}/openwowi/v1.0/CommercialInventory/" \
                    f"UseUnits?apiKey={api_key}&limit=100&buildingId={building}"
        inner_response = requests.request("GET", inner_url, headers=headers)
        if inner_response.status_code != 200:
            print(f"Fehler beei der Verbindung")
            return None
        complete_response = inner_response.json()

    return complete_response


def openwowi_get_all_license_agreements(base_url, token, api_key, exclude_garage=False):
    # url = f"{base_url}/openwowi/v1.0/CommercialInventory/UseUnits?apiKey={api_key}"

    complete_response = None
    merge_schema = {"mergeStrategy": "append"}
    merger = Merger(schema=merge_schema)
    buildings = openwowi_get_all_buildings(base_url, token, api_key)
    counter = 0
    anzahl_geb = len(buildings)
    counter_geb = 0
    for building in buildings:
        counter_geb += 1
        if exclude_garage:
            parts = building['IdNum'].split(".")
            geb_value = int(parts[1])
            if geb_value >= 900:
                continue
        print(f"Gebäude {counter_geb} von {anzahl_geb}")

        use_units = openwowi_get_all_use_units(base_url, token, api_key, building['Id'])

        for use_unit in use_units:
            t_agreements = openwowi_get_license_agreements_of_use_unit(base_url, token, api_key, use_unit['Id'])

            if complete_response is None:
                # print("is none")
                complete_response = t_agreements
            else:
                # print(f"is set, len {len(complete_response)}")
                complete_response = merger.merge(complete_response, t_agreements)
        print(f"Response LEN: {len(complete_response)}")
    return complete_response


def openwowi_get_license_agreements_of_use_unit(base_url, token, api_key, use_unit):
    headers = {
        'Accept': 'text/plain',
        'Authorization': f'Bearer {token}'
    }

    url = f"{base_url}/openwowi/v1.0/RentAccounting/" \
          f"LicenseAgreements?apiKey={api_key}&limit=100&useUnitId={use_unit}"

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200:
        print(f"Fehler in openwowi_get_license_agreements_of_use_unit, requests code {response.status_code}")
        return None

    return response.json()


def openwowi_get_contractors_of_license_agreement(base_url, token, api_key, license_agreement_id):
    headers = {
        'Accept': 'text/plain',
        'Authorization': f'Bearer {token}'
    }

    url = f"{base_url}/openwowi/v1.0/RentAccountingPersonDetails/Contractors" \
          f"?apiKey={api_key}" \
          f"&licenseAgreementId={license_agreement_id}" \
          f"&limit=100" \
          f"&includeMainAddress=true" \
          f"&includeMainCommunication=true" \
          f"&includePersonAddresses=true" \
          f"&includePersonCommunications=true" \
          f"&includePersonBankAccounts=true"

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200:
        print(f"Fehler in openwowi_get_contractors_of_license_agreement: {response.status_code} - {response.text}")
        return None

    return response.json()


def openwowi_get_contractors_of_license_agreement_from_cache(contractors_json, license_agreement_id):
    complete_response = None
    merge_schema = {"mergeStrategy": "append"}
    merger = Merger(schema=merge_schema)

    for t_contractor in contractors_json:
        if t_contractor['LicenseAgreementId'] == license_agreement_id:
            if complete_response is None:
                complete_response = [t_contractor]
            else:
                complete_response = merger.merge(complete_response, [t_contractor])

    return complete_response


def openwowi_get_all_contractors(base_url, token, api_key):
    headers = {
        'Accept': 'text/plain',
        'Authorization': f'Bearer {token}'
    }
    complete_response = None
    merge_schema = {"mergeStrategy": "append"}
    merger = Merger(schema=merge_schema)

    t_offset = 0
    t_response_count = 100
    t_total_contractors = 0
    while t_response_count == 100:
        url = f"{base_url}/openwowi/v1.0/RentAccountingPersonDetails/Contractors" \
              f"?apiKey={api_key}" \
              f"&offset={t_offset}" \
              f"&limit=100" \
              f"&includeMainAddress=true" \
              f"&includeMainCommunication=true" \
              f"&includePersonAddresses=true" \
              f"&includePersonCommunications=true" \
              f"&includePersonBankAccounts=true"

        response = requests.request("GET", url, headers=headers)

        if response.status_code != 200:
            print(f"Fehler in openwowi_get_all_contractors: {response.status_code} - {response.text}")
            return None

        if complete_response is None:
            complete_response = response.json()
        else:
            complete_response = merger.merge(complete_response, response.json())

        t_response_count = len(response.json())
        t_total_contractors = len(complete_response)
        t_offset += 100
        print(f"Total: {t_total_contractors}")
    return complete_response


def openwowi_get_license_agreements_from_file(cache_file):
    with open(cache_file, 'r') as f:
        return_json = json.load(f)

    return return_json


def openwowi_get_contract_positions(base_url, token, api_key, license_agreement_id):
    headers = {
        'Accept': 'text/plain',
        'Authorization': f'Bearer {token}'
    }

    url = f"{base_url}/openwowi/v1.0/RentAccounting/" \
          f"ContractPositions?apiKey={api_key}&limit=100&licenseAgreementId={license_agreement_id}"

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200:
        print(f"Fehler in openwowi_get_contract_positions, requests code {response.status_code}")
        return False

    return response.json()


def openwowi_local_building_idnum_to_id(idnum, building_dict):
    for tt_building in building_dict:
        if tt_building['IdNum'] == idnum:
            return tt_building['Id']

    return None


def openwowi_local_economic_unit_id_to_idnum(economic_unit_id, economic_units_json):
    for economic_unit_entry in economic_units_json:
        if economic_unit_entry['Id'] == economic_unit_id:
            return economic_unit_entry['IdNum']
    return None


def openwowi_local_economic_unit_idnum_to_id(economic_unit_idnum: str, economic_units_json):
    for economic_unit_entry in economic_units_json:
        if economic_unit_entry['IdNum'] == economic_unit_idnum:
            return economic_unit_entry['Id']
    return None


def openwowi_local_get_use_unit(use_unit_idnum, use_unit_json):
    for t_use_unit in use_unit_json:
        if t_use_unit['IdNum'] == use_unit_idnum:
            return t_use_unit
    return None


def openwowi_local_get_contract(contract_idnum, contract_json):
    for t_contract in contract_json:
        if t_contract['IdNum'] == contract_idnum:
            return t_contract
    return None
