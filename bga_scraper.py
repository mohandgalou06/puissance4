

import csv
import undetected_chromedriver as uc
from selenium.common import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import re
import sys
from datetime import datetime
from database import DatabaseManager

# --- CONFIGURATION ---
INPUT_FILE = "comprehensive_match_links.txt"
HISTORY_FILE = "scraped_history.txt"
OUTPUT_CSV = "game_move_sequences.csv"
ROWS = 8
COLS = 9

# --- DATABASE INITIALIZATION ---
db = DatabaseManager(host="localhost", user="root", password="galou1646", database="puissance4")
db.connect()

def load_queue():
    if not os.path.exists(INPUT_FILE): return []
    with open(INPUT_FILE, "r") as f:
        # Clean the format "unknown,URL" or just "URL"
        return [line.strip().split(",")[-1] for line in f if line.strip()]


def move_to_history(url, status="SUCCESS"):
    """Removes URL from input file and adds it to history."""
    links = load_queue()
    remaining = [l for l in links if l != url]

    with open(INPUT_FILE, "w") as f:
        for l in remaining: f.write(f"unknown,{l}\n")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORY_FILE, "a") as f:
        f.write(f"[{timestamp}] [{status}] {url}\n")


def get_driver():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    user_data_path = os.path.join(script_dir, "profile")
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={user_data_path}")
    # options.add_argument("--headless") # Uncomment to run without a window
    return uc.Chrome(options=options, version_main=145)


def process_match(driver, table_url):
    """Core logic to scrape a single table and save to DB."""
    try:
        print(f"\n🚀 Processing: {table_url}")
        driver.get(table_url)

        # 1. Check if 9x9
        try:
            val = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "gameoption_100_displayed_value"))
            ).text
         #   if "9x9" not in val:
         #       print("⏭️ Skipped: Not 9x9.")
          #      move_to_history(table_url, "SKIPPED_NOT_9X9")
           #     return False
        except:
            print("❌ Could not verify board size.")
            return False

        # 2. Open Replay
        review_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "reviewgame")))
        driver.execute_script("arguments[0].click();", review_btn)

        # 3. Extract Moves
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "gamelogreview")))
        time.sleep(1)
        logs = driver.find_elements(By.CLASS_NAME, "gamelogreview")

        col_sequence = [int(re.search(r"(?:colonne|column)\s*(\d+)", entry.text.lower()).group(1)) - 1
                        for entry in logs if re.search(r"(?:colonne|column)\s*(\d+)", entry.text.lower())]

        if not col_sequence:
            print("⚠️ No moves found.")
            move_to_history(table_url, "FAILED_NO_MOVES")
            return False

        # 4. Database Check & Insert
        seq_str = ''.join(map(str, col_sequence))
        if db.check_if_sequence_exists(seq_str):
            print("♻️ Match already in DB.")
            move_to_history(table_url, "ALREADY_IN_DB")
            return True

        game_id = db.create_game(rows=ROWS, cols=COLS, mode=3, confidence=1)
        col_heights = [0] * COLS
        for i, col in enumerate(col_sequence):
            row = (ROWS - 1) - col_heights[col]
            if row >= 0:
                db.save_move(game_id, i + 1, row, col, (i % 2) + 1)
                col_heights[col] += 1

        db.update_game_result(game_id, winner=((len(col_sequence) - 1) % 2) + 1)

        # 5. Backup CSV
        with open(OUTPUT_CSV, "a", newline='') as f:
            csv.writer(f).writerow([table_url, "-".join(map(str, col_sequence))])

        print(f"✅ Saved to DB: Match ID {game_id}")
        move_to_history(table_url, "SUCCESS")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    driver = get_driver()

    try:
        print("Checking BGA login...")
        driver.get("https://en.boardgamearena.com/account")
        WebDriverWait(driver, 600).until(lambda d: "account" not in d.current_url)

        # MISSION 4.1: Manual ID Check
        if len(sys.argv) > 1:
            match_id = sys.argv[1]
            url = f"https://boardgamearena.com/table?table={match_id}"
            process_match(driver, url)
        else:
            # QUEUE MODE
            print("Starting Automatic Queue processing...")
            while True:
                links = load_queue()
                if not links:
                    print("Queue empty! Finished.")
                    break

                success = process_match(driver, links[0])
                if not success:
                    time.sleep(2)  # Prevent spamming on error

    except KeyboardInterrupt:
        print("\nStopping script...")
    finally:
        driver.quit()