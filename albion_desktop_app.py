import io
import threading
import requests
import customtkinter as ctk
from PIL import Image

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Catálogo completo de armas y equipamiento principal de Albion Online
WEAPONS_AND_GEAR_MAP = {
    # --- ESPADAS ---
    "Espada Ancha (Broadsword)": "MAIN_SWORD",
    "Espadas Dobles (Dual Swords)": "DUALSWORD",
    "Claymore": "2H_CLAYMORE",
    "Espada Tallada (Carving Sword)": "2H_CLEAVER_GIANT",
    "Hoja de Galatine (Galatine Pair)": "2H_DUAL_SWORD_AVALON",
    # --- HACHAS ---
    "Hacha (Battleaxe)": "MAIN_AXE",
    "Alabarda (Halberd)": "2H_HALBERD",
    "Hacha de Guerra (Greataxe)": "2H_AXE",
    "Reaper (Infernal Scythe)": "2H_SCYTHE_HELL",
    # --- ARCOS ---
    "Arco (Bow)": "MAIN_BOW",
    "Arco de Guerra (Warbow)": "2H_WARBOW",
    "Arco Susurrante (Whispering Bow)": "2H_LONGBOW_AVALON",
    "Arco de Badon (Badon)": "2H_BOW_HELL",
    # --- BALLESTAS ---
    "Ballesta (Crossbow)": "MAIN_CROSSBOW",
    "Ballesta Pesada (Heavy Crossbow)": "2H_CROSSBOW",
    "Lanzavirotes (Repeating Crossbow)": "2H_CROSSBOW_LARGE_MORGANA",
    # --- BASTONES DE FUEGO ---
    "Bastón de Fuego (Fire Staff)": "MAIN_FIRESTAFF",
    "Bastón de Gran Fuego (Great Fire Staff)": "2H_FIRESTAFF",
    "Bastón Infernal (Infernal Staff)": "2H_INFERNALSTAFF",
    # --- BASTONES DE HIELO ---
    "Bastón de Hielo (Frost Staff)": "MAIN_FROSTSTAFF",
    "Bastón de Gran Hielo (Great Frost)": "2H_FROSTSTAFF",
    "Bastón Glacial (Glacial Staff)": "2H_GLACIALSTAFF",
    # --- BASTONES SAGRADOS ---
    "Bastón Sagrado (Holy Staff)": "MAIN_HOLYSTAFF",
    "Bastón de Gran Sagrado (Great Holy)": "2H_HOLYSTAFF",
    "Bastón Redentor (Redeemer)": "2H_HOLY_AVALON",
    # --- DAGAS ---
    "Daga (Dagger)": "MAIN_DAGGER",
    "Dagas de Sombra (Dual Daggers)": "2H_DAGGERPAIR",
    "Garras (Claws)": "2H_CLAW_PAIR",
    "Colmillo de Pantera (Deathgivers)": "2H_DAGGER_HELL",
    # --- LANZAS ---
    "Lanza (Spear)": "MAIN_SPEAR",
    "Pica (Pike)": "2H_SPEAR",
    "Lanza de Glaive (Glaive)": "2H_GLAIVE",
    "Lanza de Trinidad (Trinity Spear)": "2H_HARPOON_AVALON",
    # --- MARTILLOS ---
    "Martillo (Hammer)": "MAIN_HAMMER",
    "Martillo de Polos (Great Hammer)": "2H_HAMMER",
    "Martillo Tumba (Tombhammer)": "2H_POLEHAMMER",
    # --- GUANTES DE GUERRA ---
    "Guantes de Brawler (Brawling Gloves)": "MAIN_BRACERS",
    "Puños de Hierro (Spiked Gauntlets)": "2H_KNUCKLES_HELL",
    # --- RECURSOS Y CONSUMIBLES ---
    "Bolsa": "BAG",
    "Capa": "CAPE",
    "Poción de Vida": "POTION_HEALTH",
    "Guisado de Ternera": "MEAL_STEW"
}

CIUDADES = ["Caerleon", "Brecilien", "Martlock", "Bridgewatch", "Lymhurst", "Fort Sterling", "Thetford"]
TIERS = ["T4", "T5", "T6", "T7", "T8"]
ENCANTAMIENTOS = ["Sin encantar (.0)", ".1", ".2", ".3", ".4"]

class AlbionArbitrageApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Albion Online - Market Arbitrage Professional Tool")
        self.geometry("1020x720")

        self.tabview = ctk.CTkTabview(self, width=980, height=660)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_scan = self.tabview.add("Escaneo de Mercado")
        self.tab_config = self.tabview.add("Configuración")

        # --- PANEL DE SELECCIÓN ---
        top_frame = ctk.CTkFrame(self.tab_scan)
        top_frame.pack(fill="x", padx=10, pady=10)

        # Ciudades
        ctk.CTkLabel(top_frame, text="Origen:", font=("Arial", 11, "bold")).grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.orig_var = ctk.StringVar(value="Martlock")
        self.orig_menu = ctk.CTkOptionMenu(top_frame, variable=self.orig_var, values=CIUDADES, width=130)
        self.orig_menu.grid(row=0, column=1, padx=8, pady=8)

        ctk.CTkLabel(top_frame, text="Destino:", font=("Arial", 11, "bold")).grid(row=0, column=2, padx=8, pady=8, sticky="w")
        self.dest_var = ctk.StringVar(value="Caerleon")
        self.dest_menu = ctk.CTkOptionMenu(top_frame, variable=self.dest_var, values=CIUDADES, width=130)
        self.dest_menu.grid(row=0, column=3, padx=8, pady=8)

        self.btn_run = ctk.CTkButton(top_frame, text="🚀 Escanear Arbitraje", fg_color="#2b8a3e", hover_color="#237032", command=self.execute_arbitrage_scan)
        self.btn_run.grid(row=0, column=4, columnspan=2, padx=15, pady=8, sticky="ew")

        # Filtros de Ítem
        ctk.CTkLabel(top_frame, text="Arma / Ítem:", font=("Arial", 11, "bold")).grid(row=1, column=0, padx=8, pady=8, sticky="w")
        self.item_var = ctk.StringVar(value="Espada Ancha (Broadsword)")
        self.item_menu = ctk.CTkOptionMenu(top_frame, variable=self.item_var, values=list(WEAPONS_AND_GEAR_MAP.keys()), command=self.update_item_preview, width=220)
        self.item_menu.grid(row=1, column=1, columnspan=2, padx=8, pady=8, sticky="w")

        ctk.CTkLabel(top_frame, text="Tier:", font=("Arial", 11, "bold")).grid(row=1, column=3, padx=8, pady=8, sticky="w")
        self.tier_var = ctk.StringVar(value="T4")
        self.tier_menu = ctk.CTkOptionMenu(top_frame, variable=self.tier_var, values=TIERS, command=self.update_item_preview, width=80)
        self.tier_menu.grid(row=1, column=4, padx=8, pady=8)

        ctk.CTkLabel(top_frame, text="Encantamiento:", font=("Arial", 11, "bold")).grid(row=2, column=0, padx=8, pady=8, sticky="w")
        self.enc_var = ctk.StringVar(value="Sin encantar (.0)")
        self.enc_menu = ctk.CTkOptionMenu(top_frame, variable=self.enc_var, values=ENCANTAMIENTOS, command=self.update_item_preview, width=160)
        self.enc_menu.grid(row=2, column=1, padx=8, pady=8, sticky="w")

        # --- VISTA PREVIA ---
        preview_frame = ctk.CTkFrame(self.tab_scan)
        preview_frame.pack(fill="x", padx=10, pady=5)

        self.img_label = ctk.CTkLabel(preview_frame, text="[Cargando...]", width=80, height=80)
        self.img_label.pack(side="left", padx=15, pady=10)

        info_layout = ctk.CTkFrame(preview_frame, fg_color="transparent")
        info_layout.pack(side="left", padx=10, fill="both", expand=True)

        self.lbl_item_name = ctk.CTkLabel(info_layout, text="Selección: Espada Ancha (T4.0)", font=("Arial", 14, "bold"))
        self.lbl_item_name.pack(anchor="w", pady=2)

        self.lbl_item_id = ctk.CTkLabel(info_layout, text="ID API: T4_MAIN_SWORD", font=("Consolas", 11), text_color="#aaaaaa")
        self.lbl_item_id.pack(anchor="w", pady=2)

        # --- CONSOLA DE LOGS ---
        self.log_box = ctk.CTkTextbox(self.tab_scan, width=940, height=340, font=("Consolas", 11))
        self.log_box.pack(padx=10, pady=10, fill="both", expand=True)
        self.log_box.insert("0.0", "[SISTEMA] Bot inicializado correctamente con catálogo completo de armas y equipo.\n")

        # Configuración de tasas
        lbl_config = ctk.CTkLabel(self.tab_config, text="Tasas y Parámetros del Mercado", font=("Arial", 14, "bold"))
        lbl_config.pack(padx=20, pady=20, anchor="w")
        ctk.CTkLabel(self.tab_config, text="• Impuesto de Mercado (Con cuenta Premium): 8.5%", font=("Arial", 12)).pack(padx=20, pady=5, anchor="w")
        ctk.CTkLabel(self.tab_config, text="• Tasa de Logística / Transporte estimada: 2.5%", font=("Arial", 12)).pack(padx=20, pady=5, anchor="w")

        self.update_item_preview()

    def get_full_item_id(self):
        tier = self.tier_var.get()
        base_code = WEAPONS_AND_GEAR_MAP.get(self.item_var.get(), "MAIN_SWORD")
        enc_str = self.enc_var.get()
        
        enc_level = "@0"
        if ".1" in enc_str: enc_level = "@1"
        elif ".2" in enc_str: enc_level = "@2"
        elif ".3" in enc_str: enc_level = "@3"
        elif ".4" in enc_str: enc_level = "@4"

        full_id = f"{tier}_{base_code}"
        if enc_level != "@0":
            full_id += f"{enc_level}"
            
        return full_id

    def update_item_preview(self, *args):
        item_id = self.get_full_item_id()
        item_name = self.item_var.get()
        tier = self.tier_var.get()
        enc = self.enc_var.get().split()[0]
        
        self.lbl_item_name.configure(text=f"Selección: {item_name} ({tier} {enc})")
        self.lbl_item_id.configure(text=f"ID API: {item_id}")
        threading.Thread(target=self.load_item_image, args=(item_id,), daemon=True).start()

    def load_item_image(self, item_id):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        img_url = f"https://render.albiononline.com/v1/item/{item_id}.png?size=80"
        
        try:
            res = requests.get(img_url, headers=headers, timeout=5)
            if res.status_code == 200:
                image_data = Image.open(io.BytesIO(res.content))
                ctk_img = ctk.CTkImage(light_image=image_data, dark_image=image_data, size=(80, 80))
                self.img_label.configure(image=ctk_img, text="")
            else:
                self.img_label.configure(image=None, text="[Ítem sin Gráfico]")
        except Exception:
            self.img_label.configure(image=None, text="[Modo Texto]")

    def log(self, message):
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")

    def execute_arbitrage_scan(self):
        orig = self.orig_var.get()
        dest = self.dest_var.get()
        item_id = self.get_full_item_id()

        if orig == dest:
            self.log("[ERROR] El origen y el destino no pueden ser la misma ciudad.")
            return

        self.log(f"\n[CONSULTA] Buscando precios en vivo para '{item_id}' ({orig} ➡️ {dest})...")
        threading.Thread(target=self.fetch_market_data, args=(orig, dest, item_id), daemon=True).start()

    def fetch_market_data(self, orig, dest, item_id):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        url = f"https://www.albion-online-data.com/api/v2/stats/prices/{item_id}?locations={orig},{dest}"
        
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if not data:
                    self.log(f"[AVISO] No hay datos en la API para {item_id} entre {orig} y {dest}.")
                    return

                orig_sell, orig_buy = 0, 0
                dest_sell, dest_buy = 0, 0

                for entry in data:
                    city = entry.get("city")
                    if city == orig:
                        orig_sell = entry.get("sell_price_min", 0)
                        orig_buy = entry.get("buy_price_max", 0)
                    elif city == dest:
                        dest_sell = entry.get("sell_price_min", 0)
                        dest_buy = entry.get("buy_price_max", 0)

                precio_compra = orig_sell if orig_sell > 0 else orig_buy
                precio_venta = dest_buy if dest_buy > 0 else dest_sell

                tax_rate, logistics_rate = 0.085, 0.025
                costo_total = precio_compra * (1 + logistics_rate)
                ingreso_neto = precio_venta * (1 - tax_rate)
                ganancia = ingreso_neto - costo_total
                margen = (ganancia / costo_total * 100) if costo_total > 0 else 0

                self.log("=" * 70)
                self.log(f" 📦 ANÁLISIS DE ARBITRAJE: {item_id}")
                self.log(f" 📍 Comprar en {orig}: {precio_compra:,} plata")
                self.log(f" 📍 Vender en {dest}: {precio_venta:,} plata")
                if precio_compra == 0 or precio_venta == 0:
                    self.log(" ⚠️ Mercado sin órdenes activas en alguna de las dos ciudades.")
                else:
                    self.log(f" 📊 Costo con Logística (2.5%): {costo_total:,.1f} plata")
                    self.log(f" 📊 Ingresos netos (con 8.5% impuesto): {ingreso_neto:,.1f} plata")
                    if ganancia > 0:
                        self.log(f" 💰 GANANCIA ESTIMADA: +{ganancia:,.1f} plata (Margen: {margen:.1f}%) [RENTABLE]")
                    else:
                        self.log(f" 📉 PÉRDIDA ESTIMADA: {ganancia:,.1f} plata (Margen: {margen:.1f}%) [NO RENTABLE]")
                self.log("=" * 70)
            else:
                self.log(f"[ERROR] Código de respuesta HTTP no válido: {res.status_code}")
        except Exception as e:
            self.log(f"[ERROR] Excepción de conexión de red: {str(e)}")

if __name__ == "__main__":
    app = AlbionArbitrageApp()
    app.mainloop()
