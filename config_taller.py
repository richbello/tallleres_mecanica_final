# config_taller.py
# Módulo de configuración general: rutas, parámetros, estilo, nómina, impuestos
# Mantiene estilo: fondo oscuro (#0f172a), paneles (#1e293b), botones naranjas ("Menu.TButton")

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

BASE_DIR = r"C:\RICHARD\RB\2025\Taller_mecánica"
CONFIG_FILE = os.path.join(BASE_DIR, "config_taller.json")

DEFAULTS = {
    "paths": {
        "base_dir": BASE_DIR,
        "export_dir": BASE_DIR,
        "icons_dir": os.path.join(BASE_DIR, "icons")
    },
    "style": {
        "primary_bg": "#0f172a",
        "panel_bg": "#1e293b",
        "button_bg": "#f59e0b",
        "button_hover": "#fbbf24",
        "text_fg": "#e2e8f0"
    },
    "nomina": {
        "smmlv": 1300000,
        "aux_transporte": 162000,
        "salud_empleado_pct": 0.04,
        "pension_empleado_pct": 0.04
    },
    "impuestos": {
        "iva_pct": 0.19
    },
    "seguridad": {
        "session_timeout_seconds": 600,
        "clipboard_clear_seconds": 15
    }
}

def _ensure_base_dir():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR, exist_ok=True)
        
def _configurar_estilos(self):
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Menu.TButton",
                    background="#f59e0b",
                    foreground="#111827",
                    font=("Segoe UI Semibold", 11),
                    padding=8,
                    relief="flat",
                    borderwidth=0)
    style.map("Menu.TButton", background=[("active", "#fbbf24")])
    style.configure("Form.TEntry",
                    fieldbackground="#ffffff",
                    foreground="#111827",
                    padding=4)
    style.configure("Treeview",
                    background="#1e293b",
                    foreground="#e2e8f0",
                    fieldbackground="#1e293b",
                    rowheight=26)
    style.configure("Treeview.Heading",
                    background="#f59e0b",
                    foreground="#111827",
                    font=("Segoe UI Semibold", 11))


def _load_config():
    _ensure_base_dir()
    if not os.path.exists(CONFIG_FILE):
        return DEFAULTS.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # merge con defaults para claves faltantes
        def deep_merge(d, ref):
            for k, v in ref.items():
                if k not in d:
                    d[k] = v
                else:
                    if isinstance(v, dict) and isinstance(d[k], dict):
                        deep_merge(d[k], v)
        deep_merge(data, DEFAULTS)
        return data
    except Exception:
        return DEFAULTS.copy()

def _save_config(cfg):
    _ensure_base_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

