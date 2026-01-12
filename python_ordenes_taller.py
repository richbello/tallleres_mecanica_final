import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
import openpyxl

# ==========================
# CONFIGURACIÓN
# ==========================
DATA_FILE = r"C:\RICHARD\RB\2025\Taller_mecánica\ordenes_taller.json"
OUTPUT_FILE = r"C:\RICHARD\RB\2025\Taller_mecánica\ordenes_taller.xlsx"

SERVICIOS = [
    "Cambio de aceite",
    "Alineación y balanceo",
    "Frenos (pastillas/discos)",
    "Diagnóstico eléctrico",
    "Cambio de batería",
    "Suspensión",
    "Afinación general",
]

# Precios por servicio (ajustar según corresponda)
PRECIOS_SERVICIOS = {
    "Cambio de aceite": 60000,
    "Alineación y balanceo": 80000,
    "Frenos (pastillas/discos)": 120000,
    "Diagnóstico eléctrico": 50000,
    "Cambio de batería": 40000,
    "Suspensión": 100000,
    "Afinación general": 70000,
}

REPUESTOS = [
    {"nombre": "Aceite 10W-40", "precio": 45000},
    {"nombre": "Filtro de aceite", "precio": 25000},
    {"nombre": "Pastillas de freno", "precio": 90000},
    {"nombre": "Batería 12V", "precio": 320000},
    {"nombre": "Amortiguador", "precio": 180000},
    {"nombre": "Filtro de aire", "precio": 30000},
    {"nombre": "Líquido de frenos", "precio": 28000},
]

ESTADOS = ["Pendiente", "En proceso", "Terminado"]

# ==========================
# UTILIDADES
# ==========================
def format_currency(v):
    try:
        return f"${int(v):,}"
    except Exception:
        return f"${v}"

# ==========================
# PERSISTENCIA
# ==========================
def cargar_ordenes():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_ordenes(ordenes):
    carpeta = os.path.dirname(DATA_FILE)
    if carpeta and not os.path.exists(carpeta):
        os.makedirs(carpeta)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(ordenes, f, ensure_ascii=False, indent=2)

def calcular_totales(repuestos, servicio):
    subtotal_repuestos = sum(r["precio"] for r in repuestos)
    precio_servicio = PRECIOS_SERVICIOS.get(servicio, 0)
    subtotal = subtotal_repuestos + precio_servicio
    iva = round(subtotal * 0.19)
    total = subtotal + iva
    return subtotal, iva, total, precio_servicio

def exportar_excel(ordenes):
    carpeta = os.path.dirname(OUTPUT_FILE)
    if carpeta and not os.path.exists(carpeta):
        os.makedirs(carpeta)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Órdenes de Trabajo"

    encabezados = [
        "Fecha", "Placa", "Marca", "Modelo", "Año",
        "Cliente", "Teléfono", "Servicio", "Precio Servicio", "Estado",
        "Diagnóstico", "Repuestos", "Subtotal", "IVA", "Total"
    ]
    ws.append(encabezados)

    for o in ordenes:
        ws.append([
            o["fecha"],
            o["placa"],
            o["marca"],
            o["modelo"],
            o["anio"],
            o["cliente"],
            o["telefono"],
            o["servicio"],
            o.get("precio_servicio", 0),
            o["estado"],
            o["diagnostico"],
            ", ".join(r["nombre"] for r in o["repuestos"]),
            o["subtotal"],
            o["iva"],
            o["total"]
        ])

    wb.save(OUTPUT_FILE)

