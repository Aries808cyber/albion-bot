import io
import threading
import requests
import customtkinter as ctk
from PIL import Image

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Diccionario base de ítems para construir los IDs de la API de Albion
ITEMS_BASE = {
    "Bolsa": "BAG",
    "Capa": "CAPE",
    "Lingote de Metal": "METALBAR",
    "Tablas de Madera": "WOOD",
    "Tela": "CLOTH",
    "Cuero": "LEATHER",
    "Espada Ancha": "MAIN_SWORD",
    "Hacha de Guerra": "MAIN_AXE",
    "Poción de Cura": "POTION_HEAL"
}

CIUDADES = ["Caerleon", "Brecilien", "Martlock", "Bridgewatch", "Lymhurst", "Fort Sterling", "Thetford"]
TIERS = ["T4", "T5", "T6", "T7", "T8"]
ENCANTAMIENTOS = [".0 (Sin encantar)", ".1", ".2", ".3", ".4"]

class AlbionArbitrageApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Albion Online - Scanner de Arbitraje Avanzado")
        self.geometry("980x680")

        self.tabview = ctk.CTkTabview(self, width=940, height=620)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_scan = self.tabview.add("Escaneo de Mercado")
        self.tab_config = self.tabview.add("Configuración")

        # --- PANEL SUPERIOR DE SELECCIÓN ---
        top_frame = ctk.CTkFrame(self.tab_scan)
        top_frame.pack(fill="x", padx=10, pady=10)

        # Rutas
        ctk.CTkLabel(top_frame, text="Origen:", font=("Arial", 11, "bold")).grid(row=0, column=0, padx=5, pady=5)
        self.orig_var = ctk.StringVar(value="Martlock")
        self.orig_menu = ctk.CTkOptionMenu(top_frame, variable=self.orig_var, values=CIUDADES, width=120)
        self.orig_menu.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(top_frame, text="Destino:", font=("Arial", 11, "bold")).grid(row=0, column=2, padx=5, pady=5)
        self.dest_var = ctk.StringVar(value="Caerleon")
        self.dest_menu = ctk.CTkOptionMenu(top_frame, variable=self.dest_var, values=CIUDADES, width=120)
        self.dest_menu.grid(row=0, column=3, padx=5, pady=5)

        # Selectores de Ítem, Tier y Encantamiento
        ctk.CTkLabel(top_frame, text="Ítem:", font=("Arial", 11, "bold")).grid(row=1, column=0, padx=5, pady=5)
        self.item_var = ctk.StringVar(value="Bolsa")
        self.item_menu = ctk.CTkOptionMenu(top_frame, variable=self.item_var, values=list(ITEMS_BASE.keys()), command=self.update_item_preview, width=140)
        self.item_menu.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(top_frame, text="Tier:", font=("Arial", 11, "bold")).grid(row=1, column=2, padx=5, pady=5)
        self.tier_var = ctk.StringVar(value="T4")
        self.tier_menu = ctk.CTkOptionMenu(top_frame, variable=self.tier_var, values=TIERS, command=self.update_item_preview, width=80)
        self.tier_menu.grid(row=1, column=3, padx=5, pady=5)

        ctk.CTkLabel(top_frame, text="Encantamiento:", font=("Arial", 11, "bold")).grid(row=1, column=4, padx=5, pady=5)
        self.enc_var = ctk.StringVar(value=".0 (Sin encantar)")
        self.enc_menu = ctk.CTkOptionMenu(top_frame, variable=self.enc_var, values=ENCANTAMIENTOS, command=self.update_item_preview, width=150)
        self.enc_menu.grid(row=1, column=5, padx=5, pady=5)

        # Botón de Escaneo
        self.btn_run = ctk.CTkButton(top_frame, text="🚀 Escanear Ítem", fg_color="#2b8a3e", hover_color="#237032", command=self.execute_arbitrage_scan)
        self.btn_run.grid(row=0, column=4, columnspan=2, padx=10, pady=5, sticky="ew")

        # --- PANEL CENTRAL: VISTA PREVIA CON IMAGEN Y RESULTADOS ---
        preview_frame = ctk.CTkFrame(self.tab_scan)
        preview_frame.pack(fill="x", padx=10, pady=5)

        self.img_label = ctk.CTkLabel(preview_frame, text="[Cargando Imagen...]", width=80, height=80)
        self.img_label.pack(side="left", padx=15, pady=10)

        self.lbl_item_id = ctk.CTkLabel(preview_frame, text="ID Técnico: T4_BAG", font=("Consolas", 12, "bold"))
        self.lbl_item_id.pack(side="left", padx=10)

        # Registro de Consola
        self.log_box = ctk.CTkTextbox(self.tab_scan, width=900, height=360, font=("Consolas", 11))
        self.log_box.pack(padx=10, pady=10, fill="both", expand=True)
        self.log_box.insert("0.0", "[INFO] Selecciona un ítem, tier y encantamiento para consultar precios reales.\n")

        # --- PESTAÑA CONFIGURACIÓN ---
        lbl_config = ctk.CTkLabel(self.tab_config, text="Configuración de Tasas de Mercado", font=("Arial", 14, "bold"))
        lbl_config.pack(padx=20, pady=20, anchor="w")

        ctk.CTkLabel(self.tab_config, text="Impuesto de Mercado (Premium): 8.5%", font=("Arial", 12)).pack(padx=20, pady=5, anchor="w")
        ctk.CTkLabel(self.tab_config, text="Tasa de Logística estimada: 2.5%", font=("Arial", 12)).pack(padx=20, pady=5, anchor="w")

        # Cargar primera vista previa
        self.update_item_preview()

    def get_full_item_id(self):
        tier = self.tier_var.get()
        base_code = ITEMS_BASE.get(self.item_var.get(), "BAG")
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
        self.lbl_item_id.configure(text=f"ID Técnico: {item_id}")
        threading.Thread(target=self.load_item_image, args=(item_id,), daemon=True).start()

    def load_item_image(self, item_id):
        img_url = f"https://render.albiononline.com/v1/item/{item_id}.png?size=80"
        try:
            res = requests.get(img_url, timeout=5)
            if res.status_code == 200:
                image_data = Image.open(io.BytesIO(res.content))
                ctk_img = ctk.CTkImage(light_image=image_data, dark_image=image_data, size=(80, 80))
                self.img_label.configure(image=ctk_img, text="")
            else:
                self.img_label.configure(image=None, text="[Sin Imagen]")
        except Exception:
            self.img_label.configure(image=None, text="[Error Imagen]")

    def log(self, message):
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")

    def execute_arbitrage_scan(self):
        orig = self.orig_var.get()
        dest = self.dest_var.get()
        item_id = self.get_full_item_id()

        if orig == dest:
            self.log("[ERROR] El origen y el destino deben ser ciudades distintas.")
            return

        self.log(f"\n[INFO] Consultando datos de mercado para '{item_id}' ({orig} -> {dest})...")
        threading.Thread(target=self.fetch_market_data, args=(orig, dest, item_id), daemon=True).start()

    def fetch_market_data(self, orig, dest, item_id):
        url = f"https://www.albion-online-data.com/api/v2/stats/prices/{item_id}?locations={orig},{dest}"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if not data:
                    self.log("[WARNING] No se devolvieron registros para este ítem.")
                    return

                orig_buy, dest_sell = 0, 0
                for entry in data:
                    city = entry.get("city")
                    if city == orig:
                        orig_buy = entry.get("sell_price_min", 0)
                    elif city == dest:
                        dest_sell = entry.get("buy_price_max", 0)
                        if dest_sell == 0:
                            dest_sell = entry.get("sell_price_min", 0)

                tax_rate, logistics_rate = 0.085, 0.025
                cost = orig_buy * (1 + logistics_rate)
                revenue = dest_sell * (1 - tax_rate)
                profit = revenue - cost
                margin = (profit / cost * 100) if cost > 0 else 0

                self.log("=" * 65)
                self.log(f" 📦 RESULTADO PARA: {item_id}")
                self.log(f" 📍 Comprar en {orig}: {orig_buy:,} plata")
                self.log(f" 📍 Vender en {dest}: {dest_sell:,} plata")
                self.log(f" 📊 Costo con Logística (2.5%): {cost:,.1f} plata")
                self.log(f" 📊 Ingreso tras Impuesto (8.5%): {revenue:,.1f} plata")
                self.log(f" 💰 Ganancia / Pérdida Neta: {profit:,.1f} plata ({margin:.1f}%)")
                self.log("=" * 65)
            else:
                self.log(f"[ERROR] Respuesta de API no válida ({res.status_code})")
        except Exception as e:
            self.log(f"[ERROR] Error de conexión: {str(e)}")

if __name__ == "__main__":
    app = AlbionArbitrageApp()
    app.mainloop()
