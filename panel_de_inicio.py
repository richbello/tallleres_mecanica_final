# panel_inicio.py — Login + Panel moderno con fondo elegante, grid 3x4 y botones con íconos
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import subprocess, sys, os

from security_core import module_opened, start_user_session, end_user_session, button_clicked

# Credenciales de acceso
USUARIO_VALIDO = "taller2026"
CLAVE_VALIDA = "taller.2026**"

# Rutas base y recursos
BASE_DIR = r"C:\RICHARD\RB\2025\Taller_mecánica"
BG_IMAGE_PATH = os.path.join(BASE_DIR, "panel_de_inicio_fondo.png")
ICONS_DIR = os.path.join(BASE_DIR, "icons")

# Definición de módulos
MODULOS = [
    ("📋 Órdenes de Trabajo", "python_ordenes_taller.py", "orders.png"),
    ("📊 Ventas", "ventas_taller.py", "sales.png"),
    ("👥 Clientes", "clientes_taller.py", "clients.png"),
    ("🛠 Proveedores", "proveedores_taller.py", "providers.png"),
    ("📦 Inventario", "modulo_inventario.py", "inventory.png"),
    ("🔒 Seguridad", "seguridad_taller.py", "security.png"),
    ("💳 Pasarela de Pagos", "pasarela_pagos.py", "payments.png"),
    ("🧾 Nómina", "nomina_taller.py", "payroll.png"),
    ("🛒 Compras", "compras_taller.py", "purchases.png"),
    ("💼 Cartera", "cartera_taller.py", "portfolio.png"),
    ("📈 Reportes", "reportes_taller.py", "reports.png"),
    ("⚙️ Configuración", "config_taller.py", "settings.png"),
]

