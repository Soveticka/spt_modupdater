import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def get_soup(url: str) -> BeautifulSoup:
    return BeautifulSoup(requests.get(url).content, "html.parser")


def get_spt_version(soup: BeautifulSoup) -> str:
    version = soup.find("ul", attrs={"class": "labelList"}).find("span", attrs={"class": "badge"}).contents[0][4:]
    return version


def get_mod_version(soup: BeautifulSoup) -> str:
    version = soup.find("h1", attrs={"class": "contentTitle"}).find("span", attrs={"class": "filebaseVersionNumber"}).contents[0]
    return version


def get_download_link(soup: BeautifulSoup) -> str:
    spt_down_link = soup.find("a", attrs={"class": "externalURL"}).get("href")
    soup = get_soup(spt_down_link)
    mod_down_link = soup.find("a", attrs={"class": "noDereferer"}).get("href")
    return mod_down_link


def get_download_server(url: str) -> str:
    if "github" in url:
        return "github"
    elif "google" in url:
        return "google"
    elif "dropbox" in url:
        return "dropbox"
    elif "gitea" in url:
        return "gitea"
    else:
        print(f"Unknown server, edit the code and update the modlist.. url: {url}")
        return ""


def get_mod_name(soup: BeautifulSoup) -> str:
    name = soup.find("h1", attrs={"class": "contentTitle"}).find("span", attrs={"itemprop": "name"}).contents[0]
    return name


def load_data(file: str) -> dict:
    path = Path(__file__).resolve().parents[0] / "data"
    try:
        with open(path / f"{file}.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error while reading json: {e}")


def save_data(file: str, data: dict) -> bool:
    path = Path(__file__).resolve().parents[0] / "data"
    try:
        with open(path / f"{file}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except TypeError as e:
        print(f"Error while saving json: {e}")
    return False


def convert_input_to_bool(message: str) -> bool:
    text = input(message).lower()
    return True if text == "true" or text == "yes" else False


def add_mod(url: str, manual=False) -> bool:
    data = load_data("modlist")
    soup = get_soup(url)
    modname = get_mod_name(soup)

    mod = {
        f"{modname}": {
            "installed": False,
            "auto_update": False,
            "links": {"spt": url, "download": get_download_link(soup), "server": get_download_server(get_download_link(soup))},
            "version": {"spt": get_spt_version(soup), "current_version": get_mod_version(soup), "installed_version": "0.0"},
            "mod_type": {"server": False, "client": False, "headless": False},
        }
    }

    if manual:
        installed = convert_input_to_bool("Is mod installed? ")
        mod.get(modname)["installed"] = installed
        if installed:
            mod.get(modname)["version"]["installed_version"] = mod.get(modname)["version"]["current_version"]
        mod.get(modname)["auto_update"] = convert_input_to_bool("Can mod be auto updated? ")
        mod.get(modname)["mod_type"]["server"] = convert_input_to_bool("Is mod Server side? ")
        mod.get(modname)["mod_type"]["client"] = convert_input_to_bool("Is mod Client side? ")
        mod.get(modname)["mod_type"]["headless"] = convert_input_to_bool("Is mod for headless? ")

    data.update(mod)
    if save_data("modlist", data):
        return True
    else:
        return False


def update_modlist(mod: list, soup) -> bool:
    data = load_data("modlist")

    new_version = get_mod_version(soup)
    mod_name = get_mod_name(soup)
    new_download_link = get_download_link(soup)
    mod["version"]["current_version"] = new_version
    mod["links"]["download"] = new_download_link
    data[mod_name] = mod

    if save_data("modlist", data):
        return True
    else:
        return False


def check_for_updates() -> None:
    data = load_data("modlist")
    spt_version = load_data("sptversion").get("version")

    for mod in data:
        mod = data.get(mod)
        soup = get_soup(mod["links"]["spt"])
        spt_version_mod = get_spt_version(soup)
        mod_version = get_mod_version(soup)

        if spt_version == spt_version_mod and mod["version"]["current_version"] != mod_version:
            print(f"New version {mod_version} of mod {mod} is available - {mod['links']['spt']}")
            print("Updating modlist")
            if update_modlist(mod, soup):
                print("Version info updated in modlist")
            else:
                print("Something went wrong :/")
