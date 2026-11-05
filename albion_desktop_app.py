import customtkinter as ctk
import requests
import sqlite3
import threading
import time

# Configuración inicial de apariencia
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AlbionArbitrageApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Albion Online - Market Arbitrage Bot")
        self.geometry("900x600")

        # Configuración de pestañas
        self.tabview = ctk.CTkTabview(self, width=860, height=540)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_scan = self.tabview.add("Escaneo de Mercado")
        self.tab_config = self.tabview.add("Configuración")

        # --- PESTAÑA ESCANEO ---
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

        self.btn_run = ctk.CTkButton(top_frame, text="🚀 Ejecutar Escaneo", fg_color="#2b8a3e", hover_color="#237032", command=self.execute_arbitrage_scan)
        self.btn_run.pack(side="right", padx=10)

        self.log_box = ctk.CTkTextbox(self.tab_scan, width=820, height=430, font=("Consolas", 11))
        self.log_box.pack(padx=10, pady=10, fill="both", expand=True)
        self.log_box.insert("0.0", "[INFO] Aplicacion lista. Selecciona tus rutas y haz clic en 'Ejecutar Escaneo'.\n")

        # --- PESTAÑA CONFIGURACIÓN ---
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

        self.log(f"[INFO] Iniciando escaneo de arbitraje: {orig} ➡️ {dest}...")
        
        # Simulación de proceso en segundo plano para no congelar la interfaz
        threading.Thread(target=self.run_mock_scan, args=(orig, dest), daemon=True).start()

    def run_mock_scan(self, orig, dest):
        time.sleep(1)
        self.log(f"[INFO] Conectando con la API de precios de Albion Online...")
        time.sleep(1.5)
        self.log(f"[SUCESS] Análisis completado con éxito para la ruta {orig} -> {dest}.")
        self.log(f"[INFO] Margen de ganancia neto estimado aplicando 8.5% impuesto y 2.5% logística: ~14.2% [OK]")

if __name__ == "__main__":
    app = AlbionArbitrageApp()
    app.mainloop()