# ---------------------------
# LOGIN
# ---------------------------
class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Acceso al Taller Mecánico")
        self.root.geometry("560x360")
        self.root.minsize(520, 340)
        self.root.configure(bg="#0f172a")

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Login.TLabel", background="#1e293b", foreground="#e2e8f0", font=("Segoe UI", 11))
        style.configure("Menu.TButton",
                        background="#f59e0b",
                        foreground="#111827",
                        font=("Segoe UI Semibold", 12),
                        padding=8,
                        relief="flat",
                        borderwidth=0)
        style.map("Menu.TButton", background=[("active", "#fbbf24")])

    def _build_ui(self):
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)

        self.card = tk.Frame(self.canvas, bg="#1e293b", padx=28, pady=24)
        self.card_win = self.canvas.create_window(self.root.winfo_width()//2,
                                                  self.root.winfo_height()//2,
                                                  window=self.card, anchor="center")

        ttk.Label(self.card, text="Usuario:", style="Login.TLabel").grid(row=0, column=0, sticky="e", pady=10, padx=6)
        self.user_var = tk.StringVar()
        ttk.Entry(self.card, textvariable=self.user_var, width=28).grid(row=0, column=1, pady=10, padx=6)

        ttk.Label(self.card, text="Clave:", style="Login.TLabel").grid(row=1, column=0, sticky="e", pady=10, padx=6)
        self.pass_var = tk.StringVar()
        ttk.Entry(self.card, textvariable=self.pass_var, width=28, show="*").grid(row=1, column=1, pady=10, padx=6)

        ttk.Button(self.card, text="Ingresar", style="Menu.TButton", command=self._login).grid(row=2, column=0, columnspan=2, pady=18)

    def _build_background(self, w, h):
        bg_img = None
        if os.path.exists(BG_IMAGE_PATH):
            try:
                bg_img = Image.open(BG_IMAGE_PATH).convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
            except Exception:
                bg_img = None
        if bg_img is None:
            bg_img = Image.new("RGBA", (w, h), "#0f172a")
            draw = ImageDraw.Draw(bg_img)
            for i in range(h):
                ratio = i / max(1, h)
                color = (
                    int(15 + (30 - 15) * ratio),
                    int(23 + (41 - 23) * ratio),
                    int(42 + (59 - 42) * ratio),
                    255
                )
                draw.line([(0, i), (w, i)], fill=color)
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 80))
        bg_img = Image.alpha_composite(bg_img, overlay)
        return ImageTk.PhotoImage(bg_img)

    def _on_resize(self, event):
        w, h = event.width, event.height
        self.bg_image = self._build_background(w, h)
        if getattr(self, "bg_id", None) is None:
            self.bg_id = self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")
        else:
            self.canvas.itemconfig(self.bg_id, image=self.bg_image)
        self.canvas.coords(self.card_win, w//2, h//2)

    def _login(self):
        user = self.user_var.get().strip()
        pwd = self.pass_var.get().strip()
        if user == USUARIO_VALIDO and pwd == CLAVE_VALIDA:
            self.root.destroy()
            main_root = tk.Tk()
            start_user_session()
            PanelInicio(main_root)
            main_root.mainloop()
        else:
            messagebox.showerror("Acceso denegado", "Usuario o clave incorrectos.")

# ---------------------------
# PANEL DE INICIO
# ---------------------------
class PanelInicio:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel de Inicio - Taller Mecánico")
        self.root.geometry("1200x750")
        self.root.minsize(1024, 680)
        self.root.resizable(True, True)

        self._configurar_estilos()
        self._construir_layout()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Menu.TButton",
                        background="#f59e0b",
                        foreground="#111827",
                        font=("Segoe UI Semibold", 13),
                        padding=10,
                        relief="flat",
                        borderwidth=0)
        style.map("Menu.TButton", background=[("active", "#fbbf24")])
        style.configure("Title.TLabel", background="#0f172a", foreground="#e2e8f0", font=("Segoe UI", 18, "bold"))
        style.configure("Sub.TLabel", background="#0f172a", foreground="#94a3b8", font=("Segoe UI", 11))

    def _construir_layout(self):
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Título superior
        title_frame = tk.Frame(self.canvas, bg="#0f172a")
        self.title_window = self.canvas.create_window(0, 0, window=title_frame, anchor="n")
        ttk.Label(title_frame, text="Panel de Inicio", style="Title.TLabel").pack(anchor="w", padx=24, pady=(16, 4))
        ttk.Label(title_frame, text="Taller Mecánico — Operación integral", style="Sub.TLabel").pack(anchor="w", padx=24, pady=(0, 12))

        # Grid central de módulos
        self.grid_frame = tk.Frame(self.canvas, bg="#0f172a")
        self.grid_window = self.canvas.create_window(0, 0, window=self.grid_frame, anchor="center")

        cols = 3
        for idx, (texto, archivo, icon_name) in enumerate(MODULOS):
            card = tk.Frame(self.grid_frame, bg="#1e293b", padx=12, pady=12)
            card.grid(row=idx // cols, column=idx % cols, padx=18, pady=18, sticky="nsew")
            self._build_card(card, texto, archivo, icon_name)

        for c in range(cols):
            self.grid_frame.grid_columnconfigure(c, weight=1)

        w = self.root.winfo_width()
        h = self.root.winfo_height()
        self.bg_image = self._build_background(w, h)
        self.bg_id = self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

    def _build_background(self, w, h):
        bg_img = None
        if os.path.exists(BG_IMAGE_PATH):
            try:
                bg_img = Image.open(BG_IMAGE_PATH).convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
            except Exception:
                bg_img = None
        if bg_img is None:
            bg_img = Image.new("RGBA", (w, h), "#0f172a")
            draw = ImageDraw.Draw(bg_img)
            for i in range(h):
                ratio = i / max(1, h)
                color = (
                    int(15 + (30 - 15) * ratio),
                    int(23 + (41 - 23) * ratio),
                    int(42 + (59 - 42) * ratio),
                    255
                )
                draw.line([(0, i), (w, i)], fill=color)
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 80))
        bg_img = Image.alpha_composite(bg_img, overlay)
        return ImageTk.PhotoImage(bg_img)

    def _load_icon(self, icon_name, size=(28, 28)):
        path = os.path.join(ICONS_DIR, icon_name)
        if not os.path.exists(path):
            return None
        try:
            img = Image.open(path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def _build_card(self, parent, texto, archivo, icon_name):
        inner = tk.Frame(parent, bg="#1e293b")
        inner.pack(fill="both", expand=True, padx=12, pady=12)

        icon = self._load_icon(icon_name)
        if icon:
            btn = ttk.Button(inner, text=texto, style="Menu.TButton",
                             command=lambda a=archivo, t=texto: self.abrir_modulo(a, t))
            btn.configure(compound="left")
            img_lbl = tk.Label(inner, image=icon, bg="#1e293b")
            img_lbl.image = icon
            img_lbl.pack(side="left", padx=(4, 10))
            btn.pack(side="left", fill="x", expand=True, padx=(0, 4), pady=2)
        else:
            btn = ttk.Button(inner, text=texto, style="Menu.TButton",
                             command=lambda a=archivo, t=texto: self.abrir_modulo(a, t))
            btn.pack(fill="x", expand=True, padx=4, pady=2)

        def on_enter(e): inner.configure(bg="#223047")
        def on_leave(e): inner.configure(bg="#1e293b")
        inner.bind("<Enter>", on_enter)
        inner.bind("<Leave>", on_leave)

    def abrir_modulo(self, archivo, texto):
        # Detecta si corre como .exe empaquetado
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        ruta = os.path.join(base_path, archivo)
        module_opened(archivo, "opened_from_panel")
        button_clicked("PanelInicio", texto, f"open:{archivo}")

        if not os.path.exists(ruta):
            posible = os.path.join(BASE_DIR, archivo)
            if os.path.exists(posible):
                ruta = posible
            else:
                messagebox.showerror("Archivo no encontrado",
                                     f"No se encontró el módulo:\n{archivo}\n\nBuscado en:\n{ruta}")
                return
        try:
            subprocess.Popen([sys.executable, ruta])
        except Exception as e:
            messagebox.showerror("Error al abrir módulo",
                                 f"No se pudo ejecutar {archivo}.\n\nDetalle:\n{e}")

    def _on_canvas_configure(self, event):
        w, h = event.width, event.height
        try:
            self.bg_image = self._build_background(w, h)
            self.canvas.itemconfig(self.bg_id, image=self.bg_image)
        except Exception:
            pass

        self.canvas.coords(self.title_window, w // 2 - 420, 0)
        grid_top = int(h * 0.18)
        self.canvas.coords(self.grid_window, w // 2, grid_top + (h - grid_top) // 2)

    def _on_close(self):
        end_user_session()
        self.root.destroy()

# ---------------------------
# Importación silenciosa para PyInstaller
# ---------------------------
import tkinter as tk
from tkinter import ttk

# Importa tus módulos
from clientes_taller import ClientesTaller
from compras_taller import ComprasTallerApp
from config_taller import ConfigTallerApp
from modulo_inventario import InventarioTaller
from nomina_taller import NominaTallerApp
from proveedores_taller import ProveedoresTaller
from python_ordenes_taller import OrdenesTallerApp
from reportes_taller import ReportesTallerApp
from Seguridad_taller import SeguridadTaller
from ventas_taller import VentasTaller
from cartera_taller import CarteraTallerApp

class PanelInicio:
    def __init__(self, root):
        self.root = root
        self.root.title("🏠 Panel Principal - Taller Mecánico")
        self.root.geometry("600x500")
        self.root.configure(bg="#0f172a")

        ttk.Button(root, text="💰 Cartera", command=self.abrir_cartera).pack(pady=6)
        ttk.Button(root, text="👥 Clientes", command=self.abrir_clientes).pack(pady=6)
        ttk.Button(root, text="🛒 Compras", command=self.abrir_compras).pack(pady=6)
        ttk.Button(root, text="⚙️ Configuración", command=self.abrir_config).pack(pady=6)
        ttk.Button(root, text="💳 Pasarela Pagos", command=self.abrir_pasarela).pack(pady=6)
        ttk.Button(root, text="📦 Inventario", command=self.abrir_inventario).pack(pady=6)
        ttk.Button(root, text="👔 Nómina", command=self.abrir_nomina).pack(pady=6)
        ttk.Button(root, text="🛠 Proveedores", command=self.abrir_proveedores).pack(pady=6)
        ttk.Button(root, text="📑 Órdenes", command=self.abrir_ordenes).pack(pady=6)
        ttk.Button(root, text="📊 Reportes", command=self.abrir_reportes).pack(pady=6)
        ttk.Button(root, text="🔒 Seguridad", command=self.abrir_seguridad).pack(pady=6)
        ttk.Button(root, text="💵 Ventas", command=self.abrir_ventas).pack(pady=6)

    def abrir_cartera(self): win = tk.Toplevel(self.root); CarteraTallerApp(win)
    def abrir_clientes(self): win = tk.Toplevel(self.root); ClientesTaller(win)
    def abrir_compras(self): win = tk.Toplevel(self.root); ComprasTallerApp(win)
    def abrir_config(self): win = tk.Toplevel(self.root); ConfigTallerApp(win)
    
    def abrir_inventario(self): win = tk.Toplevel(self.root); InventarioTaller(win)
    def abrir_nomina(self): win = tk.Toplevel(self.root); NominaTallerApp(win)     
    def abrir_proveedores(self): win = tk.Toplevel(self.root); ProveedoresTaller(win)
    def abrir_ordenes(self): win = tk.Toplevel(self.root); OrdenesTallerApp(win)
    def abrir_reportes(self): win = tk.Toplevel(self.root); ReportesTallerApp(win)
    def abrir_seguridad(self): win = tk.Toplevel(self.root); SeguridadTaller(win)
    def abrir_ventas(self): win = tk.Toplevel(self.root); VentasTaller(win)
    def abrir_pasarela(self): win = tk.Toplevel(self.root); PasarelaPagosApp(win)


    
    
    
    

if __name__ == "__main__":
    root = tk.Tk()
    app = PanelInicio(root)
    root.mainloop()