# ==========================
# APLICACIÓN
# ==========================
class OrdenesTallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Órdenes de Trabajo - Taller Mecánico")
        self.root.geometry("1150x700")
        self.root.configure(bg="#0f172a")

        self.ordenes = cargar_ordenes()
        self.repuestos_seleccionados = []
        self.edit_index = None  # Índice de orden que se está editando (None si es nueva)

        self._estilos()
        self._layout()
        self.update_totales()  # mostrar valores iniciales

    def _estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#1e293b", foreground="#e2e8f0")
        style.configure(
            "Title.TLabel",
            background="#0f172a",
            foreground="#e2e8f0",
            font=("Segoe UI", 16, "bold")
        )
        style.configure("Ok.TButton", background="#f59e0b", foreground="#0b1220")
        style.configure("Treeview", background="#0b1220", foreground="#e2e8f0", rowheight=26)
        style.map("Ok.TButton",
                  background=[('active', '#f59e0b')],
                  foreground=[('active', '#ffffff')])

    def _layout(self):
        ttk.Label(
            self.root,
            text="Módulo de Órdenes de Trabajo",
            style="Title.TLabel"
        ).pack(pady=10)

        main = tk.Frame(self.root, bg="#0f172a")
        main.pack(fill="both", expand=True)

        left = tk.Frame(main, bg="#1e293b")
        left.pack(side="left", fill="y", padx=10)

        right = tk.Frame(main, bg="#1e293b")
        right.pack(side="right", fill="both", expand=True, padx=10)

        self.placa = tk.StringVar()
        self.marca = tk.StringVar()
        self.modelo = tk.StringVar()
        self.anio = tk.StringVar()
        self.cliente = tk.StringVar()
        self.telefono = tk.StringVar()
        self.servicio = tk.StringVar(value=SERVICIOS[0])
        self.estado = tk.StringVar(value=ESTADOS[0])

        # Variables para mostrar montos en formulario
        self.precio_servicio_var = tk.StringVar(value=format_currency(PRECIOS_SERVICIOS.get(SERVICIOS[0], 0)))
        self.subtotal_var = tk.StringVar(value=format_currency(0))
        self.iva_var = tk.StringVar(value=format_currency(0))
        self.total_var = tk.StringVar(value=format_currency(0))

        campos = [
            ("Placa", self.placa),
            ("Marca", self.marca),
            ("Modelo", self.modelo),
            ("Año", self.anio),
            ("Cliente", self.cliente),
            ("Teléfono", self.telefono),
        ]

        for i, (txt, var) in enumerate(campos):
            ttk.Label(left, text=txt).grid(row=i, column=0, sticky="w", padx=5, pady=3)
            ttk.Entry(left, textvariable=var).grid(row=i, column=1, padx=5, pady=3)

        ttk.Label(left, text="Diagnóstico").grid(row=6, column=0, sticky="w")
        self.diagnostico = tk.Text(left, height=4, width=30)
        self.diagnostico.grid(row=6, column=1, padx=5, pady=3)

        ttk.Label(left, text="Servicio").grid(row=7, column=0, sticky="w", padx=5)
        self.servicio_cb = ttk.Combobox(left, values=SERVICIOS, textvariable=self.servicio, state="readonly")
        self.servicio_cb.grid(row=7, column=1, padx=5, pady=3)
        self.servicio_cb.bind("<<ComboboxSelected>>", lambda e: self.on_servicio_changed())

        ttk.Label(left, text="Precio servicio").grid(row=8, column=0, sticky="w", padx=5)
        ttk.Label(left, textvariable=self.precio_servicio_var, background="#1e293b", foreground="#e2e8f0").grid(row=8, column=1, sticky="w")

        ttk.Label(left, text="Estado").grid(row=9, column=0, sticky="w", padx=5)
        ttk.Combobox(left, values=ESTADOS, textvariable=self.estado, state="readonly").grid(row=9, column=1, padx=5, pady=3)

        ttk.Label(left, text="Repuesto").grid(row=10, column=0, sticky="w", padx=5)
        self.rep_cb = ttk.Combobox(left, values=[r["nombre"] for r in REPUESTOS], state="readonly")
        if REPUESTOS:
            self.rep_cb.current(0)
        self.rep_cb.grid(row=10, column=1, padx=5, pady=3)

        ttk.Button(left, text="Agregar repuesto", command=self.agregar_repuesto).grid(row=11, column=1, pady=5)

        # --- Visualización compacta de repuestos (sin cuadro grande) ---
        self.rep_display_var = tk.StringVar(value="")
        self.rep_display_label = tk.Label(left, textvariable=self.rep_display_var,
                                          bg="#1e293b", fg="#e2e8f0", justify="left", anchor="w",
                                          wraplength=220)
        self.rep_display_label.grid(row=12, column=0, columnspan=2, padx=5, pady=(3,10), sticky="w")
        # ---------------------------------------------------------------

        # Montos visibles
        ttk.Label(left, text="Subtotal").grid(row=13, column=0, sticky="w", padx=5)
        ttk.Label(left, textvariable=self.subtotal_var, background="#1e293b", foreground="#e2e8f0").grid(row=13, column=1, sticky="w")

        ttk.Label(left, text="IVA (19%)").grid(row=14, column=0, sticky="w", padx=5)
        ttk.Label(left, textvariable=self.iva_var, background="#1e293b", foreground="#e2e8f0").grid(row=14, column=1, sticky="w")

        ttk.Label(left, text="Total").grid(row=15, column=0, sticky="w", padx=5)
        ttk.Label(left, textvariable=self.total_var, background="#1e293b", foreground="#e2e8f0", font=("Segoe UI", 10, "bold")).grid(row=15, column=1, sticky="w")

        ttk.Button(left, text="Guardar orden", style="Ok.TButton", command=self.guardar).grid(row=16, column=0, columnspan=2, pady=10)

        ttk.Button(left, text="Limpiar formulario", command=self.limpiar_formulario).grid(row=17, column=0, columnspan=2, pady=3)

        # ---------------------------
        # Treeview y botones CRUD
        # ---------------------------
        cols = ("Placa", "Cliente", "Servicio", "Estado", "Total")
        self.tree = ttk.Treeview(right, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.pack(fill="both", expand=True)

        btn_frame = tk.Frame(right, bg="#1e293b")
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="📝 Nuevo", style="Ok.TButton", command=self.nueva_orden).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Modificar", style="Ok.TButton", command=self.modificar_orden).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Eliminar", style="Ok.TButton", command=self.eliminar_orden).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📊 Exportar a Excel", style="Ok.TButton", command=self.exportar).pack(side="left", padx=5)

        self.refrescar()

    # ==========================
    # FUNCIONES
    # ==========================
    def on_servicio_changed(self):
        precio = PRECIOS_SERVICIOS.get(self.servicio.get(), 0)
        self.precio_servicio_var.set(format_currency(precio))
        self.update_totales()

    def agregar_repuesto(self):
        nombre = self.rep_cb.get()
        rep = next((r for r in REPUESTOS if r["nombre"] == nombre), None)
        if rep:
            self.repuestos_seleccionados.append(rep)
            self._actualizar_rep_display()
            self.update_totales()

    def _actualizar_rep_display(self):
        if not self.repuestos_seleccionados:
            self.rep_display_var.set("")  # sin cuadro blanco grande
        else:
            lines = [f'{r["nombre"]} - {format_currency(r["precio"])}' for r in self.repuestos_seleccionados]
            self.rep_display_var.set("\n".join(lines))

    def update_totales(self):
        subtotal, iva, total, precio_servicio = calcular_totales(self.repuestos_seleccionados, self.servicio.get())
        self.subtotal_var.set(format_currency(subtotal))
        self.iva_var.set(format_currency(iva))
        self.total_var.set(format_currency(total))
        self.precio_servicio_var.set(format_currency(precio_servicio))

    def guardar(self):
        subtotal, iva, total, precio_servicio = calcular_totales(self.repuestos_seleccionados, self.servicio.get())

        orden = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "placa": self.placa.get(),
            "marca": self.marca.get(),
            "modelo": self.modelo.get(),
            "anio": self.anio.get(),
            "cliente": self.cliente.get(),
            "telefono": self.telefono.get(),
            "diagnostico": self.diagnostico.get("1.0", "end").strip(),
            "servicio": self.servicio.get(),
            "precio_servicio": precio_servicio,
            "estado": self.estado.get(),
            "repuestos": self.repuestos_seleccionados.copy(),
            "subtotal": subtotal,
            "iva": iva,
            "total": total
        }

        if self.edit_index is None:
            # Nueva orden
            self.ordenes.append(orden)
            messagebox.showinfo("Guardado", "Orden guardada correctamente.")
        else:
            # Actualizar orden existente
            self.ordenes[self.edit_index] = orden
            messagebox.showinfo("Actualizado", "Orden actualizada correctamente.")
            self.edit_index = None

        guardar_ordenes(self.ordenes)
        self.refrescar()
        self.limpiar_formulario()

    def refrescar(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for o in self.ordenes:
            total_str = format_currency(o.get("total", 0))
            self.tree.insert("", "end",
                values=(o["placa"], o["cliente"], o["servicio"], o["estado"], total_str)
            )

    def limpiar(self):
        # Mantiene esta función si la usas en otro contexto (borra repuestos y diagnóstico)
        self.repuestos_seleccionados = []
        self._actualizar_rep_display()
        self.diagnostico.delete("1.0", "end")
        self.update_totales()

    def exportar(self):
        if not self.ordenes:
            messagebox.showwarning(
                "Atención",
                "No hay órdenes para exportar"
            )
            return

        try:
            exportar_excel(self.ordenes)
            messagebox.showinfo(
                "Exportación exitosa",
                f"El archivo Excel fue generado correctamente en:\n\n{OUTPUT_FILE}"
            )
        except Exception as e:
            messagebox.showerror(
                "Error al exportar",
                f"No se pudo generar el Excel.\n\nDetalle técnico:\n{str(e)}"
            )

    # ---------------------------
    # FUNCIONES NUEVAS
    # ---------------------------
    def nueva_orden(self):
        self.edit_index = None
        self.limpiar_formulario()

    def modificar_orden(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione una orden para modificar")
            return

        index = self.tree.index(selected[0])
        orden = self.ordenes[index]

        # Cargar datos en el formulario
        self.placa.set(orden.get("placa", ""))
        self.marca.set(orden.get("marca", ""))
        self.modelo.set(orden.get("modelo", ""))
        self.anio.set(orden.get("anio", ""))
        self.cliente.set(orden.get("cliente", ""))
        self.telefono.set(orden.get("telefono", ""))
        self.servicio.set(orden.get("servicio", SERVICIOS[0]))
        self.estado.set(orden.get("estado", ESTADOS[0]))
        self.diagnostico.delete("1.0", "end")
        self.diagnostico.insert("1.0", orden.get("diagnostico", ""))
        self.repuestos_seleccionados = orden.get("repuestos", []).copy()

        self._actualizar_rep_display()

        # No eliminar la orden; marcamos el índice para que al guardar se reemplace
        self.edit_index = index
        self.update_totales()

    def eliminar_orden(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione una orden para eliminar")
            return

        index = self.tree.index(selected[0])
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar esta orden?"):
            self.ordenes.pop(index)
            guardar_ordenes(self.ordenes)
            self.refrescar()

    def limpiar_formulario(self):
        """Limpia todos los campos del formulario sin borrar las órdenes guardadas."""
        self.placa.set("")
        self.marca.set("")
        self.modelo.set("")
        self.anio.set("")
        self.cliente.set("")
        self.telefono.set("")
        self.servicio.set(SERVICIOS[0])
        self.estado.set(ESTADOS[0])
        self.diagnostico.delete("1.0", "end")
        self.repuestos_seleccionados = []
        self._actualizar_rep_display()
        self.edit_index = None
        self.update_totales()


# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    root = tk.Tk()
    app = OrdenesTallerApp(root)
    root.mainloop()