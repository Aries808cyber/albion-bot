import customtkinter as ctk
import requests
import threading

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AlbionArbitrageApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Albion Online - Market Arbitrage Bot")
        self.geometry("900x600")

        self.tabview = ctk.CTkTabview(self, width=860, height=540)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_scan = self.tabview.add("Escaneo de Mercado")
        self.tab_config = self.tabview.add("Configuración")

        top_frame = ctk.CTkFrame(self.tab_scan)
        top_frame.pack(fill="x", padx=10, pady=10)

        self.valid_cities = ["Caerleon", "Brecilien", "Martlock", "Bridgewatch", "Lymhurst", "Fort Sterling", "Thetford"]
        
        self.lbl_orig = ctk.CTkLabel(top_frame, text="Origen:", font=("Arial", 12, "bold"))
        self.lbl_orig.pack(side="left", padx=5)
        self.orig_var = ctk.StringVar(value="Martlock")
        self.orig_menu = ctk.CTkOptionMenu(top_frame, variable=self.orig_var, values=self.valid_cities)
        self.orig_menu.pack(side="left", padx=5)

        self.lbl_dest = ctk.CTkLabel(top_frame, text="Destino:", font=("Arial", 12, "bold"))
        self.lbl_dest.pack(side="left", padx=15)
        self.dest_var = ctk.StringVar(value="Caerleon")
        self.dest_menu = ctk.CTkOptionMenu(top_frame, variable=self.dest_var, values=self.valid_cities)
        self.dest_menu.pack(side="left", padx=5)

        self.btn_run = ctk.CTkButton(top_frame, text="🚀 Ejecutar Escaneo Real", fg_color="#2b8a3e", hover_color="#237032", command=self.execute_arbitrage_scan)
        self.btn_run.pack(side="right", padx=10)

        self.log_box = ctk.CTkTextbox(self.tab_scan, width=820, height=430, font=("Consolas", 11))
        self.log_box.pack(padx=10, pady=10, fill="both", expand=True)
        self.log_box.insert("0.0", "[INFO] Aplicacion lista. Haz clic en 'Ejecutar Escaneo Real' para consultar precios en vivo.\n")

        lbl_config = ctk.CTkLabel(self.tab_config, text="Configuración de Impuestos y Tasas", font=("Arial", 14, "bold"))
        lbl_config.pack(padx=20, pady=20, anchor="w")

        self.lbl_tax = ctk.CTkLabel(self.tab_config, text="Impuesto de Mercado (Premium): 8.5%", font=("Arial", 12))
        self.lbl_tax.pack(padx=20, pady=5, anchor="w")

        self.lbl_logistics = ctk.CTkLabel(self.tab_config, text="Tasa de Logística estimada: 2.5%", font=("Arial", 12))
        self.lbl_logistics.pack(padx=20, pady=5, anchor="w")

    def log(self, message):
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")

    def execute_arbitrage_scan(self):
        orig = self.orig_var.get()
        dest = self.dest_var.get()

        if orig == dest:
            self.log("[ERROR] El origen y el destino no pueden ser iguales.")
            return

        self.log(f"[INFO] Consultando precios en vivo para ruta: {orig} -> {dest}...")
        threading.Thread(target=self.fetch_real_market_data, args=(orig, dest), daemon=True).start()

    def fetch_real_market_data(self, orig, dest):
        items = "T4_BAG,T5_BAG,T4_ORE,T5_ORE,T4_METALBAR,T5_METALBAR,T4_WOOD,T5_WOOD,T4_CLOTH,T5_CLOTH"
        url = f"https://www.albion-online-data.com/api/v2/stats/prices/{items}?locations={orig},{dest}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    self.log("[WARNING] No se encontraron datos de precios para esta ruta en la API.")
                    return
                
                self.log("=" * 70)
                self.log(f" RESULTADOS DE ARBITRAJE: {orig} ➡️ {dest}")
                self.log("=" * 70)
                
                item_prices = {}
                for entry in data:
                    item_id = entry.get("item_id")
                    loc = entry.get("city")
                    if item_id not in item_prices:
                        item_prices[item_id] = {}
                    item_prices[item_id][loc] = {
                        "sell_price": entry.get("sell_price_min", 0),
                        "buy_price": entry.get("buy_price_max", 0)
                    }

                tax_rate = 0.085
                logistics_rate = 0.025

                for item_id, locations in item_prices.items():
                    orig_data = locations.get(orig, {})
                    dest_data = locations.get(dest, {})
                    
                    buy_price = orig_data.get("sell_price", 0)
                    sell_price = dest_data.get("buy_price", 0)
                    if sell_price == 0:
                        sell_price = dest_data.get("sell_price_min", 0)

                    if buy_price > 0 and sell_price > buy_price:
                        cost_with_logistics = buy_price * (1 + logistics_rate)
                        revenue_after_tax = sell_price * (1 - tax_rate)
                        profit = revenue_after_tax - cost_with_logistics
                        margin = (profit / cost_with_logistics) * 100 if cost_with_logistics > 0 else 0

                        self.log(f"📦 Ítem: {item_id}")
                        self.log(f"   Comprar en {orig}: {buy_price:,} plata")
                        self.log(f"   Vender en {dest}: {sell_price:,} plata")
                        self.log(f"   Ganancia Neta: {profit:,.1f} plata ({margin:.1f}%)")
                        self.log("-" * 70)
                    else:
                        self.log(f"📦 Ítem: {item_id} -> Sin margen rentable directo entre {orig} y {dest}.")

                self.log("[INFO] Escaneo en vivo finalizado.")
            else:
                self.log(f"[ERROR] Error al conectar con la API (Código: {response.status_code})")
        except Exception as e:
            self.log(f"[ERROR] Excepción de red: {str(e)}")

if __name__ == "__main__":
    app = AlbionArbitrageApp()
    app.mainloop()
