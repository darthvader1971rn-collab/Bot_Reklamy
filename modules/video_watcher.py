# -*- coding: utf-8 -*-
import pyautogui
import time
import os
import logging
import csv
from datetime import datetime, timedelta
import settings

# AGRESYWNA CZUŁOŚĆ DLA PANELU
CONFIDENCE = 0.75

# Słownik zbanowanych pozycji: { (x, y): datetime_odblokowania }
BANNED_POSITIONS = {}
BAN_TOLERANCE_PX = 15

# Przesunięcie w prawo przy klikaniu bonusu
CLICK_OFFSET_X = 23


def perform_hard_click(x, y):
    """
    Fizyczne kliknięcie (Wciśnij -> Trzymaj -> Puść).
    Dojazd (0.3s) + Click.
    """
    try:
        pyautogui.moveTo(x, y, duration=0.3)
        time.sleep(0.1)
        pyautogui.mouseDown()
        time.sleep(0.15)
        pyautogui.mouseUp()
        time.sleep(0.5)
    except Exception:
        pass


def park_mouse_left_edge():
    screen_w, screen_h = pyautogui.size()
    pyautogui.moveTo(100, screen_h // 2, duration=0.2)


def load_region(path, optional=False):
    if not os.path.exists(path):
        if not optional:
            logging.error(f"[BŁĄD] Plik nie istnieje: {path}")
        return None

    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            next(reader)
            row = next(reader)

            if len(row) >= 6:
                return (int(row[0]), int(row[1]), int(row[4]), int(row[5]))
            elif len(row) >= 4:
                return (int(row[0]), int(row[1]), int(row[2]), int(row[3]))
            else:
                return None
    except Exception as e:
        logging.error(f"[BŁĄD] Zepsuty plik CSV ({path}): {e}")
        return None


def check_exists(image_name, region=None):
    full_path = os.path.join(settings.GRAPHICS_PATH, image_name)
    if not os.path.exists(full_path):
        return False
    try:
        return pyautogui.locateOnScreen(full_path, region=region, confidence=CONFIDENCE, grayscale=False) is not None
    except Exception:
        return False


def click_screen_center():
    w, h = pyautogui.size()
    perform_hard_click(w // 2, h // 2)
    logging.info("[VIDEO] Ślepy klik w środek ekranu (Fallback).")


def perform_anti_afk():
    if time.time() - watch_cycle.last_afk_move > 60:
        logging.info("[VIDEO] Anti-AFK: Wykonuję ruch myszką zapobiegający uśpieniu.")
        pyautogui.moveRel(15, 0, duration=0.2)
        pyautogui.moveRel(-15, 0, duration=0.2)
        watch_cycle.last_afk_move = time.time()


def find_and_click_bonus_with_check(image_name, region, exclusion_region=None):
    full_path = os.path.join(settings.GRAPHICS_PATH, image_name)
    if not os.path.exists(full_path):
        return False

    try:
        for box in pyautogui.locateAllOnScreen(full_path, region=region, confidence=CONFIDENCE, grayscale=False):
            center_x = int(box.left + box.width / 2)
            center_y = int(box.top + box.height / 2)

            # --- AKTYWNA TARCZA OBSZAROWA ---
            if exclusion_region:
                ex_x, ex_y, ex_w, ex_h = exclusion_region
                if ex_x <= center_x <= (ex_x + ex_w) and ex_y <= center_y <= (ex_y + ex_h):
                    continue

            # --- ANTY-CZERWONA TARCZA (CZUŁOŚĆ 95%) ---
            if image_name == "dollar.png":
                bad_path = os.path.join(settings.GRAPHICS_PATH, "dollar_bad.png")
                if os.path.exists(bad_path):
                    try:
                        bad_region = (
                            max(0, int(box.left) - 5),
                            max(0, int(box.top) - 5),
                            int(box.width) + 10,
                            int(box.height) + 10,
                        )
                        is_bad = pyautogui.locateOnScreen(bad_path, region=bad_region, confidence=0.95)
                    except Exception:
                        is_bad = None
                    if is_bad:
                        logging.info("[VIDEO] Znaleziono CZERWONY przycisk! Ignoruję kliknięcie.")
                        continue

            now = datetime.now()
            expired = [pos for pos, t in BANNED_POSITIONS.items() if t < now]
            for pos in expired:
                del BANNED_POSITIONS[pos]

            is_banned = any(
                abs(center_x - bx) <= BAN_TOLERANCE_PX and abs(center_y - by) <= BAN_TOLERANCE_PX
                for (bx, by) in BANNED_POSITIONS
            )
            if is_banned:
                continue

            ban_label = f"Pozycja_{center_x}_{center_y}"
            logging.info(f"[VIDEO] Klikam bonus: {image_name} ({ban_label})")

            # Przesunięcie celownika w prawo o zadany offset
            target_x = center_x + CLICK_OFFSET_X
            perform_hard_click(target_x, center_y)

            time.sleep(1.5)
            error_imgs = ["no_gold_bonus.png", "bank_full.png"]

            for err in error_imgs:
                if check_exists(err):
                    logging.warning(f"[VIDEO] Błąd na {ban_label}. BAN NA 2H.")
                    BANNED_POSITIONS[(center_x, center_y)] = now + timedelta(hours=2)

                    find_and_click_simple(err, wait_after=1)

                    # --- KLIKNIĘCIE W ZIELONY PRZYCISK CLOSE ---
                    if not find_and_click_simple("close_limit.png", retry=3, wait_after=1):
                        logging.warning("[VIDEO] Nie potrafię kliknąć close_limit.png! Upewnij się, że plik graficzny istnieje.")

                    return True

            return True

        return False
    except Exception:
        return False


def find_and_click_simple(image_name, retry=2, wait_after=1, fallback_center=False, region=None):
    """
    Wersja prosta dla reklam i zamykania okien.
    """
    full_path = os.path.join(settings.GRAPHICS_PATH, image_name)
    if not os.path.exists(full_path):
        return False

    for _ in range(retry):
        try:
            if region and region != (0, 0, 0, 0):
                loc = pyautogui.locateCenterOnScreen(full_path, region=region, confidence=CONFIDENCE, grayscale=False)
            else:
                loc = pyautogui.locateCenterOnScreen(full_path, confidence=CONFIDENCE, grayscale=False)

            if loc:
                logging.info(f"[VIDEO] Klikam: {image_name}")
                perform_hard_click(loc.x, loc.y)
                time.sleep(wait_after)
                return True
        except Exception:
            pass
        time.sleep(0.3)

    if fallback_center:
        logging.warning(f"[VIDEO] Nie widzę '{image_name}'. Próbuję kliknąć w środek.")
        click_screen_center()
        time.sleep(wait_after)
        return True

    return False


def wait_for_button(target_image, max_seconds=65, check_interval=5):
    logging.info(f"[VIDEO] Czekam na {target_image} (Max {max_seconds}s)...")
    park_mouse_left_edge()
    start_time = time.time()
    while time.time() - start_time < max_seconds:
        if check_exists(target_image, region=None):
            logging.info(f"[VIDEO] Wykryto: {target_image}!")
            return True
        time.sleep(check_interval)
    logging.warning(f"[VIDEO] Timeout! Nie znaleziono {target_image}.")
    return False


# --- GŁÓWNA PĘTLA CYKLU ---

def watch_cycle():
    # Inicjalizacja wewnętrznych zegarów
    if not hasattr(watch_cycle, "video_block_until"):
        watch_cycle.video_block_until = None
    if not hasattr(watch_cycle, "last_afk_move"):
        watch_cycle.last_afk_move = time.time()

    logging.info("[VIDEO] --- START CYKLU (Bonusy + Reklamy + Pollux) ---")
    start_time = time.time()

    # Wczytanie regionów
    bonus_path = getattr(settings, "CSV_REGION_BONUS", os.path.join(settings.CONFIG_PATH, "prostokat_bonusy.csv"))
    exclusion_path = os.path.join(settings.CONFIG_PATH, "prostokat_wykluczenie.csv")

    bonus_region = load_region(bonus_path, optional=False)
    exclusion_region = load_region(exclusion_path, optional=True)

    if not bonus_region:
        logging.error("[VIDEO] Brak regionu bonusów! Zatrzymuję skanowanie.")
        time.sleep(2)
        return 0.0

    if exclusion_region:
        logging.info("[VIDEO] Tarcza aktywna: Wykluczam kliknięcia w zakazanym obszarze.")

    now = datetime.now()
    video_blocked = False

    # Sprawdzenie, czy aktywna jest blokada
    if watch_cycle.video_block_until:
        if now < watch_cycle.video_block_until:
            logging.info(f"[VIDEO] Blokada wideo aktywna do {watch_cycle.video_block_until.strftime('%Y-%m-%d %H:%M:%S')}. Zbieram tylko darmowe.")
            video_blocked = True
        else:
            logging.info("[VIDEO] Blokada wideo minęła. Wracam do normalnego trybu.")
            watch_cycle.video_block_until = None

    start_collection = time.time()
    collected = True

    # --- FAZA ZBIERANIA ---
    while collected:
        if time.time() - start_collection > 120:
            break
        collected = False

        # 1. Zwykłe (darmowe) bonusy - szukamy zawsze
        if find_and_click_bonus_with_check("prestige.png", bonus_region, exclusion_region):
            collected = True
            continue
        if find_and_click_bonus_with_check("dollar.png", bonus_region, exclusion_region):
            collected = True
            continue

        # 2. Fioletowe bonusy (wymagają wideo) - szukamy TYLKO jeśli nie ma blokady
        if not video_blocked:
            if find_and_click_bonus_with_check("prestige_purple.png", bonus_region, exclusion_region):
                collected = True
                continue
            if find_and_click_bonus_with_check("dollar_purple.png", bonus_region, exclusion_region):
                collected = True
                continue

    # --- DETEKCJA LIMITU WIDEO ---
    if check_exists("bonus_video_disabled.png") or check_exists("limit_wideo.png"):
        logging.warning("[VIDEO] Wykryto wyczerpany limit wideo!")

        if check_exists("disable_video_limit.png"):
            find_and_click_simple("disable_video_limit.png", wait_after=1)
        else:
            click_screen_center()

        # Limit do 16:00 dla US102 Grand Central, domyślnie 14:00 dla innych
        server_name = getattr(settings, "ACTIVE_SERVER", "")
        limit_hour = 16 if "US102" in server_name else 14

        limit_time = now.replace(hour=limit_hour, minute=0, second=0, microsecond=0)
        if now >= limit_time:
            limit_time = limit_time + timedelta(days=1)

        watch_cycle.video_block_until = limit_time
        logging.info(f"[VIDEO] Nałożono blokadę na filmy do: {limit_time.strftime('%Y-%m-%d %H:%M:%S')}")

        video_blocked = True

    if video_blocked:
        logging.info("[VIDEO] Koniec cyklu (Wideo zablokowane - darmowe zebrane).")
        perform_anti_afk()
        return time.time() - start_time

    # --- 3. REKLAMY (Jeśli brak blokady) ---
    video_available = (
        check_exists("video_enabled.png")
        or check_exists("video_new.png")
        or check_exists("play_icon.png")
    )

    if not video_available:
        logging.info("[VIDEO] Brak wideo do odtworzenia. Koniec.")
        perform_anti_afk()
        time.sleep(1)
        return 0.0

    if not check_exists("play_icon.png"):
        if find_and_click_simple("video_enabled.png", retry=1, wait_after=2):
            pass
        elif find_and_click_simple("video_new.png", retry=1, wait_after=2):
            pass

        if check_exists("bonus_video_disabled.png"):
            logging.warning("[VIDEO] Wykryto limit po kliknięciu ikonki bocznej!")
            if check_exists("disable_video_limit.png"):
                find_and_click_simple("disable_video_limit.png", wait_after=1)

            server_name = getattr(settings, "ACTIVE_SERVER", "")
            limit_hour = 16 if "US102" in server_name else 14
            limit_time = now.replace(hour=limit_hour, minute=0, second=0, microsecond=0)
            if now >= limit_time:
                limit_time = limit_time + timedelta(days=1)
            watch_cycle.video_block_until = limit_time

            logging.info(f"[VIDEO] Nałożono blokadę na filmy do: {limit_time.strftime('%Y-%m-%d %H:%M:%S')}")
            perform_anti_afk()
            return time.time() - start_time

    logging.info("[VIDEO] Film 1: Start.")
    if not find_and_click_simple("play_icon.png", retry=5, wait_after=0, fallback_center=True):
        logging.warning("[VIDEO] Nie widzę Play. Koniec.")
        time.sleep(1)
        return 0.0

    if wait_for_button("watch_video.png", max_seconds=65):
        find_and_click_simple("watch_video.png", wait_after=2, fallback_center=True)

        logging.info("[VIDEO] Film 2: Start.")
        if not find_and_click_simple("play_icon.png", retry=5, wait_after=0, fallback_center=True):
            logging.warning("[VIDEO] Nie widzę Play (Film 2).")

        if wait_for_button("redeem.png", max_seconds=65):
            logging.info("[VIDEO] Odbieram nagrodę...")
            find_and_click_simple("redeem.png", retry=8, wait_after=2, fallback_center=True)
        else:
            logging.warning("[VIDEO] Nie pojawił się Redeem po 2. filmie.")
    else:
        if check_exists("redeem.png"):
            logging.info("[VIDEO] Wykryto Redeem. Odbieram.")
            find_and_click_simple("redeem.png", retry=8, wait_after=2, fallback_center=True)
        else:
            logging.info("[VIDEO] Brak przycisków. Próba ślepego kliku.")
            click_screen_center()
            time.sleep(2)

    time.sleep(1)

    if check_exists("lottery_png.png"):
        find_and_click_simple("close_lottery.png", wait_after=1)
    elif check_exists("lottery.png"):
        find_and_click_simple("close_lottery.png", wait_after=1)

    if check_exists("pollux.png"):
        find_and_click_simple("close_pollux.png")
    elif check_exists("no_gold_bonus.png"):
        find_and_click_simple("no_gold_bonus.png")

    logging.info("[VIDEO] Koniec cyklu.")
    return time.time() - start_time