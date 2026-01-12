# cartera_taller.py
# Módulo de cartera: cuentas por cobrar, abonos, estados y vencimientos
# Estilo consistente: fondo oscuro (#0f172a) y botones naranjas ("Menu.TButton")
# Persistencia JSON y exportación a Excel

import os
import json
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import openpyxl

# ==========================
# CONFIGURACIÓN
# ==========================
BASE_DIR = r"C:\RICHARD\RB\2025\Taller_mecánica"
DATA_FILE = os.path.join(BASE_DIR, "cartera.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "cartera.xlsx")

ESTADOS_CARTERA = ["Pendiente", "Parcial", "Pagada", "Vencida"]

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


def cargar_cartera():
    ensure_base_dir()
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def guardar_cartera(arr):
    ensure_base_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(arr, f, ensure_ascii=False, indent=2)

def exportar_excel(registros):
    ensure_base_dir()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Cartera"

    headers = [
        "Fecha", "Cliente", "Documento", "Orden/Factura", "Estado",
        "Valor factura", "Abonos", "Saldo", "Vencimiento", "Días mora", "Observaciones"
    ]
    ws.append(headers)

    for r in registros:
        ws.append([
            r["fecha"],
            r["cliente"],
            r["documento"],
            r["referencia"],
            r["estado"],
            r["valor_factura"],
            sum(a["monto"] for a in r["abonos"]),
            r["saldo"],
            r["vencimiento"],
            r["dias_mora"],
            r["observaciones"]
        ])

    wb.save(OUTPUT_FILE)

# ==========================
# CÁLCULOS
# ==========================
def calcular_estado(saldo, vencimiento_iso):
    hoy = datetime.now().date()
    venc = datetime.fromisoformat(vencimiento_iso).date()
    if saldo <= 0:
        return "Pagada", 0
    dias_mora = max((hoy - venc).days, 0)
    if dias_mora > 0:
        return "Vencida", dias_mora
    return "Pendiente", 0

# ==========================
# UI
# ==========================
class CarteraTallerApp:
    def __init__(self, root):
        ensure_base_dir()
        self.root = root
        self.root.title("💼 Cartera del Taller (CxC)")
        self.root.geometry("1150x720")
        self.root.configure(bg="#0f172a")

        self.registros = cargar_cartera()
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
        title = ttk.Label(self.root, text="Módulo de Cartera (Cuentas por Cobrar)", style="Title.TLabel")
        title.pack(pady=10, anchor="w")

        main = tk.Frame(self.root, bg="#0f172a")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        left = tk.Frame(main, bg="#1e293b")
        left.pack(side="left", fill="y", padx=10, pady=10)

        right = tk.Frame(main, bg="#1e293b")
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Variables
        self.cliente = tk.StringVar()
        self.documento = tk.StringVar()
        self.referencia = tk.StringVar()  # Orden/Factura
        self.valor_factura = tk.StringVar(value="0")
        self.vencimiento = tk.StringVar(value=(datetime.now() + timedelta(days=15)).date().isoformat())
        self.observaciones = tk.StringVar()

        # Formulario
        rows = [
            ("Cliente", self.cliente, 28),
            ("Documento", self.documento, 20),
            ("Orden/Factura", self.referencia, 20),
            ("Valor factura (COP)", self.valor_factura, 14),
            ("Vencimiento (YYYY-MM-DD)", self.vencimiento, 14),
        ]
        for i, (label, var, width) in enumerate(rows):
            ttk.Label(left, text=label).grid(row=i, column=0, sticky="e", padx=8, pady=6)
            ttk.Entry(left, textvariable=var, width=width).grid(row=i, column=1, sticky="w", padx=8, pady=6)

        ttk.Label(left, text="Observaciones").grid(row=len(rows), column=0, sticky="ne", padx=8, pady=6)
        self.obs_txt = tk.Text(left, height=4, width=30)
        self.obs_txt.grid(row=len(rows), column=1, sticky="w", padx=8, pady=6)

        ttk.Button(left, text="Crear cuenta por cobrar", style="Menu.TButton", command=self._crear_cxc).grid(row=len(rows)+1, column=1, sticky="w", padx=8, pady=10)
        ttk.Button(left, text="Registrar abono", style="Menu.TButton", command=self._registrar_abono).grid(row=len(rows)+2, column=1, sticky="w", padx=8, pady=6)
        ttk.Button(left, text="Exportar a Excel", style="Menu.TButton", command=self._exportar).grid(row=len(rows)+3, column=1, sticky="w", padx=8, pady=6)
        ttk.Button(left, text="Limpiar formulario", style="Menu.TButton", command=self._limpiar_form).grid(row=len(rows)+4, column=1, sticky="w", padx=8, pady=6)

        # Treeview
        cols = ("Cliente","Documento","Ref","Estado","Valor","Abonos","Saldo","Vencimiento","Mora(días)")
        self.tree = ttk.Treeview(right, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=130)
        self.tree.pack(fill="both", expand=True)

        btn_frame = tk.Frame(right, bg="#1e293b")
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="📄 Ver detalle", style="Menu.TButton", command=self._ver_detalle).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="✏️ Editar", style="Menu.TButton", command=self._editar).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="🗑️ Eliminar", style="Menu.TButton", command=self._eliminar).pack(side="left", padx=6)

    # ==========================
    # ACCIONES
    # ==========================
    def _crear_cxc(self):
        try:
            valor = float(self.valor_factura.get())
            if valor <= 0:
                raise ValueError()
        except Exception:
            messagebox.showwarning("Validación", "Valor de factura debe ser numérico y mayor a 0.")
            return

        cxc = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "cliente": self.cliente.get().strip(),
            "documento": self.documento.get().strip(),
            "referencia": self.referencia.get().strip(),
            "valor_factura": round(valor, 2),
            "abonos": [],
            "saldo": round(valor, 2),
            "vencimiento": self.vencimiento.get().strip(),
            "observaciones": self.obs_txt.get("1.0", "end").strip(),
            "estado": "Pendiente",
            "dias_mora": 0
        }
        cxc["estado"], cxc["dias_mora"] = calcular_estado(cxc["saldo"], cxc["vencimiento"])

        self.registros.append(cxc)
        guardar_cartera(self.registros)
        self._refresh_tree()
        self._limpiar_form()
        messagebox.showinfo("Cartera", f"CxC creada para {cxc['cliente']}.\nSaldo: ${cxc['saldo']:,}")

    def _registrar_abono(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona una cuenta para registrar abono.")
            return
        idx = self.tree.index(sel[0])
        r = self.registros[idx]

        top = tk.Toplevel(self.root)
        top.title("Registrar abono")
        top.configure(bg="#0f172a")

        tk.Label(top, text=f"Cliente: {r['cliente']} | Ref: {r['referencia']}", bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=12, pady=6)
        tk.Label(top, text=f"Saldo actual: ${r['saldo']:,}", bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=12, pady=6)

        amt_var = tk.StringVar(value="0")
        ttk.Label(top, text="Monto abono").pack(anchor="w", padx=12, pady=4)
        ttk.Entry(top, textvariable=amt_var, width=18).pack(anchor="w", padx=12, pady=4)

        def do_abono():
            try:
                monto = float(amt_var.get())
                if monto <= 0:
                    raise ValueError()
            except Exception:
                messagebox.showwarning("Validación", "Monto debe ser numérico y mayor a 0.")
                return
            if monto > r["saldo"]:
                messagebox.showwarning("Validación", "El abono no puede superar el saldo.")
                return

            abono = {"fecha": datetime.now().isoformat(), "monto": round(monto, 2)}
            r["abonos"].append(abono)
            r["saldo"] = round(r["saldo"] - monto, 2)
            r["estado"], r["dias_mora"] = calcular_estado(r["saldo"], r["vencimiento"])
            guardar_cartera(self.registros)
            self._refresh_tree()
            messagebox.showinfo("Abono", f"Abono registrado: ${monto:,}. Nuevo saldo: ${r['saldo']:,}")
            top.destroy()

        ttk.Button(top, text="Registrar", style="Menu.TButton", command=do_abono).pack(pady=8)
        ttk.Button(top, text="Cancelar", style="Menu.TButton", command=top.destroy).pack(pady=4)

    def _refresh_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for r in self.registros:
            total_abonos = sum(a["monto"] for a in r["abonos"])
            self.tree.insert("", "end", values=(
                r["cliente"], r["documento"], r["referencia"], r["estado"],
                f"${r['valor_factura']:,}", f"${total_abonos:,}", f"${r['saldo']:,}",
                r["vencimiento"], r["dias_mora"]
            ))

    def _ver_detalle(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona una cuenta para ver detalle.")
            return
        idx = self.tree.index(sel[0])
        r = self.registros[idx]

        top = tk.Toplevel(self.root)
        top.title(f"Detalle cartera - {r['cliente']}")
        top.configure(bg="#0f172a")

        lines = [
            f"Fecha: {r['fecha']}",
            f"Cliente: {r['cliente']}  |  Documento: {r['documento']}",
            f"Referencia: {r['referencia']}",
            f"Estado: {r['estado']}  |  Vencimiento: {r['vencimiento']}  |  Mora: {r['dias_mora']} días",
            f"Valor factura: ${r['valor_factura']:,}  |  Saldo: ${r['saldo']:,}",
            f"Observaciones: {r['observaciones']}",
            "Abonos:"
        ]
        for ln in lines:
            tk.Label(top, text=ln, bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=12, pady=3)
        if not r["abonos"]:
            tk.Label(top, text="• Sin abonos registrados", bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=24, pady=2)
        else:
            for a in r["abonos"]:
                tk.Label(top, text=f'• {a["fecha"]}: ${a["monto"]:,}', bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=24, pady=2)

        ttk.Button(top, text="Cerrar", style="Menu.TButton", command=top.destroy).pack(pady=10)

    def _editar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona una cuenta para editar.")
            return
        idx = self.tree.index(sel[0])
        r = self.registros[idx]

        # Cargar en formulario
        self.cliente.set(r["cliente"])
        self.documento.set(r["documento"])
        self.referencia.set(r["referencia"])
        self.valor_factura.set(str(r["valor_factura"]))
        self.vencimiento.set(r["vencimiento"])
        self.obs_txt.delete("1.0", "end")
        self.obs_txt.insert("1.0", r["observaciones"])

        # Eliminar para reemplazar al crear
        self.registros.pop(idx)
        self._refresh_tree()

    def _eliminar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona una cuenta para eliminar.")
            return
        idx = self.tree.index(sel[0])
        if messagebox.askyesno("Confirmar", "¿Eliminar la cuenta seleccionada?"):
            self.registros.pop(idx)
            guardar_cartera(self.registros)
            self._refresh_tree()
            messagebox.showinfo("Eliminado", "Cuenta eliminada.")

    def _exportar(self):
        if not self.registros:
            messagebox.showwarning("Sin datos", "No hay registros para exportar.")
            return
        try:
            exportar_excel(self.registros)
            messagebox.showinfo("Exportado", f"Archivo Excel generado en:\n{OUTPUT_FILE}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

    def _limpiar_form(self):
        self.cliente.set("")
        self.documento.set("")
        self.referencia.set("")
        self.valor_factura.set("0")
        self.vencimiento.set((datetime.now() + timedelta(days=15)).date().isoformat())
        self.obs_txt.delete("1.0", "end")

# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    ensure_base_dir()
    root = tk.Tk()
    app = CarteraTallerApp(root)
    root.mainloop()
