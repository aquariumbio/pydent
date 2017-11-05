"""Define the http methods: login, get, put, post"""

import re
from config import config
import requests

HEADERS = {}
LOGGED_IN = False


def login():
    """Log in to Aquarium using login info in config.py"""
    global HEADERS
    global LOGGED_IN

    params = {
        "session": {
            "login": config["login"],
            "password": config["password"]
        }
    }

    try:
        result = requests.post(
            config['aquarium_url'] + "/sessions.json",
            json=params
        )
    except Exception as error:
        raise Exception("Could not log in to " + config["aquarium_url"] +
                        ": " + str(error))

    HEADERS = {"cookie": __fix_remember_token(result.headers["set-cookie"])}
    print(result.status_code)
    LOGGED_IN = True
    return result.status_code


def get(path):
    """Perform an http.get"""
    if LOGGED_IN:
        result = requests.get(config['aquarium_url'] + path, headers=HEADERS)
    else:
        raise Exception(
            "Not logged into an Aquarium instance. Run aq.login().")

    try:
        return result.json()
    except Exception:
        raise Exception(
            "Could not parse http.post result, most likely because of" + \
            "a server side error or incorrect url.")


def put(path):
    """Perform an http.put"""
    if LOGGED_IN:
        result = requests.put(config['aquarium_url'] + path, headers=HEADERS)
    else:
        raise Exception(
            "Not logged into an Aquarium instance. Run aq.login().")

    try:
        return result.json()
    except Exception:
        raise Exception(
            "Could not parse http.post result, most likely because of a server " + \
            "side error or incorrect url.")


def post(path, data):
    """Perform an http.post"""
    if LOGGED_IN:
        result = requests.post(config['aquarium_url'] + path, json=data, headers=HEADERS)
    else:
        raise Exception(
            "Not logged into an Aquarium instance. Run aq.login().")

    try:
        return result.json()
    except Exception:
        raise Exception(
            "Could not parse http.post result, most likely because of a server" + \
            "side error or incorrect url.")


def __fix_remember_token(header):
    """Reformat the remember token from rails, which may have extra characters
    in its name
    """
    parts = header.split(';')
    rtok = ""
    for part in parts:
        cparts = part.split('=')
        if re.match('remember_token', cparts[0]):
            rtok = cparts[1]
    return "remember_token=" + rtok + "; " + header
