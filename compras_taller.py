# compras_taller.py
# Módulo de compras: órdenes de compra a proveedores, recepción y costos
# Estilo consistente: fondo oscuro (#0f172a) y botones naranjas ("Menu.TButton")
# Persistencia JSON y exportación a Excel

import os
import json
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import openpyxl

# ==========================
# CONFIGURACIÓN
# ==========================
BASE_DIR = r"C:\RICHARD\RB\2025\Taller_mecánica"
DATA_FILE = os.path.join(BASE_DIR, "compras.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "compras.xlsx")

ESTADOS_COMPRA = ["Solicitada", "Aprobada", "Recibida", "Cancelada"]

# Catálogo de ítems (puedes integrar con tu módulo de repuestos)
CATALOGO = [
    {"codigo": "ACE-1040", "nombre": "Aceite 10W-40", "precio": 45000},
    {"codigo": "FIL-ACE", "nombre": "Filtro de aceite", "precio": 25000},
    {"codigo": "FRE-PAD", "nombre": "Pastillas de freno", "precio": 90000},
    {"codigo": "BAT-12V", "nombre": "Batería 12V", "precio": 320000},
    {"codigo": "AMO-STD", "nombre": "Amortiguador", "precio": 180000},
    {"codigo": "FIL-AIR", "nombre": "Filtro de aire", "precio": 30000},
    {"codigo": "LIQ-FRE", "nombre": "Líquido de frenos", "precio": 28000},
]

# ==========================
# PERSISTENCIA
# ==========================
def ensure_base_dir():
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


def cargar_compras():
    ensure_base_dir()
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def guardar_compras(arr):
    ensure_base_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(arr, f, ensure_ascii=False, indent=2)

def exportar_excel(compras):
    ensure_base_dir()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Compras"

    headers = [
        "Fecha", "Proveedor", "NIT", "Contacto", "Estado",
        "Ítems", "Subtotal", "IVA", "Total", "Observaciones"
    ]
    ws.append(headers)

    for c in compras:
        ws.append([
            c["fecha"],
            c["proveedor"],
            c["nit"],
            c["contacto"],
            c["estado"],
            "; ".join([f'{i["codigo"]} - {i["nombre"]} x{i["cantidad"]} @${i["precio"]:,}' for i in c["items"]]),
            c["subtotal"],
            c["iva"],
            c["total"],
            c["observaciones"]
        ])

    wb.save(OUTPUT_FILE)

# ==========================
# CÁLCULOS
# ==========================
def calcular_totales(items, iva_pct=0.19):
    subtotal = sum(i["cantidad"] * i["precio"] for i in items)
    iva = round(subtotal * iva_pct)
    total = subtotal + iva
    return round(subtotal, 2), iva, round(total, 2)

# ==========================
# UI
# ==========================
class ComprasTallerApp:
    def __init__(self, root):
        ensure_base_dir()
        self.root = root
        self.root.title("🛒 Compras del Taller")
        self.root.geometry("1100x720")
        self.root.configure(bg="#0f172a")

        self.compras = cargar_compras()
        self.items_seleccionados = []

        self._setup_styles()
        self._build_ui()
        self._refresh_tree()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#0f172a", foreground="#e2e8f0")
        style.configure("TEntry", fieldbackground="#ffffff")
        style.configure("TCombobox", fieldbackground="#ffffff")
        style.configure("Menu.TButton", background="#f59e0b", foreground="#111827", font=("Segoe UI Semibold", 11), padding=6)
        style.map("Menu.TButton", background=[("active", "#fbbf24")])
        style.configure("Treeview", background="#0b1220", foreground="#e2e8f0", rowheight=26, fieldbackground="#0b1220")
        style.configure("Title.TLabel", background="#0f172a", foreground="#e2e8f0", font=("Segoe UI", 16, "bold"))

    def _build_ui(self):
        title = ttk.Label(self.root, text="Módulo de Compras", style="Title.TLabel")
        title.pack(pady=10, anchor="w")

        main = tk.Frame(self.root, bg="#0f172a")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        left = tk.Frame(main, bg="#1e293b")
        left.pack(side="left", fill="y", padx=10, pady=10)

        right = tk.Frame(main, bg="#1e293b")
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Variables
        self.proveedor = tk.StringVar()
        self.nit = tk.StringVar()
        self.contacto = tk.StringVar()
        self.estado = tk.StringVar(value=ESTADOS_COMPRA[0])
        self.observaciones = tk.StringVar()

        # Formulario proveedor
        rows = [
            ("Proveedor", self.proveedor, 28),
            ("NIT", self.nit, 20),
            ("Contacto", self.contacto, 28),
        ]
        for i, (label, var, width) in enumerate(rows):
            ttk.Label(left, text=label).grid(row=i, column=0, sticky="e", padx=8, pady=6)
            ttk.Entry(left, textvariable=var, width=width).grid(row=i, column=1, sticky="w", padx=8, pady=6)

        ttk.Label(left, text="Estado").grid(row=len(rows), column=0, sticky="e", padx=8, pady=6)
        ttk.Combobox(left, values=ESTADOS_COMPRA, textvariable=self.estado, state="readonly", width=26).grid(row=len(rows), column=1, sticky="w", padx=8, pady=6)

        ttk.Label(left, text="Observaciones").grid(row=len(rows)+1, column=0, sticky="ne", padx=8, pady=6)
        self.obs_txt = tk.Text(left, height=4, width=30)
        self.obs_txt.grid(row=len(rows)+1, column=1, sticky="w", padx=8, pady=6)

        # Ítems
        ttk.Label(left, text="Ítem catálogo").grid(row=len(rows)+2, column=0, sticky="e", padx=8, pady=6)
        self.item_cb = ttk.Combobox(left, values=[f'{x["codigo"]} - {x["nombre"]}' for x in CATALOGO], state="readonly", width=26)
        self.item_cb.grid(row=len(rows)+2, column=1, sticky="w", padx=8, pady=6)
        self.item_cb.current(0)

        ttk.Label(left, text="Cantidad").grid(row=len(rows)+3, column=0, sticky="e", padx=8, pady=6)
        self.cantidad_var = tk.StringVar(value="1")
        ttk.Entry(left, textvariable=self.cantidad_var, width=10).grid(row=len(rows)+3, column=1, sticky="w", padx=8, pady=6)

        ttk.Button(left, text="Agregar ítem", style="Menu.TButton", command=self._agregar_item).grid(row=len(rows)+4, column=1, sticky="w", padx=8, pady=8)

        self.items_list = tk.Listbox(left, height=8)
        self.items_list.grid(row=len(rows)+5, column=0, columnspan=2, sticky="we", padx=8, pady=6)

        ttk.Button(left, text="Guardar compra", style="Menu.TButton", command=self._guardar_compra).grid(row=len(rows)+6, column=1, sticky="w", padx=8, pady=10)
        ttk.Button(left, text="Limpiar formulario", style="Menu.TButton", command=self._limpiar_form).grid(row=len(rows)+7, column=1, sticky="w", padx=8, pady=6)
        ttk.Button(left, text="Exportar a Excel", style="Menu.TButton", command=self._exportar).grid(row=len(rows)+8, column=1, sticky="w", padx=8, pady=6)

        # Treeview
        cols = ("Proveedor","NIT","Estado","Subtotal","IVA","Total","Fecha")
        self.tree = ttk.Treeview(right, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=140)
        self.tree.pack(fill="both", expand=True)

        btn_frame = tk.Frame(right, bg="#1e293b")
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="✏️ Modificar", style="Menu.TButton", command=self._modificar).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="🗑️ Eliminar", style="Menu.TButton", command=self._eliminar).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="📄 Ver detalle", style="Menu.TButton", command=self._ver_detalle).pack(side="left", padx=6)

    # ==========================
    # ACCIONES
    # ==========================
    def _agregar_item(self):
        try:
            cantidad = float(self.cantidad_var.get())
            if cantidad <= 0:
                raise ValueError()
        except Exception:
            messagebox.showwarning("Validación", "Cantidad debe ser numérica y mayor a 0.")
            return

        sel = self.item_cb.get()
        codigo = sel.split(" - ")[0]
        item = next((x for x in CATALOGO if x["codigo"] == codigo), None)
        if not item:
            messagebox.showwarning("Catálogo", "Ítem no encontrado.")
            return

        reg = {"codigo": item["codigo"], "nombre": item["nombre"], "precio": item["precio"], "cantidad": cantidad}
        self.items_seleccionados.append(reg)
        self.items_list.insert(tk.END, f'{reg["codigo"]} - {reg["nombre"]} x{cantidad} @${reg["precio"]:,}')

    def _guardar_compra(self):
        if not self.items_seleccionados:
            messagebox.showwarning("Validación", "Agrega al menos un ítem.")
            return

        compra = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "proveedor": self.proveedor.get().strip(),
            "nit": self.nit.get().strip(),
            "contacto": self.contacto.get().strip(),
            "estado": self.estado.get(),
            "observaciones": self.obs_txt.get("1.0", "end").strip(),
            "items": self.items_seleccionados.copy()
        }
        subtotal, iva, total = calcular_totales(compra["items"])
        compra["subtotal"] = subtotal
        compra["iva"] = iva
        compra["total"] = total

        self.compras.append(compra)
        guardar_compras(self.compras)
        self._refresh_tree()
        self._limpiar_form()
        messagebox.showinfo("Compras", f"Compra registrada a {compra['proveedor']}.\nTotal: ${total:,}")

    def _refresh_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for c in self.compras:
            self.tree.insert("", "end", values=(
                c["proveedor"], c["nit"], c["estado"],
                f"${c['subtotal']:,}", f"${c['iva']:,}", f"${c['total']:,}", c["fecha"]
            ))

    def _modificar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona una compra para modificar.")
            return
        idx = self.tree.index(sel[0])
        c = self.compras[idx]

        # Cargar en formulario
        self.proveedor.set(c["proveedor"])
        self.nit.set(c["nit"])
        self.contacto.set(c["contacto"])
        self.estado.set(c["estado"])
        self.obs_txt.delete("1.0", "end")
        self.obs_txt.insert("1.0", c["observaciones"])
        self.items_seleccionados = c["items"].copy()
        self.items_list.delete(0, tk.END)
        for i in self.items_seleccionados:
            self.items_list.insert(tk.END, f'{i["codigo"]} - {i["nombre"]} x{i["cantidad"]} @${i["precio"]:,}')

        # Eliminar para reemplazar al guardar
        self.compras.pop(idx)
        self._refresh_tree()

    def _eliminar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona una compra para eliminar.")
            return
        idx = self.tree.index(sel[0])
        if messagebox.askyesno("Confirmar", "¿Eliminar la compra seleccionada?"):
            self.compras.pop(idx)
            guardar_compras(self.compras)
            self._refresh_tree()
            messagebox.showinfo("Eliminado", "Compra eliminada.")

    def _ver_detalle(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona una compra para ver detalle.")
            return
        idx = self.tree.index(sel[0])
        c = self.compras[idx]

        top = tk.Toplevel(self.root)
        top.title(f"Detalle compra - {c['proveedor']}")
        top.configure(bg="#0f172a")

        lines = [
            f"Fecha: {c['fecha']}",
            f"Proveedor: {c['proveedor']}  |  NIT: {c['nit']}  |  Contacto: {c['contacto']}",
            f"Estado: {c['estado']}",
            f"Observaciones: {c['observaciones']}",
            f"Subtotal: ${c['subtotal']:,}  |  IVA: ${c['iva']:,}  |  Total: ${c['total']:,}",
            "Ítems:"
        ]
        for ln in lines:
            tk.Label(top, text=ln, bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=12, pady=3)
        for i in c["items"]:
            tk.Label(top, text=f'• {i["codigo"]} - {i["nombre"]} x{i["cantidad"]} @${i["precio"]:,}', bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=24, pady=2)

        ttk.Button(top, text="Cerrar", style="Menu.TButton", command=top.destroy).pack(pady=10)

    def _exportar(self):
        if not self.compras:
            messagebox.showwarning("Sin datos", "No hay compras para exportar.")
            return
        try:
            exportar_excel(self.compras)
            messagebox.showinfo("Exportado", f"Archivo Excel generado en:\n{OUTPUT_FILE}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

    def _limpiar_form(self):
        self.proveedor.set("")
        self.nit.set("")
        self.contacto.set("")
        self.estado.set(ESTADOS_COMPRA[0])
        self.obs_txt.delete("1.0", "end")
        self.items_seleccionados = []
        self.items_list.delete(0, tk.END)
        self.cantidad_var.set("1")
        self.item_cb.current(0)

# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    ensure_base_dir()
    root = tk.Tk()
    app = ComprasTallerApp(root)
    root.mainloop()
