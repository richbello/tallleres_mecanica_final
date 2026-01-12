# nomina_taller.py
# Nómina mensual del taller con prestaciones sociales (Colombia)
# Estilo consistente: fondo oscuro (#0f172a) y botones naranjas ("Menu.TButton")
# Exporta a Excel y guarda registros en JSON

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
DATA_FILE = os.path.join(BASE_DIR, "nomina_registros.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "nomina_registros.xlsx")

# Parámetros Colombia (ajustables por año)
SMMLV = 1300000        # Salario mínimo mensual legal vigente (ejemplo)
AUX_TRANSPORTE = 162000  # Auxilio de transporte mensual (ejemplo)

# Porcentajes estándar (empleado)
PORC_SALUD_EMPLEADO = 0.04
PORC_PENSION_EMPLEADO = 0.04

# Prestaciones sociales (base: salario devengado sin auxilio)
# Cesantías: 1 salario anual -> proporcional mensual: salario_base * (días/360)
# Intereses cesantías: 12% anual -> proporcional mensual: cesantías * (12% / 12)
# Prima de servicios: 1 salario anual -> proporcional mensual: salario_base * (días/360)
# Vacaciones: 15 días por año -> proporcional mensual: salario_base * (días/720)
DIAS_MES_REFERENCIA = 30

# Recargos (simplificados)
RECARGO_NOCTURNO = 0.35     # sobre hora ordinaria
RECARGO_FESTIVO_DIURNO = 0.75
RECARGO_FESTIVO_NOCTURNO = 1.10
RECARGO_EXTRA_DIURNA = 1.25
RECARGO_EXTRA_NOCTURNA = 1.75

# ==========================
# PERSISTENCIA
# ==========================
def ensure_base_dir():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR, exist_ok=True)

def cargar_registros():
    ensure_base_dir()
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def guardar_registros(arr):
    ensure_base_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(arr, f, ensure_ascii=False, indent=2)

def exportar_excel(registros):
    ensure_base_dir()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Nómina"

    headers = [
        "Fecha", "Empleado", "Documento", "Cargo",
        "Salario base", "Días trabajados", "Auxilio transporte",
        "Horas extra diurnas", "Horas extra nocturnas",
        "Horas festivo diurnas", "Horas festivo nocturnas",
        "Comisiones",
        "Devengado", "Salud (4%)", "Pensión (4%)",
        "Cesantías", "Intereses cesantías", "Prima", "Vacaciones",
        "Neto a pagar"
    ]
    ws.append(headers)

    for r in registros:
        ws.append([
            r["fecha"],
            r["empleado"],
            r["documento"],
            r["cargo"],
            r["salario_base"],
            r["dias_trabajados"],
            r["auxilio_transporte"],
            r["horas_extra_diurnas"],
            r["horas_extra_nocturnas"],
            r["horas_festivo_diurnas"],
            r["horas_festivo_nocturnas"],
            r["comisiones"],
            r["devengado"],
            r["salud_empleado"],
            r["pension_empleado"],
            r["cesantias"],
            r["intereses_cesantias"],
            r["prima_servicios"],
            r["vacaciones"],
            r["neto_pagar"]
        ])

    wb.save(OUTPUT_FILE)

