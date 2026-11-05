import customtkinter as ctk
import requests
import sqlite3
import csv
import threading
from datetime import datetime

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AlbionDesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Albion Online - Arbitrage & Market Bot")
        self.geometry("900x650")
        self.minsize(850, 600)

        self.db_name = "albion_market.db"
        self.csv_file = "arbitrage_report.csv"
        self.market_tax = 0.085
        self.transport_cost = 0.025
        self.valid_cities = ["Martlock", "Fort Sterling", "Lymhurst", "Bridgewatch", "Thetford", "Caerleon", "Brecilien"]
        
        self.current_origin = "Martlock"
        self.current_dest = "Caerleon"
        self.current_items = ["T8_HIDE_LEVEL5", "T7_POTION_HEAL_BIG", "T6_ARMOR_LEATHER_SET1"]
        self.discord_webhook = ""
        self.alert_threshold = 20.0
        self.items_cache = None

        self._init_db()
        self._build_ui()

    def _init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS arbitrage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    item_id TEXT,
                    origin_city TEXT,
                    dest_city TEXT,
                    buy_price INTEGER,
                    sell_price INTEGER,
                    net_profit INTEGER,
                    roi REAL
                )
            ''')
            conn.commit()

    def _build_ui(self):
        self.tabview = ctk.CTkTabview(self, width=860, height=600)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_scan = self.tabview.add("📊 Escaneo y Rutas")
        self.tab_items = self.tabview.add("🔍 Búsqueda de Ítems")
        self.tab_config = self.tabview.add("⚙️ Configuración y Alertas")

        self._setup_scan_tab()
        self._setup_items_tab()
        self._setup_config_tab()

    def _setup_scan_tab(self):
        top_frame = ctk.CTkFrame(self.tab_scan)
        top_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(top_frame, text="Origen:", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        self.origin_var = ctk.StringVar(value=self.current_origin)
        self.origin_menu = ctk.CTkOptionMenu(top_frame, variable=self.origin_var, values=self.valid_cities, command=lambda v: setattr(self, 'current_origin', v))
        self.origin_menu.pack(side="left", padx=5)

        ctk.CTkLabel(top_frame, text="Destino:", font=("Arial", 12, "bold")).pack(side="left", padx=15)
        self.dest_var = ctk.StringVar(value=self.current_dest)
        self.dest_menu = ctk.CTkOptionMenu(top_frame, variable=self.dest_var, values=self.valid_cities, command=lambda v: setattr(self, 'current_dest', v))
        self.dest_menu.pack(side="left", padx=5)

        self.btn_run = ctk.CTkButton(top_frame, text="🚀 Ejecutar Escaneo", fg_color="#2b8a3e", hover_color="#237032", command=lambda: threading.Thread(target=self.execute_arbitrage_scan, daemon=True).start())
        self.btn_run.pack(side="right", padx=10)

        self.log_box = ctk.CTkTextbox(self.tab_scan, width=820, height=430, font=("Consolas", 11))
        self.log_box.pack(padx=10, pady=10, fill="both", expand=True)
        self.log_box.insert("0.0", "[INFO] Aplicación lista. Selecciona tus rutas y haz clic en 'Ejecutar Escaneo'.
")

    def log(self, message):
        self.log_box.insert("end", f"{message}
")
        self.log_box.see("end")

    def execute_arbitrage_scan(self):
        self.log(f"
[INFO] Consultando mercado: {self.current_origin} ➔ {self.current_dest}...")
        items_str = ",".join(self.current_items)
        url = f"https://west.albion-online-data.com/api/v2/stats/prices/{items_str}?locations={self.current_origin},{self.current_dest}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                self.log(f"[ERROR] Fallo al conectar con la API (Código {response.status_code})")
                return

            data = response.json()
            market_map = {}
            for entry in data:
                item_id = entry["item_id"]
                city = entry["city"]
                if item_id not in market_map:
                    market_map[item_id] = {}
                market_map[item_id][city] = {"sell_price_min": entry.get("sell_price_min", 0)}

            current_time = datetime.now().isoformat()
            results = []

            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                for item, cities in market_map.items():
                    if self.current_origin in cities and self.current_dest in cities:
                        buy_price = cities[self.current_origin]["sell_price_min"]
                        sell_price = cities[self.current_dest]["sell_price_min"]
                        
                        if buy_price > 0 and sell_price > 0:
                            transport_fee = buy_price * self.transport_cost
                            gross_revenue = sell_price * (1 - self.market_tax)
                            net_profit = int(gross_revenue - buy_price - transport_fee)
                            roi = round((net_profit / buy_price) * 100, 2)
                            
                            results.append({
                                "timestamp": current_time, "item_id": item, "origin_city": self.current_origin,
                                "dest_city": self.current_dest, "buy_price": buy_price, "sell_price": sell_price,
                                "net_profit": net_profit, "roi": roi
                            })

                            cursor.execute('''
                                INSERT INTO arbitrage_logs (timestamp, item_id, origin_city, dest_city, buy_price, sell_price, net_profit, roi)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (current_time, item, self.current_origin, self.current_dest, buy_price, sell_price, net_profit, roi))

                            self.log(f"[OK] {item:<25} | Neto: {net_profit:>8}s | ROI: {roi:>6}%")
                            
                            if roi >= self.alert_threshold and self.discord_webhook:
                                try:
                                    requests.post(self.discord_webhook, json={"content": f"🚨 **Arbitraje Albion** | `{item}` | `{self.current_origin} ➔ {self.current_dest}` | Neto: **{net_profit:,}s** | ROI: **+{roi}%**"}, timeout=5)
                                except:
                                    pass

                conn.commit()

            if results:
                with open(self.csv_file, mode="w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)
                self.log(f"[SUCCESS] Datos guardados en '{self.csv_file}' y SQLite.
")
            else:
                self.log("[WARNING] No se encontraron precios de venta válidos.
")

        except Exception as e:
            self.log(f"[ERROR] Excepción durante el escaneo: {e}")

    def _setup_items_tab(self):
        search_frame = ctk.CTkFrame(self.tab_items)
        search_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(search_frame, text="Buscar Ítem:", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        self.search_entry = ctk.CTkEntry(search_frame, width=300, placeholder_text="ej: T8 Hide, Stalker Jacket...")
        self.search_entry.pack(side="left", padx=5)

        self.btn_search = ctk.CTkButton(search_frame, text="Buscar en API", command=lambda: threading.Thread(target=self.perform_item_search, daemon=True).start())
        self.btn_search.pack(side="left", padx=10)

        content_frame = ctk.CTkFrame(self.tab_items)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.result_box = ctk.CTkTextbox(content_frame, width=400, height=400)
        self.result_box.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.result_box.insert("0.0", "--- Escribe un término y presiona Buscar ---
")

        right_panel = ctk.CTkFrame(content_frame)
        right_panel.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(right_panel, text="Ítems en Seguimiento:", font=("Arial", 12, "bold")).pack(pady=5)
        self.items_list_box = ctk.CTkTextbox(right_panel, width=380, height=350)
        self.items_list_box.pack(padx=5, pady=5)
        for item in self.current_items:
            self.items_list_box.insert("end", f"- {item}
")

    def perform_item_search(self):
        query = self.search_entry.get().strip().lower()
        if not query:
            return

        self.result_box.delete("0.0", "end")
        self.result_box.insert("end", "[INFO] Descargando catálogo de referencia...
")

        if not self.items_cache:
            try:
                res = requests.get("https://raw.githubusercontent.com/ao-data/ao-bin-dumps/master/formatted/items.json", timeout=15)
                self.items_cache = res.json()
            except Exception as e:
                self.result_box.insert("end", f"[ERROR] No se pudo cargar el catálogo: {e}
")
                return

        self.result_box.delete("0.0", "end")
        matches = 0
        for item in self.items_cache:
            uid = item.get("UniqueName", "")
            name = item.get("localized_names", {}).get("EN-US", "")
            if query in uid.lower() or query in name.lower():
                self.result_box.insert("end", f"ID: {uid}
Nombre: {name}
--------------------
")
                matches += 1
                if matches >= 15:
                    break
        if matches == 0:
            self.result_box.insert("end", "No se encontraron coincidencias.
")

    def _setup_config_tab(self):
        config_frame = ctk.CTkFrame(self.tab_config)
        config_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(config_frame, text="Configuración de Webhook de Discord", font=("Arial", 14, "bold")).pack(anchor="w", pady=5)
        self.webhook_entry = ctk.CTkEntry(config_frame, width=500, placeholder_text="https://discord.com/api/webhooks/...")
        self.webhook_entry.pack(anchor="w", pady=5)

        ctk.CTkLabel(config_frame, text="Umbral Mínimo de ROI (%) para Alertas:", font=("Arial", 14, "bold")).pack(anchor="w", pady=(15, 5))
        self.threshold_entry = ctk.CTkEntry(config_frame, width=150)
        self.threshold_entry.insert(0, str(self.alert_threshold))
        self.threshold_entry.pack(anchor="w", pady=5)

        self.btn_save_config = ctk.CTkButton(config_frame, text="Guardar Configuración", fg_color="#1864ab", command=self.save_config)
        self.btn_save_config.pack(anchor="w", pady=25)

    def save_config(self, event=None):
        self.discord_webhook = self.webhook_entry.get().strip()
        try:
            self.alert_threshold = float(self.threshold_entry.get().strip())
        except ValueError:
            pass
        self.log("[OK] Configuración actualizada correctamente.")

if __name__ == "__main__":
    app = AlbionDesktopApp()
    app.mainloop()
