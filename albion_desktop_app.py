import io
import threading
import requests
import urllib.parse
import customtkinter as ctk
from PIL import Image

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Ítems con alta rotación garantizada en la API pública de Albion
ITEMS_MAP = {
    "Lingote de Metal": "METALBAR",
    "Tablas de Madera": "WOOD",
    "Tela": "CLOTH",
    "Cuero": "LEATHER",
    "Bolsa": "BAG",
    "Capa": "CAPE",
    "Poción de Vida": "POTION_HEALTH",
    "Espada Ancha (Broadsword)": "MAIN_SWORD",
    "Claymore": "2H_CLAYMORE"
}

CIUDADES = ["Caerleon", "Martlock", "Bridgewatch", "Lymhurst", "Fort Sterling", "Thetford"]
TIERS = ["T4", "T5", "T6", "T7", "T8"]
ENCANTAMIENTOS = ["Sin encantar (.0)", ".1", ".2", ".3", ".4"]
CALIDADES = ["1 - Normal", "2 - Bueno", "3 - Notable", "4 - Sobresaliente", "5 - Obra Maestra"]

class AlbionArbitrageApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Albion Online - Arbitrage Pro (Modo Seguro)")
        self.geometry("1040x740")

        self.tabview = ctk.CTkTabview(self, width=1000, height=680)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_scan = self.tabview.add("Escaneo de Mercado")
        self.tab_config = self.tabview.add("Configuración")

        top_frame = ctk.CTkFrame(self.tab_scan)
        top_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(top_frame, text="Origen:", font=("Arial", 11, "bold")).grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.orig_var = ctk.StringVar(value="Martlock")
        self.orig_menu = ctk.CTkOptionMenu(top_frame, variable=self.orig_var, values=CIUDADES, width=130)
        self.orig_menu.grid(row=0, column=1, padx=8, pady=8)

        ctk.CTkLabel(top_frame, text="Destino:", font=("Arial", 11, "bold")).grid(row=0, column=2, padx=8, pady=8, sticky="w")
        self.dest_var = ctk.StringVar(value="Caerleon")
        self.dest_menu = ctk.CTkOptionMenu(top_frame, variable=self.dest_var, values=CIUDADES, width=130)
        self.dest_menu.grid(row=0, column=3, padx=8, pady=8)

        self.btn_run = ctk.CTkButton(top_frame, text="🚀 Escanear Precios Reales", fg_color="#2b8a3e", hover_color="#237032", command=self.execute_arbitrage_scan)
        self.btn_run.grid(row=0, column=4, columnspan=2, padx=15, pady=8, sticky="ew")

        ctk.CTkLabel(top_frame, text="Ítem / Recurso:", font=("Arial", 11, "bold")).grid(row=1, column=0, padx=8, pady=8, sticky="w")
        self.item_var = ctk.StringVar(value="Lingote de Metal")
        self.item_menu = ctk.CTkOptionMenu(top_frame, variable=self.item_var, values=list(ITEMS_MAP.keys()), command=self.update_item_preview, width=220)
        self.item_menu.grid(row=1, column=1, columnspan=2, padx=8, pady=8, sticky="w")

        ctk.CTkLabel(top_frame, text="Tier:", font=("Arial", 11, "bold")).grid(row=1, column=3, padx=8, pady=8, sticky="w")
        self.tier_var = ctk.StringVar(value="T4")
        self.tier_menu = ctk.CTkOptionMenu(top_frame, variable=self.tier_var, values=TIERS, command=self.update_item_preview, width=80)
        self.tier_menu.grid(row=1, column=4, padx=8, pady=8)

        ctk.CTkLabel(top_frame, text="Encantamiento:", font=("Arial", 11, "bold")).grid(row=2, column=0, padx=8, pady=8, sticky="w")
        self.enc_var = ctk.StringVar(value="Sin encantar (.0)")
        self.enc_menu = ctk.CTkOptionMenu(top_frame, variable=self.enc_var, values=ENCANTAMIENTOS, command=self.update_item_preview, width=160)
        self.enc_menu.grid(row=2, column=1, padx=8, pady=8, sticky="w")

        ctk.CTkLabel(top_frame, text="Calidad:", font=("Arial", 11, "bold")).grid(row=2, column=2, padx=8, pady=8, sticky="w")
        self.qual_var = ctk.StringVar(value="1 - Normal")
        self.qual_menu = ctk.CTkOptionMenu(top_frame, variable=self.qual_var, values=CALIDADES, width=150)
        self.qual_menu.grid(row=2, column=3, padx=8, pady=8)

        preview_frame = ctk.CTkFrame(self.tab_scan)
        preview_frame.pack(fill="x", padx=10, pady=5)

        self.img_label = ctk.CTkLabel(preview_frame, text="[Cargando...]", width=80, height=80)
        self.img_label.pack(side="left", padx=15, pady=10)

        info_layout = ctk.CTkFrame(preview_frame, fg_color="transparent")
        info_layout.pack(side="left", padx=10, fill="both", expand=True)

        self.lbl_item_name = ctk.CTkLabel(info_layout, text="", font=("Arial", 14, "bold"))
        self.lbl_item_name.pack(anchor="w", pady=2)

        self.lbl_item_id = ctk.CTkLabel(info_layout, text="", font=("Consolas", 11), text_color="#aaaaaa")
        self.lbl_item_id.pack(anchor="w", pady=2)

        self.log_box = ctk.CTkTextbox(self.tab_scan, width=960, height=320, font=("Consolas", 11))
        self.log_box.pack(padx=10, pady=10, fill="both", expand=True)
        self.log_box.insert("0.0", "[SISTEMA] Conexión lista. Selecciona un recurso o ítem común para ver precios inmediatos.\n")

        lbl_config = ctk.CTkLabel(self.tab_config, text="Parámetros y Tasas Financieras", font=("Arial", 14, "bold"))
        lbl_config.pack(padx=20, pady=20, anchor="w")
        ctk.CTkLabel(self.tab_config, text="• Impuesto de Mercado (Con Premium): 8.5%", font=("Arial", 12)).pack(padx=20, pady=5, anchor="w")
        ctk.CTkLabel(self.tab_config, text="• Costo de Logística / Transporte: 2.5%", font=("Arial", 12)).pack(padx=20, pady=5, anchor="w")

        self.update_item_preview()

    def get_full_item_id(self):
        tier = self.tier_var.get()
        base_code = ITEMS_MAP.get(self.item_var.get(), "METALBAR")
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
        headers = {"User-Agent": "Mozilla/5.0"}
        encoded_id = urllib.parse.quote(item_id, safe='')
        img_url = f"https://render.albiononline.com/v1/item/{encoded_id}.png?size=80"
        try:
            res = requests.get(img_url, headers=headers, timeout=5)
            if res.status_code == 200:
                image_data = Image.open(io.BytesIO(res.content))
                ctk_img = ctk.CTkImage(light_image=image_data, dark_image=image_data, size=(80, 80))
                self.current_ctk_img = ctk_img
                self.img_label.configure(image=ctk_img, text="")
            else:
                self.img_label.configure(image=None, text="[Sin Gráfico]")
        except Exception:
            self.img_label.configure(image=None, text="[Modo Texto]")

    def log(self, message):
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")

    def execute_arbitrage_scan(self):
        orig = self.orig_var.get()
        dest = self.dest_var.get()
        item_id = self.get_full_item_id()
        calidad_str = self.qual_var.get()
        target_quality = int(calidad_str.split(" - ")[0])

        if orig == dest:
            self.log("[ERROR] El origen y el destino no pueden ser la misma ciudad.")
            return

        self.log(f"\n[CONSULTA] Analizando '{item_id}' [Calidad: {calidad_str}] ({orig} ➡️ {dest})...")
        threading.Thread(target=self.fetch_market_data, args=(orig, dest, item_id, target_quality), daemon=True).start()

    def fetch_market_data(self, orig, dest, item_id, target_quality):
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://www.albion-online-data.com/api/v2/stats/prices/{item_id}?locations={orig},{dest}"
        
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if not data:
                    self.log(f"[AVISO] Sin registros en la API para {item_id}.")
                    return

                orig_price = 0
                dest_price = 0

                for entry in data:
                    city = entry.get("city")
                    q = entry.get("quality", 1)
                    
                    # Buscamos precio de venta mínimo disponible
                    sell_min = entry.get("sell_price_min", 0)
                    buy_max = entry.get("buy_price_max", 0)
                    price_to_use = sell_min if sell_min > 0 else buy_max

                    if city == orig and orig_price == 0:
                        orig_price = price_to_use
                    elif city == dest and dest_price == 0:
                        dest_price = price_to_use

                self.log("=" * 70)
                self.log(f" 📦 REPORTE: {item_id} (Calidad {target_quality})")
                self.log(f" 📍 Compra en {orig}: {orig_price:,} plata")
                self.log(f" 📍 Venta en {dest}: {dest_price:,} plata")

                if orig_price == 0 or dest_price == 0:
                    self.log(" ⚠️ Mercado sin órdenes activas para este ítem en la API.")
                    self.log(" 💡 Sugerencia: Prueba con 'Lingote de Metal' o 'Tela' en T4 o T5 para ver precios instantáneos.")
                else:
                    tax_rate = 0.085
                    logistics_rate = 0.025
                    costo_total = orig_price * (1 + logistics_rate)
                    ingreso_neto = dest_price * (1 - tax_rate)
                    ganancia = ingreso_neto - costo_total
                    margen = (ganancia / costo_total * 100) if costo_total > 0 else 0

                    self.log(f" 📊 Costo con Logística (2.5%): {costo_total:,.1f} plata")
                    self.log(f" 📊 Ingreso tras Impuesto (8.5%): {ingreso_neto:,.1f} plata")
                    if ganancia > 0:
                        self.log(f" 💰 GANANCIA NETA: +{ganancia:,.1f} plata ({margen:.1f}%) [RENTABLE]")
                    else:
                        self.log(f" 📉 PÉRDIDA NETA: {ganancia:,.1f} plata ({margen:.1f}%) [NO RENTABLE]")
                self.log("=" * 70)
            else:
                self.log(f"[ERROR] Código HTTP: {res.status_code}")
        except Exception as e:
            self.log(f"[ERROR] Error de red: {str(e)}")

if __name__ == "__main__":
    app = AlbionArbitrageApp()
    app.mainloop()