# ==========================
# CÁLCULOS
# ==========================
def calcular_nomina(
    salario_base: float,
    dias_trabajados: int,
    horas_extra_diurnas: float,
    horas_extra_nocturnas: float,
    horas_festivo_diurnas: float,
    horas_festivo_nocturnas: float,
    comisiones: float,
    aplica_auxilio: bool
):
    # Valor hora ordinaria (simplificado): salario_base / 240 (30 días * 8 horas)
    valor_hora = salario_base / (DIAS_MES_REFERENCIA * 8)

    # Recargos y extras
    valor_extra_diurna = horas_extra_diurnas * valor_hora * RECARGO_EXTRA_DIURNA
    valor_extra_nocturna = horas_extra_nocturnas * valor_hora * RECARGO_EXTRA_NOCTURNA
    valor_festivo_diurno = horas_festivo_diurnas * valor_hora * RECARGO_FESTIVO_DIURNO
    valor_festivo_nocturno = horas_festivo_nocturnas * valor_hora * RECARGO_FESTIVO_NOCTURNO

    # Proporcionalidad por días trabajados
    proporcional_salario = salario_base * (dias_trabajados / DIAS_MES_REFERENCIA)

    # Auxilio de transporte (si salario <= 2 SMMLV y aplica)
    aux_transporte = AUX_TRANSPORTE * (dias_trabajados / DIAS_MES_REFERENCIA) if aplica_auxilio else 0.0

    # Devengado
    devengado = (
        proporcional_salario
        + aux_transporte
        + valor_extra_diurna
        + valor_extra_nocturna
        + valor_festivo_diurno
        + valor_festivo_nocturno
        + comisiones
    )

    # Base prestaciones (sin auxilio de transporte)
    base_prestaciones = proporcional_salario + valor_extra_diurna + valor_extra_nocturna + valor_festivo_diurno + valor_festivo_nocturno + comisiones

    # Salud y pensión (empleado)
    salud_empleado = base_prestaciones * PORC_SALUD_EMPLEADO
    pension_empleado = base_prestaciones * PORC_PENSION_EMPLEADO

    # Cesantías (proporcional mensual): salario_base * (días/360) -> usando base_prestaciones
    cesantias = base_prestaciones * (dias_trabajados / 360.0)

    # Intereses cesantías (12% anual -> mensual): cesantías * (0.12 / 12)
    intereses_cesantias = cesantias * (0.12 / 12.0)

    # Prima de servicios (proporcional mensual): base_prestaciones * (días/360)
    prima_servicios = base_prestaciones * (dias_trabajados / 360.0)

    # Vacaciones (15 días por año -> mensual): base_prestaciones * (días/720)
    vacaciones = base_prestaciones * (dias_trabajados / 720.0)

    # Neto a pagar (simplificado): devengado - descuentos empleado (salud + pensión)
    neto_pagar = devengado - (salud_empleado + pension_empleado)

    return {
        "valor_hora": round(valor_hora, 2),
        "proporcional_salario": round(proporcional_salario, 2),
        "auxilio_transporte": round(aux_transporte, 2),
        "extras": {
            "extra_diurna": round(valor_extra_diurna, 2),
            "extra_nocturna": round(valor_extra_nocturna, 2),
            "festivo_diurno": round(valor_festivo_diurno, 2),
            "festivo_nocturno": round(valor_festivo_nocturno, 2),
        },
        "devengado": round(devengado, 2),
        "salud_empleado": round(salud_empleado, 2),
        "pension_empleado": round(pension_empleado, 2),
        "cesantias": round(cesantias, 2),
        "intereses_cesantias": round(intereses_cesantias, 2),
        "prima_servicios": round(prima_servicios, 2),
        "vacaciones": round(vacaciones, 2),
        "neto_pagar": round(neto_pagar, 2),
    }

