# alertas_taller.py — Sistema de alarmas preventivas
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

# Ejemplo de base de datos en memoria (puedes reemplazar con JSON/SQLite)
vehiculos = [
    {"placa": "CAR001", "km_actual": 15000, "km_ultimo_cambio": 10000, "intervalo_km": 5000,
     "fecha_ultimo_cambio": datetime(2025, 11, 15), "intervalo_dias": 180},
    {"placa": "CAR002", "km_actual": 22000, "km_ultimo_cambio": 17000, "intervalo_km": 5000,
     "fecha_ultimo_cambio": datetime(2025, 11, 20), "intervalo_dias": 180},
    {"placa": "CAR003", "km_actual": 30500, "km_ultimo_cambio": 26000, "intervalo_km": 5000,
     "fecha_ultimo_cambio": datetime(2025, 11, 25), "intervalo_dias": 180},
    {"placa": "CAR004", "km_actual": 41000, "km_ultimo_cambio": 36000, "intervalo_km": 5000,
     "fecha_ultimo_cambio": datetime(2025, 11, 28), "intervalo_dias": 180},
    {"placa": "CAR005", "km_actual": 52000, "km_ultimo_cambio": 47000, "intervalo_km": 5000,
     "fecha_ultimo_cambio": datetime(2025, 12, 1), "intervalo_dias": 180},
    {"placa": "CAR006", "km_actual": 61000, "km_ultimo_cambio": 56000, "intervalo_km": 5000,
     "fecha_ultimo_cambio": datetime(2025, 12, 3), "intervalo_dias": 180},
    {"placa": "CAR007", "km_actual": 72000, "km_ultimo_cambio": 67000, "intervalo_km": 5000,
     "fecha_ultimo_cambio": datetime(2025, 12, 5), "intervalo_dias": 180},
    {"placa": "CAR008", "km_actual": 83000, "km_ultimo_cambio": 78000, "intervalo_km": 5000,
     "fecha_ultimo_cambio": datetime(2025, 12, 7), "intervalo_dias": 180},
    {"placa": "CAR009", "km_actual": 94000, "km_ultimo_cambio": 89000, "intervalo_km": 5000,
     "fecha_ultimo_cambio": datetime(2025, 12, 9), "intervalo_dias": 180},
    {"placa": "CAR010", "km_actual": 105000, "km_ultimo_cambio": 100000, "intervalo_km": 5000,
     "fecha_ultimo_cambio": datetime(2025, 12, 11), "intervalo_dias": 180},
    # ... puedes continuar hasta CAR040
]

class AlertasTallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🚨 Sistema de Alarmas - Taller Mecánico")
        self.root.geometry("600x400")
        self.root.configure(bg="#0f172a")

        self._setup_styles()
        self._build_ui()

        # Verificación automática cada 60 segundos
        self._programar_alertas()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Menu.TButton",
                        background="#f59e0b",
                        foreground="#111827",
                        font=("Segoe UI Semibold", 12),
                        padding=8)
        style.map("Menu.TButton", background=[("active", "#fbbf24")])
        style.configure("TLabel", background="#0f172a", foreground="#e2e8f0")

    def _build_ui(self):
        ttk.Label(self.root, text="Vehículos registrados", style="TLabel", font=("Segoe UI", 14)).pack(pady=10)

        self.tree = ttk.Treeview(self.root, columns=("placa","km","ultimo","proximo"), show="headings", height=8)
        self.tree.heading("placa", text="Placa")
        self.tree.heading("km", text="Km actual")
        self.tree.heading("ultimo", text="Último cambio")
        self.tree.heading("proximo", text="Próximo cambio (Km)")
        self.tree.pack(fill="both", expand=True, padx=12, pady=12)

        ttk.Button(self.root, text="Verificar ahora", style="Menu.TButton", command=self.verificar_alertas).pack(pady=10)

        self._refresh_tree()

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for v in vehiculos:
            proximo_km = v["km_ultimo_cambio"] + v["intervalo_km"]
            self.tree.insert("", "end", values=(v["placa"], v["km_actual"], v["km_ultimo_cambio"], proximo_km))

    def verificar_alertas(self):
        hoy = datetime.now()
        for v in vehiculos:
            km_restante = v["intervalo_km"] - (v["km_actual"] - v["km_ultimo_cambio"])
            dias_restantes = v["intervalo_dias"] - (hoy - v["fecha_ultimo_cambio"]).days

            if km_restante <= 500 or dias_restantes <= 45:  # alerta si faltan menos de 45 días
                messagebox.showwarning("Alerta de mantenimiento",
                                       f"Vehículo {v['placa']} está próximo a cambio de aceite.\n"
                                       f"Km restantes: {km_restante}\n"
                                       f"Días restantes: {dias_restantes}")

    def _programar_alertas(self):
        self.verificar_alertas()
        self.root.after(60000, self._programar_alertas)  # cada 60 segundos

# ---------------------------
# Arranque independiente
# ---------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = AlertasTallerApp(root)
    root.mainloop()
