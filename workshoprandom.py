import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import requests
from bs4 import BeautifulSoup
import random
import threading
import os
from urllib.parse import quote

# --- Configuration ---
GAMES_DB = {
    "Left 4 Dead 2": {
        "appid": "550",
        "categories": {
            "Survivors": ["Survivors", "Bill", "Francis", "Louis", "Zoey", "Coach", "Ellis", "Nick", "Rochelle"],
            "Infected": ["Common Infected", "Special Infected", "Boomer", "Charger", "Hunter", "Jockey", "Smoker", "Spitter", "Tank", "Witch"],
            "Game Content": ["Campaigns", "Weapons", "Items", "Sounds", "Scripts", "UI", "Miscellaneous", "Models", "Textures"],
            "Game Modes": ["Single Player", "Co-op", "Versus", "Scavenge", "Survival", "Realism", "Realism Versus", "Mutations"],
            "Weapons": ["Grenade Launcher", "M60", "Melee", "Pistol", "Rifle", "Shotgun", "SMG", "Sniper", "Throwable"],
            "Items": ["Adrenaline", "Defibrillator", "Medkit", "Pills", "Other"]
        }
    },
    "Garry's Mod": {
        "appid": "4000",
        "categories": {
            "Content Type": ["Addon", "Save", "Dupe", "Demo"],
            "Addon Type": ["Gamemode", "Map", "Weapon", "Vehicle", "NPC", "Tool", "Entity", "Effects", "Model", "Server content"],
            "Addon Tags": ["Build", "Cartoon", "Comic", "Fun", "Movie", "Roleplay", "Scenic", "Realism", "Water"],
            "Dupe Tags": ["Buildings", "Machines", "Posed", "Scenes", "Vehicles", "Other"],
            "Save Tags": ["Buildings", "Courses"]
        }
    },
    "Counter-Strike 2": {
        "appid": "730",
        "categories": {
            "Game Mode": ["Classic", "Deathmatch", "Demolition", "Armsrace", "Custom", "Training", "Co-op Strike", "Wingman", "Flying Scoutsman"]
        }
    }, 
    "Source Filmmaker": {
        "appid": "1840",
        "categories": {
            "Universe": ["Half-Life", "Team Fortress", "Portal", "Left 4 Dead", "Dota", "Counter-Strike", "Day Of Defeat", "Richochet", "Alien Swarm", "Blade Symphony", "Dino D-Day", "Original IP", "The Stanley Parable"],
            "Models": ["Model","Characters","Weapon", "Clothing", "Creature", "Vehicle","Architecture","Industrial","Hand-held","Indoor","Outdoor"],
            "Sounds": ["Sound", "Dialogue", "Music", "Effects"],
            "Other": ["Map", "Particle", "Script", "Material", "Texture", "Session","Shot","Animation"]
        }
    }
}

SINGLE_CHOICE_CATEGORIES = ["Content Type", "Universe", "Models", "Sounds"]

class WorkshopRandomizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Coinflip Workshop")
        self.root.geometry("390x555")

        # --- Set Icon for Main Window ---
        try:
            self.root.iconbitmap("res/coinflip.ico")
        except Exception as e:
            print(f"[DEBUG] Could not load icon: {e}")

        # --- Settings Variables (Default Values) ---
        self.max_pages_var = tk.IntVar(value=1000)
        self.max_attempts_var = tk.IntVar(value=5)
        self.search_text_var = tk.StringVar(value="") 
        self.save_to_file_var = tk.BooleanVar(value=False)

        # LOAD CONFIG FROM FILE
        self.load_config()

        self.tag_vars = {}

        tk.Label(root, text="Coinflip Workshop", font=("Helvetica", 16, "bold")).pack(pady=10)

        # 1. Game Selector
        tk.Label(root, text="Select Game:").pack()
        self.game_var = tk.StringVar()
        self.game_combo = ttk.Combobox(root, textvariable=self.game_var, state="readonly")
        self.game_combo['values'] = list(GAMES_DB.keys())
        self.game_combo.pack(pady=5)
        self.game_combo.bind("<<ComboboxSelected>>", self.reset_and_update)

        # 2. Category Group Selector
        tk.Label(root, text="Category Group:").pack()
        self.cat_var = tk.StringVar()
        self.cat_combo = ttk.Combobox(root, textvariable=self.cat_var, state="readonly")
        self.cat_combo.pack(pady=5)
        self.cat_combo.bind("<<ComboboxSelected>>", self.draw_tag_buttons)

        # 3. Active Selections Display
        self.tag_label = tk.Label(root, text="Active Selections: 0", font=("Helvetica", 10, "bold"), fg="#2a475e")
        self.tag_label.pack(pady=(10, 0))
        
        # 4. Button Container
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=10, padx=20)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Clear All Selections", command=self.clear_all_selections).grid(row=0, column=0, padx=5)

        self.search_btn = tk.Button(root, text="Find Random Item & Open", command=self.start_search_thread, 
                                    bg="#2a475e", fg="white", font=("Arial", 11, "bold"), padx=25, pady=10)
        self.search_btn.pack(pady=20)

        footer_frame = tk.Frame(root)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.settings_btn = tk.Button(footer_frame, text="⚙ Settings", command=self.open_settings, font=("Arial", 9))
        self.settings_btn.pack(side=tk.LEFT)

        self.about_btn = tk.Button(footer_frame, text="ℹ About", command=self.open_about, font=("Arial", 9))
        self.about_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(footer_frame, text="Ready", fg="gray")
        self.status_label.pack(side=tk.RIGHT)

    def load_config(self):
        """Loads all settings from config.txt"""
        if os.path.exists("config.txt"):
            try:
                with open("config.txt", "r") as f:
                    lines = f.read().splitlines()
                    if len(lines) >= 1:
                        self.save_to_file_var.set(lines[0] == "1")
                    if len(lines) >= 2:
                        self.max_pages_var.set(int(lines[1]))
                    if len(lines) >= 3:
                        self.max_attempts_var.set(int(lines[2]))
                print("[DEBUG] Config loaded successfully")
            except Exception as e:
                print(f"[DEBUG] Error loading config: {e}")

    def save_config(self):
        """Saves current settings to config.txt"""
        try:
            with open("config.txt", "w") as f:
                f.write("1\n" if self.save_to_file_var.get() else "0\n")
                f.write(f"{self.max_pages_var.get()}\n")
                f.write(f"{self.max_attempts_var.get()}\n")
            print("[DEBUG] Config saved successfully")
        except Exception as e:
            print(f"[DEBUG] Error saving config: {e}")

    def open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Search Settings")
        settings_win.geometry("280x320")
        settings_win.resizable(False, False)
        
        # --- Set Icon for Settings Window ---
        try:
            settings_win.iconbitmap("res/coinflip.ico")
        except:
            pass

        settings_win.grab_set()

        tk.Label(settings_win, text="Search Configuration", font=("Arial", 10, "bold")).pack(pady=10)
        tk.Label(settings_win, text="Search for specific word/phrase:").pack()
        tk.Entry(settings_win, textvariable=self.search_text_var, width=30).pack(pady=5)
        
        tk.Label(settings_win, text="Max Search Pages (1 - 9999):").pack()
        tk.Entry(settings_win, textvariable=self.max_pages_var).pack(pady=5)
        
        tk.Label(settings_win, text="Max Retries (if page empty):").pack()
        tk.Entry(settings_win, textvariable=self.max_attempts_var).pack(pady=5)

        tk.Checkbutton(settings_win, text="Save found links to Documents", 
                       variable=self.save_to_file_var).pack(pady=10)

        # Save and Close button
        tk.Button(settings_win, text="Save & Close", 
                  command=lambda: [self.save_config(), settings_win.destroy()], 
                  bg="#66c0f4", width=15).pack(pady=10)

    def open_about(self):
        about_win = tk.Toplevel(self.root)
        about_win.title("About")
        about_win.geometry("300x320")
        about_win.resizable(False, False)

        # --- Set Icon for About Window ---
        try:
            about_win.iconbitmap("res/coinflip.ico")
        except:
            pass

        about_win.grab_set()
        tk.Label(about_win, text="About Coinflip Workshop", font=("Arial", 10, "bold")).pack(pady=15)
        dummy_text = "Steam Workshop Multi-Tag Randomizer Tool\n\nVersion: 1.1\n\nThe Fun 2026\nhttps://thenonfun.neocities.org \n\nDeveloped with Python\nCode mostly generated by Gemini"
        tk.Label(about_win, text=dummy_text, justify=tk.CENTER).pack(padx=20, pady=10)
        tk.Button(about_win, text="Close", command=about_win.destroy).pack(pady=15)

    def reset_and_update(self, event):
        game = self.game_var.get()
        self.tag_vars = {}
        if game in GAMES_DB:
            cats = list(GAMES_DB[game]["categories"].keys())
            self.cat_combo['values'] = cats
            self.cat_combo.current(0)
            self.draw_tag_buttons(None)

    def clear_all_selections(self):
        for var in self.tag_vars.values():
            var.set(False)
        self.update_selection_count()

    def update_selection_count(self):
        count = sum(1 for var in self.tag_vars.values() if var.get())
        self.tag_label.config(text=f"Active Selections: {count}")

    def handle_tag_click(self, cat, tag):
        state = self.tag_vars[(cat, tag)].get()
        if cat in SINGLE_CHOICE_CATEGORIES:
            if state:
                for (c, t), var in self.tag_vars.items():
                    if c == cat and t != tag:
                        var.set(False)
        self.update_selection_count()

    def draw_tag_buttons(self, event):
        cat = self.cat_var.get()
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        game = self.game_var.get()
        if game in GAMES_DB and cat in GAMES_DB[game]["categories"]:
            tags = GAMES_DB[game]["categories"][cat]
            cols = 3
            for i in range(cols):
                self.button_frame.grid_columnconfigure(i, weight=1)

            for index, tag in enumerate(tags):
                key = (cat, tag)
                if key not in self.tag_vars:
                    self.tag_vars[key] = tk.BooleanVar(value=False)

                cb = tk.Checkbutton(
                    self.button_frame, text=tag, variable=self.tag_vars[key],
                    indicatoron=False, relief="raised", selectcolor="#66c0f4", width=17,
                    command=lambda c=cat, t=tag: self.handle_tag_click(c, t)
                )
                cb.grid(row=index // cols, column=index % cols, padx=5, pady=5)

    def start_search_thread(self):
        game = self.game_var.get()
        if not game:
            messagebox.showwarning("Warning", "Please select a game.")
            return
        
        self.search_btn.config(state="disabled", text="Searching Workshop...")
        
        pages = self.max_pages_var.get()
        attempts = self.max_attempts_var.get()
        keyword = self.search_text_var.get()
        
        threading.Thread(target=self.perform_deep_search, args=(game, pages, attempts, keyword), daemon=True).start()

    def perform_deep_search(self, game_name, max_page_limit, attempts_left, keyword):
        try:
            if attempts_left <= 0:
                self.reset_ui("No items found matching criteria.")
                return

            app_id = GAMES_DB[game_name]["appid"]
            active_tags = [tag for (cat, tag), var in self.tag_vars.items() if var.get()]
            
            tag_params = "".join([f"&requiredtags[]={quote(t)}" for t in active_tags])
            text_param = f"&searchtext={quote(keyword)}" if keyword else ""
            
            self.update_status("Determining search range...")
            base_url = f"https://steamcommunity.com/workshop/browse/?appid={app_id}{tag_params}{text_param}&browsesort=trend"
            
            headers = {"User-Agent": "Mozilla/5.0"}
            initial_res = requests.get(base_url, headers=headers, timeout=10)
            initial_soup = BeautifulSoup(initial_res.text, 'html.parser')
            
            paging_links = initial_soup.find_all('a', class_='pagelink')
            if paging_links:
                last_page_actual = int(paging_links[-1].text.replace(',', ''))
                effective_max_page = min(max_page_limit, last_page_actual)
            else:
                effective_max_page = 1 
            
            random_page = random.randint(1, effective_max_page)
            url = f"{base_url}&p={random_page}"
            
            self.update_status(f"Scanning Page {random_page}...")
            
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            items = []
            for div in soup.find_all('div', class_='workshopItem'):
                link_tag = div.find('a', class_='ugc', href=True)
                if link_tag:
                    items.append(link_tag['href'])

            if not items:
                self.perform_deep_search(game_name, max_page_limit, attempts_left - 1, keyword)
                return

            final_url = random.choice(items).split('&')[0]
            
            if self.save_to_file_var.get():
                try:
                    docs_path = os.path.join(os.path.expanduser("~"), "Documents")
                    file_path = os.path.join(docs_path, "workshop_links.txt")
                    with open(file_path, "a", encoding="utf-8") as f:
                        f.write(f"{final_url}\n")
                except Exception as file_err:
                    print(f"[DEBUG] File save error: {file_err}")

            webbrowser.open(final_url)
            self.reset_ui(f"Found something!")
                
        except Exception as e:
            self.reset_ui("Search Error.")

    def update_status(self, text):
        self.root.after(0, lambda: self.status_label.config(text=text))

    def reset_ui(self, status_text):
        self.root.after(0, lambda: self.search_btn.config(state="normal", text="Find Random Item & Open"))
        self.root.after(0, lambda: self.status_label.config(text=status_text))

if __name__ == "__main__":
    root = tk.Tk()
    app = WorkshopRandomizerApp(root)
    root.mainloop()