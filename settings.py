# -*- coding: utf-8 -*-
import os
import pyautogui
import logging
import json

# --- DETEKCJA ROZDZIELCZOŚCI ---
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
RESOLUTION_STRING = f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}"

# --- WYBÓR FOLDERU KONFIGURACYJNEGO ---
if SCREEN_WIDTH == 3840:
    CONFIG_FOLDER_NAME = "config_4k"
elif SCREEN_WIDTH == 2560:
    CONFIG_FOLDER_NAME = "config_2k"
elif SCREEN_WIDTH <= 1920:
    CONFIG_FOLDER_NAME = "config_laptop"
else:
    CONFIG_FOLDER_NAME = "config_laptop"
    logging.warning(f"Nierozpoznana rozdzielczość {RESOLUTION_STRING}. Używam config_laptop.")

# --- BUDOWANIE ŚCIEŻEK ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Ścieżka do plików CSV (Regionów)
CONFIG_PATH = os.path.join(BASE_DIR, CONFIG_FOLDER_NAME)

# 2. Ścieżka do grafik (resources/img/en/ROZDZIELCZOŚĆ)
GRAPHICS_PATH = os.path.join(BASE_DIR, "resources", "img", "en", RESOLUTION_STRING)

# 3. Plik CSV regionu bonusów
CSV_REGION_BONUS = os.path.join(CONFIG_PATH, "prostokat_bonusy.csv")

print(f"[SETTINGS] Wykryto ekran: {RESOLUTION_STRING}")
print(f"[SETTINGS] Używany folder config: {CONFIG_FOLDER_NAME}")
print(f"[SETTINGS] Ścieżka grafik: {GRAPHICS_PATH}")

# --- PAMIĘĆ OSTATNIEGO SERWERA (JSON) ---
LAST_SERVER_FILE = os.path.join(BASE_DIR, "last_server.json")

def load_last_server():
    if os.path.exists(LAST_SERVER_FILE):
        try:
            with open(LAST_SERVER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("active_server", "INT5402 Kap Arkona")
        except Exception as e:
            logging.error(f"[BŁĄD] Nie można wczytać last_server.json: {e}")
    return "INT5402 Kap Arkona"

def save_last_server(server_name):
    global ACTIVE_SERVER
    ACTIVE_SERVER = server_name
    try:
        with open(LAST_SERVER_FILE, "w", encoding="utf-8") as f:
            json.dump({"active_server": server_name}, f)
    except Exception as e:
        logging.error(f"[BŁĄD] Nie można zapisać last_server.json: {e}")

ACTIVE_SERVER = load_last_server()