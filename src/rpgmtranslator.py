import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import os
import re
import json
import concurrent.futures
import queue
import threading
from deep_translator import GoogleTranslator
from itertools import cycle
from typing import Dict, List, Tuple

class RPGMakerTranslator:
    def __init__(self, root):
        self.root = root
        self.root.title("RPG Maker MV Turbo Translator")
        self.root.geometry("1200x800")
        self.running = False
        self.total_files = 0
        self.processed_files = 0

        # RPG Maker MV özel desenleri
        self.code_patterns = [
            r'(if|en)\([\w \=\[\]\&<>\|\.\$\_\+\-\*\/\@\!]+\)',
            r'(\\[a-zA-Z0-9]+\[.*?\])+',
            r'(\\[a-zA-Z0-9]+<.*?>)+',
            r'(\\[a-zA-Z\{\}\\\$\.\|\!\><\^])+',
            r'(\@[0-9]+)+',
            r'(?<=\{)(.*?)(?=\})',
            r'(?<=\[)(.*?)(?=\])',
            r'(?<=<)(.*?)(?=>)',
            r'((#|%)+\w+)|(\w+(#|%)+)|((#|%)+\([a-zA-Z]+\))+',
            r'(\w+_\w+)|(_+\w+)|(\w+_)',
            r'[a-zA-Z\/\\\=\_0-9]+(\.)+(ttf|otf|png|mp3|mp4|ogg|wav|jpg|webm|avi|webp)',
            r'\\[a-zA-Z0-9]+'
        ]
        
        self.translatable_json_fields = [
            'parameters', 'description', 'message', 'text', 'help', 'nickname',
            'intro', 'title', 'caption', 'skillName', 'itemName', 'terms',
            'actor', 'item', 'skill', 'equipment', 'level', 'currencyUnit',
            'profile'
        ]
        
        # Çeviri için hedef dil desteği (örneğin GoogleTranslator için)
        self.target_language = tk.StringVar(value='Türkçe')
        self.languages = {
            'Türkçe': 'tr',
            'español': 'es',
            'English': 'en',
            'Afrikaans': 'af',
            'shqip': 'sq',
            'አማርኛ': 'am',
            'العربية': 'ar',
            'հայերեն': 'hy',
            'azərbaycan dili': 'az',
            'euskara': 'eu',
            'беларуская': 'be',
            'বাংলা': 'bn',
            'bosanski': 'bs',
            'български': 'bg',
            'català': 'ca',
            'Sinugbuanong Binisaya': 'ceb',
            'Chichewa': 'ny',
            '简体中文': 'zh-CN',
            '繁體中文': 'zh-TW',
            'corsu': 'co',
            'hrvatski': 'hr',
            'čeština': 'cs',
            'dansk': 'da',
            'Nederlands': 'nl',
            'Esperanto': 'eo',
            'eesti': 'et',
            'Filipino': 'tl',
            'suomi': 'fi',
            'français': 'fr',
            'Frysk': 'fy',
            'galego': 'gl',
            'ქართული': 'ka',
            'Deutsch': 'de',
            'Ελληνικά': 'el',
            'ગુજરાતી': 'gu',
            'Kreyòl ayisyen': 'ht',
            'Hausa': 'ha',
            'ʻŌlelo Hawaiʻi': 'haw',
            'עברית': 'he',
            'हिन्दी': 'hi',
            'Hmoob': 'hmn',
            'magyar': 'hu',
            'íslenska': 'is',
            'Igbo': 'ig',
            'Bahasa Indonesia': 'id',
            'Gaeilge': 'ga',
            'Italiano': 'it',
            '日本語': 'ja',
            'Basa Jawa': 'jw',
            'ಕನ್ನಡ': 'kn',
            'қазақ тілі': 'kk',
            'ខ្មែរ': 'km',
            '한국어': 'ko',
            'кыргызча': 'ky',
            'ພາສາລາວ': 'lo',
            'Latina': 'la',
            'latviešu': 'lv',
            'lietuvių': 'lt',
            'Lëtzebuergesch': 'lb',
            'македонски': 'mk',
            'Malagasy': 'mg',
            'Bahasa Melayu': 'ms',
            'മലയാളം': 'ml',
            'Malti': 'mt',
            'Māori': 'mi',
            'मराठी': 'mr',
            'Монгол': 'mn',
            'မြန်မာဘာသာ': 'my',
            'नेपाली': 'ne',
            'norsk': 'no',
            'پښتو': 'ps',
            'فارسی': 'fa',
            'polski': 'pl',
            'português': 'pt',
            'ਪੰਜਾਬੀ': 'pa',
            'română': 'ro',
            'русский': 'ru',
            'Gagana Samoa': 'sm',
            'Gàidhlig': 'gd',
            'српски': 'sr',
            'Sesotho': 'st',
            'chiShona': 'sn',
            'سنڌي': 'sd',
            'සිංහල': 'si',
            'slovenčina': 'sk',
            'slovenščina': 'sl',
            'Soomaali': 'so',
            'Basa Sunda': 'su',
            'Kiswahili': 'sw',
            'svenska': 'sv',
            'тоҷикӣ': 'tg',
            'தமிழ்': 'ta',
            'తెలుగు': 'te',
            'ไทย': 'th',
            'українська': 'uk',
            'اردو': 'ur',
            'O‘zbek': 'uz',
            'Tiếng Việt': 'vi',
            'Cymraeg': 'cy',
            'isiXhosa': 'xh',
            'ייִדיש': 'yi',
            'Yorùbá': 'yo',
            'isiZulu': 'zu'
        }
        
        # Arayüz dili seçenekleri için (sınırlı liste, yalnızca arayüz metinleri)
        self.interface_language = tk.StringVar(value="English")
        self.interface_texts = {
            "Türkçe": {
                "interface_lang_label": "Arayüz Dili:",
                "target_label": "Hedef Dil:",
                "proxy_list_label": "Proxy Listesi:",
                "load_proxy_button": "Yükle",
                "active_proxy_label": "Aktif Proxy: Yok",
                "exe_button": "EXE Seç",
                "exe_label": "Seçilen EXE: Yok",
                "start_translation_button": "ÇEVİRİYİ BAŞLAT",
                "tree_column_file": "Dosya Adı",
                "tree_column_status": "Durum",
                "tree_column_progress": "İlerleme",
                "made_by": "Made by HAN"
            },
            "English": {
                "interface_lang_label": "Interface Language:",
                "target_label": "Target Language:",
                "proxy_list_label": "Proxy List:",
                "load_proxy_button": "Load",
                "active_proxy_label": "Active Proxy: None",
                "exe_button": "Select EXE",
                "exe_label": "Selected EXE: None",
                "start_translation_button": "START TRANSLATION",
                "tree_column_file": "File Name",
                "tree_column_status": "Status",
                "tree_column_progress": "Progress",
                "made_by": "Made by HAN"
            },
            "Deutsch": {
                "interface_lang_label": "Oberflächensprache:",
                "target_label": "Zielsprache:",
                "proxy_list_label": "Proxy-Liste:",
                "load_proxy_button": "Laden",
                "active_proxy_label": "Aktiver Proxy: Keiner",
                "exe_button": "EXE wählen",
                "exe_label": "Gewähltes EXE: Keines",
                "start_translation_button": "ÜBERSETZUNG STARTEN",
                "tree_column_file": "Dateiname",
                "tree_column_status": "Status",
                "tree_column_progress": "Fortschritt",
                "made_by": "Made by HAN"
            },
            "Français": {
                "interface_lang_label": "Langue de l'interface:",
                "target_label": "Langue cible:",
                "proxy_list_label": "Liste des Proxy:",
                "load_proxy_button": "Charger",
                "active_proxy_label": "Proxy actif: Aucun",
                "exe_button": "Sélectionner EXE",
                "exe_label": "EXE sélectionné: Aucun",
                "start_translation_button": "DÉMARRER LA TRADUCTION",
                "tree_column_file": "Nom de fichier",
                "tree_column_status": "Statut",
                "tree_column_progress": "Progression",
                "made_by": "Made by HAN"
            },
            "Español": {
                "interface_lang_label": "Idioma de la interfaz:",
                "target_label": "Idioma objetivo:",
                "proxy_list_label": "Lista de Proxy:",
                "load_proxy_button": "Cargar",
                "active_proxy_label": "Proxy activo: Ninguno",
                "exe_button": "Seleccionar EXE",
                "exe_label": "EXE seleccionado: Ninguno",
                "start_translation_button": "INICIAR LA TRADUCCIÓN",
                "tree_column_file": "Nombre de archivo",
                "tree_column_status": "Estado",
                "tree_column_progress": "Progreso",
                "made_by": "Made by HAN"
            },
            "Italiano": {
                "interface_lang_label": "Lingua dell'interfaccia:",
                "target_label": "Lingua di destinazione:",
                "proxy_list_label": "Elenco Proxy:",
                "load_proxy_button": "Carica",
                "active_proxy_label": "Proxy attivo: Nessuno",
                "exe_button": "Seleziona EXE",
                "exe_label": "EXE selezionato: Nessuno",
                "start_translation_button": "AVVIA TRADUZIONE",
                "tree_column_file": "Nome del file",
                "tree_column_status": "Stato",
                "tree_column_progress": "Progresso",
                "made_by": "Made by HAN"
            },
            "Русский": {
                "interface_lang_label": "Язык интерфейса:",
                "target_label": "Целевой язык:",
                "proxy_list_label": "Список Proxy:",
                "load_proxy_button": "Загрузить",
                "active_proxy_label": "Активный Proxy: Нет",
                "exe_button": "Выбрать EXE",
                "exe_label": "Выбранный EXE: Нет",
                "start_translation_button": "НАЧАТЬ ПЕРЕВОД",
                "tree_column_file": "Имя файла",
                "tree_column_status": "Статус",
                "tree_column_progress": "Прогресс",
                "made_by": "Made by HAN"
            }
        }
        
        # Çeviri önbelleği
        self.cache_file = 'rpg_translation_cache.json'
        self.translation_cache = self.load_cache()
        
        self.proxy_list = []
        self.good_proxies = []
        self.bad_proxies = []
        self.proxy_cycle = None
        self.max_workers = os.cpu_count() * 8
        self.placeholder_cycle = cycle([f"§{i}§" for i in range(1000)])
        self.progress_queue = queue.Queue()
        self.file_status = {}
        
        self.setup_ui()
        self.setup_styles()
        self.root.after(50, self.update_progress)

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(padx=10, pady=10, fill='both', expand=True)

        # Üst kontrol çerçevesi: Arayüz dili, hedef dil, proxy vb.
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill='x', pady=5)

        # Arayüz Dili Seçimi
        interface_frame = ttk.Frame(control_frame)
        interface_frame.pack(side='left', padx=5)
        ttk.Label(interface_frame, text=self.interface_texts[self.interface_language.get()]["interface_lang_label"]).pack(side='left')
        self.interface_language_combo = ttk.Combobox(
            interface_frame,
            textvariable=self.interface_language,
            values=list(self.interface_texts.keys()),
            state="readonly",
            width=15
        )
        self.interface_language_combo.pack(side='left', padx=5)
        self.interface_language_combo.bind("<<ComboboxSelected>>", self.update_interface_texts)

        # Hedef Dil Seçimi
        lang_frame = ttk.Frame(control_frame)
        lang_frame.pack(side='left', padx=5)
        self.target_label = ttk.Label(lang_frame, text=self.interface_texts[self.interface_language.get()]["target_label"])
        self.target_label.pack(side='left')
        self.lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.target_language,
            values=list(self.languages.keys()),
            state='readonly',
            width=15
        )
        self.lang_combo.pack(side='left', padx=5)
        self.lang_combo.current(0)
        
        # Proxy Bölümü
        proxy_frame = ttk.Frame(control_frame)
        proxy_frame.pack(side='left', padx=5)
        self.proxy_list_label = ttk.Label(proxy_frame, text=self.interface_texts[self.interface_language.get()]["proxy_list_label"])
        self.proxy_list_label.pack(side='left')
        self.proxy_text = scrolledtext.ScrolledText(proxy_frame, height=3, width=30)
        self.proxy_text.pack(side='left', padx=5)
        ttk.Button(proxy_frame, text=self.interface_texts[self.interface_language.get()]["load_proxy_button"], command=self.load_proxies).pack(side='left', padx=5)
        self.proxy_status = ttk.Label(proxy_frame, text=self.interface_texts[self.interface_language.get()]["active_proxy_label"])
        self.proxy_status.pack(side='left', padx=5)

        # EXE Seçimi
        file_frame = ttk.Frame(control_frame)
        file_frame.pack(side='left', padx=5)
        ttk.Button(file_frame, text=self.interface_texts[self.interface_language.get()]["exe_button"], command=self.select_exe).pack()
        self.folder_label = ttk.Label(file_frame, text=self.interface_texts[self.interface_language.get()]["exe_label"])
        self.folder_label.pack()

        # Dosya Listesi (Treeview)
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill='both', expand=True, pady=5)
        self.tree = ttk.Treeview(tree_frame, columns=('Dosya', 'Durum', 'İlerleme'), show='headings')
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.heading('Dosya', text=self.interface_texts[self.interface_language.get()]["tree_column_file"])
        self.tree.heading('Durum', text=self.interface_texts[self.interface_language.get()]["tree_column_status"])
        self.tree.heading('İlerleme', text=self.interface_texts[self.interface_language.get()]["tree_column_progress"])
        self.tree.column('Dosya', width=400, anchor='w')
        self.tree.column('Durum', width=150, anchor='center')
        self.tree.column('İlerleme', width=100, anchor='center')
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Konsol Alanı
        self.console = scrolledtext.ScrolledText(main_frame, height=10, bg='#000000', fg='#00FFFF')
        self.console.pack(fill='both', expand=True, pady=5)

        # Çeviriyi Başlat Butonu ve "Made by" etiketi
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=5)
        self.start_translation_button = ttk.Button(button_frame, text=self.interface_texts[self.interface_language.get()]["start_translation_button"], command=self.start_translation_thread)
        self.start_translation_button.pack(side='left', padx=5)
        self.made_by_label = tk.Label(button_frame, text=self.interface_texts[self.interface_language.get()]["made_by"], fg='gray', bg='#000000')
        self.made_by_label.pack(side='right', padx=5)

    def update_interface_texts(self, event=None):
        lang = self.interface_language.get()
        texts = self.interface_texts[lang]
        # Güncelleme: arayüz dil etiketi (combo'da görünmese de diğer widgetlarda kullanılacak)
        self.target_label.config(text=texts["target_label"])
        self.proxy_list_label.config(text=texts["proxy_list_label"])
        self.proxy_status.config(text=texts["active_proxy_label"])
        self.start_translation_button.config(text=texts["start_translation_button"])
        self.made_by_label.config(text=texts["made_by"])
        # EXE seçimi
        self.folder_label.config(text=texts["exe_label"])
        # Treeview başlıkları
        self.tree.heading('Dosya', text=texts["tree_column_file"])
        self.tree.heading('Durum', text=texts["tree_column_status"])
        self.tree.heading('İlerleme', text=texts["tree_column_progress"])
        # Proxy butonu
        # (load_proxy_button metnini de güncelleyelim; eğer varsa)
        for child in self.proxy_list_label.master.winfo_children():
            if isinstance(child, ttk.Button):
                child.config(text=texts["load_proxy_button"])
        # EXE butonu
        for child in self.folder_label.master.winfo_children():
            if isinstance(child, ttk.Button):
                child.config(text=texts["exe_button"])

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Varolan stiller...
        style.configure('TFrame', background='#000000')
        style.configure('TButton', foreground='#00FFFF', background='#000000', font=('Helvetica', 10, 'bold'))
        style.map('TButton', background=[('active', '#1a1a1a')])
        style.configure('TLabel', background='#000000', foreground='#00FFFF', font=('Helvetica', 10))
        style.configure('TEntry', fieldbackground='#000000', background='#000000', foreground='#00FFFF')
        style.configure('TCombobox', fieldbackground='#000000', background='#000000', foreground='#00FFFF')
        style.configure('Treeview', background='#000000', fieldbackground='#000000', foreground='#00FFFF', font=('Helvetica', 10))
        style.configure("Treeview.Heading", background='#000000', foreground='#00FFFF')
        
        # Yeni scrollbar stili (yatay ve dikey)
        style.configure("Vertical.TScrollbar", background="#000000", troughcolor="#000000", arrowcolor="#00FFFF")
        style.configure("Horizontal.TScrollbar", background="#000000", troughcolor="#000000", arrowcolor="#00FFFF")
        
        self.root.config(bg="#000000")


    
    def load_proxies(self):
        try:
            self.proxy_list = self.proxy_text.get("1.0", tk.END).splitlines()
            self.proxy_list = [p.strip() for p in self.proxy_list if p.strip()]
            
            if self.proxy_list:
                self.good_proxies = self.proxy_list.copy()
                self.bad_proxies = []
                self.proxy_cycle = cycle(self.good_proxies)
                self.log(f"Yüklendi: {len(self.proxy_list)} proxy")
                self.proxy_status.config(text=f"{self.interface_texts[self.interface_language.get()]['active_proxy_label']} {self.good_proxies[0]}")
            else:
                self.log("Proxy bulunamadı! Direkt bağlantı kullanılacak")
                self.proxy_status.config(text=self.interface_texts[self.interface_language.get()]["active_proxy_label"])
        except Exception as e:
            self.log(f"Proxy yükleme hatası: {str(e)}")

    def select_exe(self):
        exe_path = filedialog.askopenfilename(
            title="Oyun EXE'sini seçin",
            filetypes=(("Executable files", "*.exe"), ("All files", "*.*"))
        )
        if exe_path:
            base_dir = os.path.dirname(exe_path)
            # İlk olarak www/data klasörünü kontrol et
            data_path = os.path.join(base_dir, 'www', 'data')
            # Eğer www/data yoksa, exe'nin bulunduğu dizindeki data klasörünü kontrol et
            if not os.path.exists(data_path):
                data_path = os.path.join(base_dir, 'data')
            if os.path.exists(data_path):
                self.folder_path = data_path
                self.folder_label.config(text=f"Seçilen EXE: {exe_path}")
                self.populate_file_tree()
            else:
                messagebox.showerror("Hata", "www/data veya data klasörü bulunamadı!")

    def populate_file_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.file_status = {}
        for root_dir, _, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith(('.json', '.js')):
                    self.tree.insert('', 'end', values=(file, 'Bekliyor', '%0'))
                    self.file_status[file] = {'status': 'Bekliyor', 'progress': 0}

    def log(self, message):
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)

    def update_progress(self):
        try:
            while not self.progress_queue.empty():
                msg_type, content = self.progress_queue.get_nowait()
                if msg_type == 'progress':
                    file_name, progress, status = content
                    self.update_file_status(file_name, progress, status)
                elif msg_type == 'log':
                    self.log(content)
                elif msg_type == 'error':
                    self.log(f"Kritik Hata: {content}")
        except queue.Empty:
            pass
        self.root.after(50, self.update_progress)

    def process_text(self, text: str) -> Tuple[str, Dict]:
        replacements = {}
        for pattern in self.code_patterns:
            for match in re.finditer(pattern, text):
                placeholder = next(self.placeholder_cycle)
                replacements[placeholder] = match.group(0)
                text = text.replace(match.group(0), placeholder, 1)
        return text, replacements

    def translate_text(self, text: str) -> str:
        target_lang = self.languages[self.target_language.get()]
        retries = 3
        
        for attempt in range(retries):
            proxy = next(self.proxy_cycle) if self.proxy_cycle else None
            try:
                translator = GoogleTranslator(
                    source='auto',
                    target=target_lang,
                    proxies={'http': proxy, 'https': proxy} if proxy else None,
                    timeout=10
                )
                translated = translator.translate(text)
                if proxy and proxy in self.good_proxies:
                    self.good_proxies.remove(proxy)
                    self.good_proxies.insert(0, proxy)
                return translated
            except Exception as e:
                if proxy:
                    self.bad_proxies.append(proxy)
                    if proxy in self.good_proxies:
                        self.good_proxies.remove(proxy)
                self.log(f"Çeviri hatası (deneme {attempt+1}/{retries}): {str(e)}")
        return text

    def load_cache(self) -> Dict:
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)

    def get_output_path(self, original_path):
        relative_path = os.path.relpath(original_path, self.folder_path)
        translated_path = os.path.join(
            os.path.dirname(self.folder_path),
            'translated',
            relative_path
        )
        os.makedirs(os.path.dirname(translated_path), exist_ok=True)
        return translated_path

    def translate_json_file(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            def process_item(item):
                if isinstance(item, dict):
                    for key in list(item.keys()):
                        if key in self.translatable_json_fields:
                            if key == 'parameters' and item.get("code") == 401:
                                continue
                            elif isinstance(item[key], str):
                                processed, replacements = self.process_text(item[key])
                                if processed in self.translation_cache:
                                    item[key] = self.restore_code(self.translation_cache[processed], replacements)
                                else:
                                    translated = self.translate_text(processed)
                                    self.translation_cache[processed] = translated
                                    item[key] = self.restore_code(translated, replacements)
                        else:
                            process_item(item[key])
                elif isinstance(item, list):
                    process_list(item)

            def process_list(lst):
                i = 0
                while i < len(lst):
                    if (isinstance(lst[i], dict)
                        and lst[i].get("code") == 401
                        and isinstance(lst[i].get("parameters"), list)
                        and len(lst[i]["parameters"]) > 0
                        and isinstance(lst[i]["parameters"][0], str)):
                        group = [lst[i]]
                        base_indent = lst[i].get("indent")
                        j = i + 1
                        while (j < len(lst)
                            and isinstance(lst[j], dict)
                            and lst[j].get("code") == 401
                            and lst[j].get("indent") == base_indent
                            and isinstance(lst[j].get("parameters"), list)
                            and len(lst[j]["parameters"]) > 0
                            and isinstance(lst[j]["parameters"][0], str)):
                            group.append(lst[j])
                            j += 1
                        if len(group) > 1:
                            marker = "X_SPLIT_X"
                            original_texts = [cmd["parameters"][0] for cmd in group]
                            merged_text = marker.join(original_texts)
                            processed, replacements = self.process_text(merged_text)
                            if processed in self.translation_cache:
                                merged_translated = self.translation_cache[processed]
                            else:
                                merged_translated = self.translate_text(processed)
                                self.translation_cache[processed] = merged_translated
                            merged_translated = self.restore_code(merged_translated, replacements)
                            splitted = re.split(rf'\s*{re.escape(marker)}\s*', merged_translated)
                            splitted = [s.strip() for s in splitted if s.strip()]
                            if len(splitted) == len(group):
                                for k, cmd in enumerate(group):
                                    cmd["parameters"][0] = splitted[k]
                            else:
                                for cmd in group:
                                    text = cmd["parameters"][0]
                                    proc, repl = self.process_text(text)
                                    if proc in self.translation_cache:
                                        trans = self.translation_cache[proc]
                                    else:
                                        trans = self.translate_text(proc)
                                        self.translation_cache[proc] = trans
                                    cmd["parameters"][0] = self.restore_code(trans, repl)
                            i = j
                        else:
                            text = group[0]["parameters"][0]
                            processed, replacements = self.process_text(text)
                            if processed in self.translation_cache:
                                translated = self.translation_cache[processed]
                            else:
                                translated = self.translate_text(processed)
                                self.translation_cache[processed] = translated
                            group[0]["parameters"][0] = self.restore_code(translated, replacements)
                            i += 1
                    else:
                        process_item(lst[i])
                        i += 1

            process_item(data)
            output_path = self.get_output_path(file_path)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.log(f"JSON Hatası: {os.path.basename(file_path)} - {str(e)}")
            return False

    def translate_js_file(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            text_pattern = re.compile(
                r'(?<!\\)["\'](.*?)(?<!\\)["\']',
                re.DOTALL
            )
            def replace_match(match):
                original = match.group(0)
                text = match.group(1)
                processed, replacements = self.process_text(text)
                if processed in self.translation_cache:
                    translated = self.restore_code(self.translation_cache[processed], replacements)
                else:
                    translated = self.translate_text(processed)
                    self.translation_cache[processed] = translated
                    translated = self.restore_code(translated, replacements)
                return original.replace(text, translated)
            translated_content = text_pattern.sub(replace_match, content)
            output_path = self.get_output_path(file_path)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            return True
        except Exception as e:
            self.log(f"JS Hatası: {os.path.basename(file_path)} - {str(e)}")
            return False

    def process_file(self, file_path: str):
        try:
            file_name = os.path.basename(file_path)
            self.progress_queue.put(('progress', (file_name, 0, 'İşleniyor')))
            success = False
            if file_path.endswith('.json'):
                success = self.translate_json_file(file_path)
            elif file_path.endswith('.js'):
                success = self.translate_js_file(file_path)
            if success:
                self.processed_files += 1
                current_progress = int((self.processed_files / self.total_files) * 100)
                self.progress_queue.put(('progress', (file_name, current_progress, 'Tamamlandı')))
                return True
            else:
                self.progress_queue.put(('progress', (file_name, 0, 'Hatalı')))
                return False
        except Exception as e:
            self.progress_queue.put(('error', f"{file_name} - {str(e)}"))
            return False

    def restore_code(self, translated_text: str, replacements: dict) -> str:
        if translated_text is None:
            return ""
        for placeholder, code in replacements.items():
            translated_text = translated_text.replace(placeholder, code)
        import re
        chars = '>/]}\\'
        pattern = r'([' + re.escape(chars) + r'])(?=\S)'
        translated_text = re.sub(pattern, r'\1 ', translated_text)
        return translated_text


    def start_translation_thread(self):
        if not hasattr(self, 'folder_path') or not self.folder_path:
            self.log("Lütfen önce bir EXE dosyası seçin!")
            return
        if not self.running:
            self.running = True
            threading.Thread(target=self.start_translation, daemon=True).start()

    def start_translation(self):
        files = []
        for root_dir, _, filenames in os.walk(self.folder_path):
            for filename in filenames:
                if filename.endswith(('.json', '.js')):
                    files.append(os.path.join(root_dir, filename))
        self.total_files = len(files)
        self.processed_files = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_file, file): file for file in files}
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.progress_queue.put(('error', str(e)))
        self.save_cache()
        self.running = False
        messagebox.showinfo("Çeviri Tamamlandı", "Tüm dosyalar başarıyla çevrildi!")
        self.log("Çeviri işlemi tamamlandı!")

    def update_file_status(self, file_name, progress, status):
        for item in self.tree.get_children():
            if self.tree.item(item, 'values')[0] == file_name:
                self.tree.item(item, values=(file_name, status, f"%{progress}"))
                self.tree.see(item)
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = RPGMakerTranslator(root)
    root.mainloop()