# ==========================
# UI
# ==========================
class NominaTallerApp:
    def __init__(self, root):
        ensure_base_dir()
        self.root = root
        self.root.title("🧾 Nómina del Taller - Prestaciones Sociales (Colombia)")
        self.root.geometry("1100x720")
        self.root.configure(bg="#0f172a")

        self.registros = cargar_registros()
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
        title = ttk.Label(self.root, text="Módulo de Nómina y Prestaciones Sociales", style="Title.TLabel")
        title.pack(pady=10, anchor="w")

        main = tk.Frame(self.root, bg="#0f172a")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        left = tk.Frame(main, bg="#1e293b")
        left.pack(side="left", fill="y", padx=10, pady=10)

        right = tk.Frame(main, bg="#1e293b")
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Variables
        self.empleado = tk.StringVar()
        self.documento = tk.StringVar()
        self.cargo = tk.StringVar()
        self.salario_base = tk.StringVar(value=str(SMMLV))
        self.dias_trabajados = tk.StringVar(value="30")
        self.horas_extra_diurnas = tk.StringVar(value="0")
        self.horas_extra_nocturnas = tk.StringVar(value="0")
        self.horas_festivo_diurnas = tk.StringVar(value="0")
        self.horas_festivo_nocturnas = tk.StringVar(value="0")
        self.comisiones = tk.StringVar(value="0")
        self.aplica_auxilio = tk.BooleanVar(value=True)

        # Formulario
        rows = [
            ("Empleado", self.empleado, 30),
            ("Documento", self.documento, 20),
            ("Cargo", self.cargo, 20),
            ("Salario base (COP)", self.salario_base, 14),
            ("Días trabajados", self.dias_trabajados, 10),
            ("Horas extra diurnas", self.horas_extra_diurnas, 10),
            ("Horas extra nocturnas", self.horas_extra_nocturnas, 10),
            ("Horas festivo diurnas", self.horas_festivo_diurnas, 10),
            ("Horas festivo nocturnas", self.horas_festivo_nocturnas, 10),
            ("Comisiones (COP)", self.comisiones, 14),
        ]
        for i, (label, var, width) in enumerate(rows):
            ttk.Label(left, text=label).grid(row=i, column=0, sticky="e", padx=8, pady=6)
            ttk.Entry(left, textvariable=var, width=width).grid(row=i, column=1, sticky="w", padx=8, pady=6)

        ttk.Checkbutton(left, text="Aplica auxilio de transporte (≤ 2 SMMLV)", variable=self.aplica_auxilio).grid(row=len(rows), column=1, sticky="w", padx=8, pady=6)

        ttk.Button(left, text="Calcular y agregar", style="Menu.TButton", command=self._calcular_agregar).grid(row=len(rows)+1, column=1, sticky="w", padx=8, pady=10)
        ttk.Button(left, text="Exportar a Excel", style="Menu.TButton", command=self._exportar).grid(row=len(rows)+2, column=1, sticky="w", padx=8, pady=6)
        ttk.Button(left, text="Limpiar formulario", style="Menu.TButton", command=self._limpiar_form).grid(row=len(rows)+3, column=1, sticky="w", padx=8, pady=6)

        # Treeview
        cols = ("Empleado","Documento","Cargo","Devengado","Salud","Pensión","Cesantías","Intereses","Prima","Vacaciones","Neto")
        self.tree = ttk.Treeview(right, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120)
        self.tree.pack(fill="both", expand=True)

        btn_frame = tk.Frame(right, bg="#1e293b")
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="🗑️ Eliminar registro", style="Menu.TButton", command=self._eliminar).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="📄 Ver detalle", style="Menu.TButton", command=self._ver_detalle).pack(side="left", padx=6)

    # ==========================
    # ACCIONES
    # ==========================
    def _calcular_agregar(self):
        try:
            salario = float(self.salario_base.get())
            dias = int(self.dias_trabajados.get())
            he_d = float(self.horas_extra_diurnas.get())
            he_n = float(self.horas_extra_nocturnas.get())
            hf_d = float(self.horas_festivo_diurnas.get())
            hf_n = float(self.horas_festivo_nocturnas.get())
            com = float(self.comisiones.get())
        except Exception:
            messagebox.showwarning("Validación", "Verifica que salario, días y horas sean numéricos.")
            return

        if dias < 0 or dias > 30:
            messagebox.showwarning("Validación", "Los días trabajados deben estar entre 0 y 30.")
            return

        # Auxilio aplica si el salario base <= 2 SMMLV y el checkbox está activo
        aplica_aux = self.aplica_auxilio.get() and (salario <= 2 * SMMLV)

        calc = calcular_nomina(
            salario_base=salario,
            dias_trabajados=dias,
            horas_extra_diurnas=he_d,
            horas_extra_nocturnas=he_n,
            horas_festivo_diurnas=hf_d,
            horas_festivo_nocturnas=hf_n,
            comisiones=com,
            aplica_auxilio=aplica_aux
        )

        registro = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "empleado": self.empleado.get().strip(),
            "documento": self.documento.get().strip(),
            "cargo": self.cargo.get().strip(),
            "salario_base": round(salario, 2),
            "dias_trabajados": dias,
            "horas_extra_diurnas": he_d,
            "horas_extra_nocturnas": he_n,
            "horas_festivo_diurnas": hf_d,
            "horas_festivo_nocturnas": hf_n,
            "comisiones": round(com, 2),
            "auxilio_transporte": calc["auxilio_transporte"],
            "devengado": calc["devengado"],
            "salud_empleado": calc["salud_empleado"],
            "pension_empleado": calc["pension_empleado"],
            "cesantias": calc["cesantias"],
            "intereses_cesantias": calc["intereses_cesantias"],
            "prima_servicios": calc["prima_servicios"],
            "vacaciones": calc["vacaciones"],
            "neto_pagar": calc["neto_pagar"],
            "detalle_extras": calc["extras"],
            "valor_hora": calc["valor_hora"],
            "proporcional_salario": calc["proporcional_salario"]
        }

        self.registros.append(registro)
        guardar_registros(self.registros)
        self._refresh_tree()
        messagebox.showinfo("Nómina", f"Registro agregado para {registro['empleado']}.\nNeto: ${registro['neto_pagar']:,}")

    def _refresh_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for r in self.registros:
            self.tree.insert("", "end", values=(
                r["empleado"],
                r["documento"],
                r["cargo"],
                f"${r['devengado']:,}",
                f"${r['salud_empleado']:,}",
                f"${r['pension_empleado']:,}",
                f"${r['cesantias']:,}",
                f"${r['intereses_cesantias']:,}",
                f"${r['prima_servicios']:,}",
                f"${r['vacaciones']:,}",
                f"${r['neto_pagar']:,}",
            ))

    def _eliminar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona un registro para eliminar.")
            return
        idx = self.tree.index(sel[0])
        if messagebox.askyesno("Confirmar", "¿Eliminar el registro seleccionado?"):
            self.registros.pop(idx)
            guardar_registros(self.registros)
            self._refresh_tree()
            messagebox.showinfo("Eliminado", "Registro eliminado.")

    def _ver_detalle(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona un registro para ver detalle.")
            return
        idx = self.tree.index(sel[0])
        r = self.registros[idx]
        top = tk.Toplevel(self.root)
        top.title(f"Detalle de nómina - {r['empleado']}")
        top.configure(bg="#0f172a")

        lines = [
            f"Fecha: {r['fecha']}",
            f"Empleado: {r['empleado']}  |  Documento: {r['documento']}",
            f"Cargo: {r['cargo']}",
            f"Salario base: ${r['salario_base']:,}  |  Valor hora: ${r['valor_hora']:,}",
            f"Días trabajados: {r['dias_trabajados']}  |  Proporcional salario: ${r['proporcional_salario']:,}",
            f"Auxilio transporte: ${r['auxilio_transporte']:,}",
            f"Extras: Diurna ${r['detalle_extras']['extra_diurna']:,} | Nocturna ${r['detalle_extras']['extra_nocturna']:,}",
            f"Festivos: Diurno ${r['detalle_extras']['festivo_diurno']:,} | Nocturno ${r['detalle_extras']['festivo_nocturno']:,}",
            f"Comisiones: ${r['comisiones']:,}",
            f"Devengado: ${r['devengado']:,}",
            f"Descuentos: Salud ${r['salud_empleado']:,} | Pensión ${r['pension_empleado']:,}",
            f"Cesantías: ${r['cesantias']:,} | Intereses cesantías: ${r['intereses_cesantias']:,}",
            f"Prima de servicios: ${r['prima_servicios']:,} | Vacaciones: ${r['vacaciones']:,}",
            f"Neto a pagar: ${r['neto_pagar']:,}",
        ]

        for ln in lines:
            tk.Label(top, text=ln, bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=12, pady=3)

        ttk.Button(top, text="Cerrar", style="Menu.TButton", command=top.destroy).pack(pady=10)

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
        self.empleado.set("")
        self.documento.set("")
        self.cargo.set("")
        self.salario_base.set(str(SMMLV))
        self.dias_trabajados.set("30")
        self.horas_extra_diurnas.set("0")
        self.horas_extra_nocturnas.set("0")
        self.horas_festivo_diurnas.set("0")
        self.horas_festivo_nocturnas.set("0")
        self.comisiones.set("0")
        self.aplica_auxilio.set(True)

# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    ensure_base_dir()
    root = tk.Tk()
    app = NominaTallerApp(root)
    root.mainloop()