class ConfigTallerApp:
    def __init__(self, root):
        _ensure_base_dir()
        self.root = root
        self.root.title("⚙️ Configuración del Taller")
        self.root.geometry("1000x680")
        self.root.configure(bg="#0f172a")

        self.cfg = _load_config()
        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#0f172a", foreground="#e2e8f0")
        style.configure("Title.TLabel", background="#0f172a", foreground="#e2e8f0", font=("Segoe UI", 16, "bold"))
        style.configure("Menu.TButton", background="#f59e0b", foreground="#111827", font=("Segoe UI Semibold", 11), padding=6)
        style.map("Menu.TButton", background=[("active", "#fbbf24")])
        style.configure("Card.TFrame", background="#1e293b")
        style.configure("TEntry", fieldbackground="#ffffff")
        style.configure("TCombobox", fieldbackground="#ffffff")

    def _build_ui(self):
        ttk.Label(self.root, text="Configuración general del sistema", style="Title.TLabel").pack(anchor="w", padx=12, pady=10)

        main = tk.Frame(self.root, bg="#0f172a")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        # Notebook por secciones
        nb = ttk.Notebook(main)
        nb.pack(fill="both", expand=True)

        self._tab_paths(nb)
        self._tab_style(nb)
        self._tab_nomina(nb)
        self._tab_impuestos(nb)
        self._tab_seguridad(nb)

        # acciones
        actions = tk.Frame(self.root, bg="#0f172a")
        actions.pack(fill="x", padx=12, pady=8)
        ttk.Button(actions, text="💾 Guardar configuración", style="Menu.TButton", command=self._guardar).pack(side="left", padx=6)
        ttk.Button(actions, text="↩️ Restaurar valores por defecto", style="Menu.TButton", command=self._restaurar).pack(side="left", padx=6)

    def _tab_paths(self, nb):
        frame = ttk.Frame(nb, style="Card.TFrame")
        nb.add(frame, text="Rutas")

        # Variables
        self.base_dir = tk.StringVar(value=self.cfg["paths"]["base_dir"])
        self.export_dir = tk.StringVar(value=self.cfg["paths"]["export_dir"])
        self.icons_dir = tk.StringVar(value=self.cfg["paths"]["icons_dir"])

        rows = [
            ("Carpeta base", self.base_dir),
            ("Carpeta exportación", self.export_dir),
            ("Carpeta íconos", self.icons_dir),
        ]
        for i, (label, var) in enumerate(rows):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="e", padx=10, pady=8)
            ttk.Entry(frame, textvariable=var, width=60).grid(row=i, column=1, sticky="w", padx=10, pady=8)
            ttk.Button(frame, text="📂 Seleccionar", style="Menu.TButton",
                       command=lambda v=var: self._select_dir(v)).grid(row=i, column=2, padx=10, pady=8)

    def _tab_style(self, nb):
        frame = ttk.Frame(nb, style="Card.TFrame")
        nb.add(frame, text="Estilo")

        self.primary_bg = tk.StringVar(value=self.cfg["style"]["primary_bg"])
        self.panel_bg = tk.StringVar(value=self.cfg["style"]["panel_bg"])
        self.button_bg = tk.StringVar(value=self.cfg["style"]["button_bg"])
        self.button_hover = tk.StringVar(value=self.cfg["style"]["button_hover"])
        self.text_fg = tk.StringVar(value=self.cfg["style"]["text_fg"])

        rows = [
            ("Fondo principal", self.primary_bg),
            ("Fondo paneles", self.panel_bg),
            ("Botón (naranja)", self.button_bg),
            ("Hover botón", self.button_hover),
            ("Texto (claro)", self.text_fg),
        ]
        for i, (label, var) in enumerate(rows):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="e", padx=10, pady=8)
            ttk.Entry(frame, textvariable=var, width=20).grid(row=i, column=1, sticky="w", padx=10, pady=8)

    def _tab_nomina(self, nb):
        frame = ttk.Frame(nb, style="Card.TFrame")
        nb.add(frame, text="Nómina")

        self.smmlv = tk.StringVar(value=str(self.cfg["nomina"]["smmlv"]))
        self.aux_transporte = tk.StringVar(value=str(self.cfg["nomina"]["aux_transporte"]))
        self.salud_pct = tk.StringVar(value=str(self.cfg["nomina"]["salud_empleado_pct"]))
        self.pension_pct = tk.StringVar(value=str(self.cfg["nomina"]["pension_empleado_pct"]))

        rows = [
            ("SMMLV (COP)", self.smmlv),
            ("Auxilio transporte (COP)", self.aux_transporte),
            ("Salud empleado (%)", self.salud_pct),
            ("Pensión empleado (%)", self.pension_pct),
        ]
        for i, (label, var) in enumerate(rows):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="e", padx=10, pady=8)
            ttk.Entry(frame, textvariable=var, width=20).grid(row=i, column=1, sticky="w", padx=10, pady=8)

    def _tab_impuestos(self, nb):
        frame = ttk.Frame(nb, style="Card.TFrame")
        nb.add(frame, text="Impuestos")

        self.iva_pct = tk.StringVar(value=str(self.cfg["impuestos"]["iva_pct"]))
        ttk.Label(frame, text="IVA (%)").grid(row=0, column=0, sticky="e", padx=10, pady=8)
        ttk.Entry(frame, textvariable=self.iva_pct, width=20).grid(row=0, column=1, sticky="w", padx=10, pady=8)

    def _tab_seguridad(self, nb):
        frame = ttk.Frame(nb, style="Card.TFrame")
        nb.add(frame, text="Seguridad")

        self.session_timeout = tk.StringVar(value=str(self.cfg["seguridad"]["session_timeout_seconds"]))
        self.clipboard_clear = tk.StringVar(value=str(self.cfg["seguridad"]["clipboard_clear_seconds"]))

        rows = [
            ("Tiempo de sesión (seg)", self.session_timeout),
            ("Limpiar portapapeles (seg)", self.clipboard_clear),
        ]
        for i, (label, var) in enumerate(rows):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="e", padx=10, pady=8)
            ttk.Entry(frame, textvariable=var, width=20).grid(row=i, column=1, sticky="w", padx=10, pady=8)

    def _select_dir(self, var):
        d = filedialog.askdirectory()
        if d:
            var.set(d)

    def _guardar(self):
        try:
            cfg = {
                "paths": {
                    "base_dir": self.base_dir.get().strip(),
                    "export_dir": self.export_dir.get().strip(),
                    "icons_dir": self.icons_dir.get().strip()
                },
                "style": {
                    "primary_bg": self.primary_bg.get().strip(),
                    "panel_bg": self.panel_bg.get().strip(),
                    "button_bg": self.button_bg.get().strip(),
                    "button_hover": self.button_hover.get().strip(),
                    "text_fg": self.text_fg.get().strip()
                },
                "nomina": {
                    "smmlv": float(self.smmlv.get()),
                    "aux_transporte": float(self.aux_transporte.get()),
                    "salud_empleado_pct": float(self.salud_pct.get()),
                    "pension_empleado_pct": float(self.pension_pct.get())
                },
                "impuestos": {
                    "iva_pct": float(self.iva_pct.get())
                },
                "seguridad": {
                    "session_timeout_seconds": int(float(self.session_timeout.get())),
                    "clipboard_clear_seconds": int(float(self.clipboard_clear.get()))
                }
            }
            _save_config(cfg)
            self.cfg = cfg
            messagebox.showinfo("Configuración", "Parámetros guardados correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def _restaurar(self):
        if not messagebox.askyesno("Confirmar", "¿Restaurar valores por defecto?"):
            return
        try:
            _save_config(DEFAULTS.copy())
            self.cfg = _load_config()
            # recargar UI
            self.base_dir.set(self.cfg["paths"]["base_dir"])
            self.export_dir.set(self.cfg["paths"]["export_dir"])
            self.icons_dir.set(self.cfg["paths"]["icons_dir"])
            self.primary_bg.set(self.cfg["style"]["primary_bg"])
            self.panel_bg.set(self.cfg["style"]["panel_bg"])
            self.button_bg.set(self.cfg["style"]["button_bg"])
            self.button_hover.set(self.cfg["style"]["button_hover"])
            self.text_fg.set(self.cfg["style"]["text_fg"])
            self.smmlv.set(str(self.cfg["nomina"]["smmlv"]))
            self.aux_transporte.set(str(self.cfg["nomina"]["aux_transporte"]))
            self.salud_pct.set(str(self.cfg["nomina"]["salud_empleado_pct"]))
            self.pension_pct.set(str(self.cfg["nomina"]["pension_empleado_pct"]))
            self.iva_pct.set(str(self.cfg["impuestos"]["iva_pct"]))
            self.session_timeout.set(str(self.cfg["seguridad"]["session_timeout_seconds"]))
            self.clipboard_clear.set(str(self.cfg["seguridad"]["clipboard_clear_seconds"]))
            messagebox.showinfo("Configuración", "Valores por defecto restaurados.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo restaurar: {e}")

if __name__ == "__main__":
    _ensure_base_dir()
    root = tk.Tk()
    app = ConfigTallerApp(root)
    root.mainloop()
