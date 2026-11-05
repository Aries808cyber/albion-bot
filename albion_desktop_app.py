import io
import threading
import requests
import customtkinter as ctk
from PIL import Image

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Mapeo preciso de ítems y sus identificadores oficiales en la API de Albion
ITEMS_MAP = {
    "Bolsa": "BAG",
    "Capa": "CAPE",
    "Poción de Vida": "POTION_HEALTH",
    "Poción de Maná": "POTION_ENERGY",
    "Poción de Gigante": "POTION_COOLDOWN",
    "Guisado de Ternera": "MEAL_STEW",
    "Tortilla de Cerdo": "MEAL_OMELETTE",
    "Lingote de Metal": "METALBAR",
    "Tablas de Madera": "WOOD",
    "Tela": "CLOTH",
    "Cuero": "LEATHER",
    "Espada Ancha": "MAIN_SWORD",
    "Hacha de Guerra": "MAIN_AXE",
    "Brazales de Cruzado": "ARMOR_PLATE_SET1",
    "Túnica de Mago": "ARMOR_CLOTH_SET2"
}

CIUDADES = ["Caerleon", "Brecilien", "Martlock", "Bridgewatch", "Lymhurst", "Fort Sterling", "Thetford"]
TIERS = ["T4", "T5", "T6", "T7", "T8"]
ENCANTAMIENTOS = ["Sin encantar (.0)", ".1", ".2", ".3", ".4"]

class AlbionArbitrageApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Albion Online - Market Arbitrage Professional Tool")
        self.geometry("1000x700")

        self.tabview = ctk.CTkTabview(self, width=960, height=650)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_scan = self.tabview.add("Escaneo de Mercado")
        self.tab_config = self.tabview.add("Configuración")

        # --- PANEL DE SELECCIÓN ---
        top_frame = ctk.CTkFrame(self.tab_scan)
        top_frame.pack(fill="x", padx=10, pady=10)

        # Fila 1: Origen y Destino
        ctk.CTkLabel(top_frame, text="Ciudad Origen:", font=("Arial", 11, "bold")).grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.orig_var = ctk.StringVar(value="Martlock")
        self.orig_menu = ctk.CTkOptionMenu(top_frame, variable=self.orig_var, values=CIUDADES, width=130)
        self.orig_menu.grid(row=0, column=1, padx=8, pady=8)

        ctk.CTkLabel(top_frame, text="Ciudad Destino:", font=("Arial", 11, "bold")).grid(row=0, column=2, padx=8, pady=8, sticky="w")
        self.dest_var = ctk.StringVar(value="Caerleon")
        self.dest_menu = ctk.CTkOptionMenu(top_frame, variable=self.dest_var, values=CIUDADES, width=130)
        self.dest_menu.grid(row=0, column=3, padx=8, pady=8)

        self.btn_run = ctk.CTkButton(top_frame, text="🚀 Escanear Ítem", fg_color="#2b8a3e", hover_color="#237032", command=self.execute_arbitrage_scan)
        self.btn_run.grid(row=0, column=4, columnspan=2, padx=15, pady=8, sticky="ew")

        # Fila 2: Selección de Ítems
        ctk.CTkLabel(top_frame, text="Ítem:", font=("Arial", 11, "bold")).grid(row=1, column=0, padx=8, pady=8, sticky="w")
        self.item_var = ctk.StringVar(value="Bolsa")
        self.item_menu = ctk.CTkOptionMenu(top_frame, variable=self.item_var, values=list(ITEMS_MAP.keys()), command=self.update_item_preview, width=150)
        self.item_menu.grid(row=1, column=1, padx=8, pady=8)

        ctk.CTkLabel(top_frame, text="Tier:", font=("Arial", 11, "bold")).grid(row=1, column=2, padx=8, pady=8, sticky="w")
        self.tier_var = ctk.StringVar(value="T4")
        self.tier_menu = ctk.CTkOptionMenu(top_frame, variable=self.tier_var, values=TIERS, command=self.update_item_preview, width=90)
        self.tier_menu.grid(row=1, column=3, padx=8, pady=8)

        ctk.CTkLabel(top_frame, text="Encantamiento:", font=("Arial", 11, "bold")).grid(row=1, column=4, padx=8, pady=8, sticky="w")
        self.enc_var = ctk.StringVar(value="Sin encantar (.0)")
        self.enc_menu = ctk.CTkOptionMenu(top_frame, variable=self.enc_var, values=ENCANTAMIENTOS, command=self.update_item_preview, width=150)
        self.enc_menu.grid(row=1, column=5, padx=8, pady=8)

        # --- PANEL VISTA PREVIA DE IMAGEN Y DETALLES ---
        preview_frame = ctk.CTkFrame(self.tab_scan)
        preview_frame.pack(fill="x", padx=10, pady=5)

        self.img_label = ctk.CTkLabel(preview_frame, text="[Cargando...]", width=90, height=90)
        self.img_label.pack(side="left", padx=15, pady=10)

        info_layout = ctk.CTkFrame(preview_frame, fg_color="transparent")
        info_layout.pack(side="left", padx=10, fill="both", expand=True)

        self.lbl_item_name = ctk.CTkLabel(info_layout, text="Nombre: Bolsa (T4.0)", font=("Arial", 14, "bold"))
        self.lbl_item_name.pack(anchor="w", pady=2)

        self.lbl_item_id = ctk.CTkLabel(info_layout, text="ID API: T4_BAG", font=("Consolas", 11), text_color="#aaaaaa")
        self.lbl_item_id.pack(anchor="w", pady=2)

        # --- LOG / CONSOLA DE RESULTADOS ---
        self.log_box = ctk.CTkTextbox(self.tab_scan, width=920, height=360, font=("Consolas", 11))
        self.log_box.pack(padx=10, pady=10, fill="both", expand=True)
        self.log_box.insert("0.0", "[SISTEMA] Aplicación inicializada correctamente. Elige tus parámetros e inicia la consulta.\n")

        # --- CONFIGURACIÓN DE IMPUESTOS ---
        lbl_config = ctk.CTkLabel(self.tab_config, text="Ajustes de Mercado", font=("Arial", 14, "bold"))
        lbl_config.pack(padx=20, pady=20, anchor="w")
        ctk.CTkLabel(self.tab_config, text="Impuesto de Mercado (Con Premium): 8.5%", font=("Arial", 12)).pack(padx=20, pady=5, anchor="w")
        ctk.CTkLabel(self.tab_config, text="Estestimación Logística / Transporte: 2.5%", font=("Arial", 12)).pack(padx=20, pady=5, anchor="w")

        # Cargar primera imagen en la interfaz
        self.update_item_preview()

    def get_full_item_id(self):
        tier = self.tier_var.get()
        base_code = ITEMS_MAP.get(self.item_var.get(), "BAG")
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
        
        self.lbl_item_name.configure(text=f"Nombre: {item_name} ({tier} {enc})")
        self.lbl_item_id.configure(text=f"ID API: {item_id}")
        threading.Thread(target=self.load_item_image, args=(item_id,), daemon=True).start()

    def load_item_image(self, item_id):
        # Cabecera de navegador real para evitar el error [Error Imagen]
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        img_url = f"https://render.albiononline.com/v1/item/{item_id}.png?size=90"
        
        try:
            res = requests.get(img_url, headers=headers, timeout=5)
            if res.status_code == 200:
                image_data = Image.open(io.BytesIO(res.content))
                ctk_img = ctk.CTkImage(light_image=image_data, dark_image=image_data, size=(90, 90))
                self.img_label.configure(image=ctk_img, text="")
            else:
                self.img_label.configure(image=None, text="[Sin Imagen]")
        except Exception:
            self.img_label.configure(image=None, text="[Error Red]")

    def log(self, message):
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")

    def execute_arbitrage_scan(self):
        orig = self.orig_var.get()
        dest = self.dest_var.get()
        item_id = self.get_full_item_id()

        if orig == dest:
            self.log("[ERROR] Las ciudades de origen y destino no pueden ser iguales.")
            return

        self.log(f"\n[CONSULTA] Obteniendo precios en vivo de '{item_id}' ({orig} ➡️ {dest})...")
        threading.Thread(target=self.fetch_market_data, args=(orig, dest, item_id), daemon=True).start()

    def fetch_market_data(self, orig, dest, item_id):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        url = f"https://www.albion-online-data.com/api/v2/stats/prices/{item_id}?locations={orig},{dest}"
        
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if not data:
                    self.log("[AVISO] No hay registros de precios en la API para este objeto en estas ubicaciones.")
                    return

                orig_sell_min, orig_buy_max = 0, 0
                dest_sell_min, dest_buy_max = 0, 0

                for entry in data:
                    city = entry.get("city")
                    if city == orig:
                        orig_sell_min = entry.get("sell_price_min", 0)
                        orig_buy_max = entry.get("buy_price_max", 0)
                    elif city == dest:
                        dest_sell_min = entry.get("sell_price_min", 0)
                        dest_buy_max = entry.get("buy_price_max", 0)

                # Priorizar compra por orden de venta existente en Origen
                precio_compra = orig_sell_min if orig_sell_min > 0 else orig_buy_max
                # Priorizar venta en orden de compra directa (Mercado Negro o instantánea) o en venta directa en Destino
                precio_venta = dest_buy_max if dest_buy_max > 0 else dest_sell_min

                tax_rate, logistics_rate = 0.085, 0.025
                costo_total = precio_compra * (1 + logistics_rate)
                ingreso_neto = precio_venta * (1 - tax_rate)
                ganancia = ingreso_neto - costo_total
                margen = (ganancia / costo_total * 100) if costo_total > 0 else 0

                self.log("=" * 70)
                self.log(f" 📦 DETALLE DE MERCADO: {item_id}")
                self.log(f" 📍 Comprar en {orig}: {precio_compra:,} plata")
                self.log(f" 📍 Vender en {dest}: {precio_venta:,} plata")
                if precio_compra == 0 or precio_venta == 0:
                    self.log(" ⚠️ Uno o ambos mercados carecen de datos o ventas recientes en la API pública.")
                else:
                    self.log(f" 📊 Costo Total (con 2.5% transporte): {costo_total:,.1f} plata")
                    self.log(f" 📊 Retorno Neto (tras 8.5% impuesto): {ingreso_neto:,.1f} plata")
                    if ganancia > 0:
                        self.log(f" 💰 GANANCIA NETA: +{ganancia:,.1f} plata (Margen: {margen:.1f}%) [RENTABLE]")
                    else:
                        self.log(f" 📉 PÉRDIDA NETA: {ganancia:,.1f} plata (Margen: {margen:.1f}%) [NO RENTABLE]")
                self.log("=" * 70)
            else:
                self.log(f"[ERROR] Error al consultar servidor de mercado ({res.status_code})")
        except Exception as e:
            self.log(f"[ERROR] Error de conexión de red: {str(e)}")

if __name__ == "__main__":
    app = AlbionArbitrageApp()
    app.mainloop()
