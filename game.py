import requests

from config import GAME_SERVER


def get_state():
    response = requests.get(f"{GAME_SERVER}/state")
    response.raise_for_status()
    return response.json()


def do(action):
    response = requests.post(f"{GAME_SERVER}/action", json={"actions": [action]})
    response.raise_for_status()
    return response.json()["state_after"]


def load(save_name):
    response = requests.post(f"{GAME_SERVER}/load", json={"name": save_name})
    response.raise_for_status()
    return response.json()["state_after"]


def save(save_name):
    response = requests.post(f"{GAME_SERVER}/save", json={"name": save_name})
    response.raise_for_status()
