# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import pyautogui
import logging
import time
import os
import settings
from modules import video_watcher

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

pyautogui.FAILSAFE = False

START_BOT = False
AUTO_START_TIMER = None


def setup_console_buffer():
    os.system("mode con: cols=140 lines=9000")
    os.system("title Rail Nation - Bonusy i Reklamy")


def get_gui_geometry():
    screen_w, screen_h = pyautogui.size()
    if screen_w == 3840:
        return "700x360+1570+700"
    elif screen_w == 1920 or screen_w == 1536:
        return "460x260+730+350"
    else:
        return "480x280+200+200"


def run_video_loop():
    logging.info(f"Bot uruchomiony (Serwer: {settings.ACTIVE_SERVER} | Tryb: Bonusy + Reklamy + Pollux).")
    while True:
        video_watcher.watch_cycle()
        time.sleep(5)


def start_gui(geometry):
    global START_BOT, AUTO_START_TIMER
    root = tk.Tk()
    root.title("Centrum Sterowania - Reklamy")
    if geometry:
        root.geometry(geometry)
    root.configure(bg="#2b2b2b")

    # --- MENU WYBORU SERWERA (Godzina resetu limitu reklam: 16:00 dla US102, 14:00 dla innych) ---
    tk.Label(
        root,
        text="Wybierz serwer (ustawia godzinę resetu reklam):",
        font=("Arial", 10, "bold"),
        fg="#aaa",
        bg="#2b2b2b"
    ).pack(pady=(20, 5))

    lista_serwerow = ["INT5402 Kap Arkona", "US102 Grand Central", "Serwer 3"]
    server_var = tk.StringVar()

    default_server = getattr(settings, "ACTIVE_SERVER", "INT5402 Kap Arkona")
    if default_server not in lista_serwerow:
        lista_serwerow.append(default_server)
    server_var.set(default_server)

    server_combo = ttk.Combobox(
        root,
        textvariable=server_var,
        values=lista_serwerow,
        state="readonly",
        width=33,
        font=("Arial", 11)
    )
    server_combo.pack(pady=(0, 15))

    def launch():
        global START_BOT
        if AUTO_START_TIMER:
            root.after_cancel(AUTO_START_TIMER)

        wybrany_serwer = server_var.get()
        settings.save_last_server(wybrany_serwer)

        print(f"[GUI] Serwer operacyjny: {wybrany_serwer}")
        START_BOT = True
        root.destroy()

    # --- AUTOSTART ---
    countdown_seconds = 600

    def update_countdown():
        nonlocal countdown_seconds
        countdown_seconds -= 1
        if countdown_seconds > 0:
            root.title(f"Autostart za {countdown_seconds}s...")
            global AUTO_START_TIMER
            AUTO_START_TIMER = root.after(1000, update_countdown)
        else:
            print("[GUI] Czas minął! Autostart zbierania bonusów i reklam.")
            launch()

    AUTO_START_TIMER = root.after(1000, update_countdown)

    tk.Label(
        root,
        text="Kliknij START (Autostart za 10 min):",
        font=("Arial", 11, "bold"),
        fg="white",
        bg="#2b2b2b"
    ).pack(pady=(5, 10))

    tk.Button(
        root,
        text="START (BONUSY + REKLAMY + POLLUX)",
        command=launch,
        font=("Arial", 11, "bold"),
        width=35,
        height=2,
        bg="#004400",
        fg="white"
    ).pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    setup_console_buffer()
    gui_geom = get_gui_geometry()
    try:
        start_gui(gui_geom)
    except Exception as e:
        print(f"[ERROR GUI] {e}")

    if START_BOT:
        print("--- Uruchamianie modułu bonusów i reklam... ---")
        try:
            run_video_loop()
        except KeyboardInterrupt:
            print("\nZatrzymano przez użytkownika.")
    else:
        print("Zamykanie.")