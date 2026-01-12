import tkinter as tk
from tkinter import ttk, messagebox
import os, json
from datetime import datetime
import openpyxl

# Ruta de persistencia y exportación
BASE_DIR = r"C:\RICHARD\RB\2025\Taller_mecánica"
DB_FILE = os.path.join(BASE_DIR, "inventario.json")
EXPORT_FILE = os.path.join(BASE_DIR, "inventario_taller.xlsx")

def format_currency(v):
    try:
        return f"${int(v):,}"
    except Exception:
        return f"${v}"

class InventarioTaller:
    def __init__(self, root):
        self.root = root
        self.root.title("📦 Inventario - Taller Mecánico")
        self.root.geometry("1000x600")
        self.root.minsize(820, 520)
        self.root.configure(bg="#0f172a")

        self.productos = []
        self.edit_id = None
        self.next_id = 1

        self._configurar_estilos()
        self._build_ui()
        self._cargar_datos()

    # -------------------------
    # Estilos coherentes
    # -------------------------
    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Title.TLabel",
                        background="#0f172a",
                        foreground="#e2e8f0",
                        font=("Segoe UI", 16, "bold"))

        style.configure("Menu.TButton",
                        background="#f59e0b",
                        foreground="#111827",
                        font=("Segoe UI Semibold", 11),
                        padding=6)
        style.map("Menu.TButton", background=[("active", "#fbbf24")])

        style.configure("Form.TEntry",
                        fieldbackground="#ffffff",
                        foreground="#111827")

        style.configure("Treeview",
                        background="#0b1220",
                        foreground="#e2e8f0",
                        rowheight=26,
                        fieldbackground="#0b1220")
        style.configure("Treeview.Heading",
                        background="#f59e0b",
                        foreground="#111827",
                        font=("Segoe UI Semibold", 11))

    # -------------------------
    # UI
    # -------------------------
    def _build_ui(self):
        title = ttk.Label(self.root, text="📦 Registro de Inventario", style="Title.TLabel")
        title.pack(pady=10, anchor="w")

        main = tk.Frame(self.root, bg="#0f172a")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        left = tk.Frame(main, bg="#1e293b")
        left.pack(side="left", fill="y", padx=10, pady=10)

        right = tk.Frame(main, bg="#1e293b")
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        etiquetas = ["Código", "Producto", "Cantidad", "Precio Unitario"]
        self.entries = {}
        for i, etiqueta in enumerate(etiquetas):
            ttk.Label(left, text=etiqueta).grid(row=i, column=0, sticky="e", padx=8, pady=6)
            entry = ttk.Entry(left, width=28, style="Form.TEntry")
            entry.grid(row=i, column=1, sticky="w", padx=8, pady=6)
            self.entries[etiqueta] = entry

        ttk.Label(left, text="Valor Total").grid(row=len(etiquetas), column=0, sticky="e", padx=8, pady=6)
        self.valor_var = tk.StringVar(value=format_currency(0))
        ttk.Label(left, textvariable=self.valor_var).grid(row=len(etiquetas), column=1, sticky="w")

        ttk.Button(left, text="💾 Guardar", style="Menu.TButton", command=self._guardar_producto).grid(row=len(etiquetas)+1, column=1, sticky="w", pady=6)
        ttk.Button(left, text="🧹 Limpiar", style="Menu.TButton", command=self._limpiar_formulario).grid(row=len(etiquetas)+2, column=1, sticky="w", pady=6)

        cols = ("Código","Producto","Cantidad","Precio Unitario","Valor Total")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", style="Treeview")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120 if c in ("Código","Producto") else 90, anchor="center")
        self.tree.pack(fill="both", expand=True)

        btn_frame = tk.Frame(right, bg="#1e293b")
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="🆕 Nuevo", style="Menu.TButton", command=self._nuevo).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="✏️ Modificar", style="Menu.TButton", command=self._cargar_seleccion_para_editar).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="🗑️ Eliminar", style="Menu.TButton", command=self._eliminar_producto).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="📤 Exportar Excel", style="Menu.TButton", command=self._exportar_excel).pack(side="left", padx=6)

    # -------------------------
    # Persistencia
    # -------------------------
    def _cargar_datos(self):
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            self.productos = []
            self.next_id = 1
            return
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                self.productos = json.load(f)
            ids = [p.get("id", 0) for p in self.productos]
            self.next_id = max(ids, default=0) + 1
            self._refrescar_treeview()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer la base de datos:\n{e}")
            self.productos = []

    def _guardar_a_archivo(self):
        try:
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(self.productos, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la base de datos:\n{e}")

    # -------------------------
    # Lógica
    # -------------------------
    def _validar_campos(self):
        codigo = self.entries["Código"].get().strip()
        producto = self.entries["Producto"].get().strip()
        cantidad = self.entries["Cantidad"].get().strip()
        precio = self.entries["Precio Unitario"].get().strip()

        if not codigo or not producto:
            messagebox.showwarning("Validación", "Código y Producto son obligatorios.")
            return False
        try:
            c = float(cantidad)
            if c < 0: raise ValueError()
        except Exception:
            messagebox.showwarning("Validación", "Cantidad debe ser un número válido.")
            return False
        try:
            p = float(precio)
            if p < 0: raise ValueError()
        except Exception:
            messagebox.showwarning("Validación", "Precio Unitario debe ser un número válido.")
            return False
        return True

    def _calcular_valor(self, cantidad, precio):
        try:
            return int(round(float(cantidad) * float(precio)))
        except Exception:
            return 0

    def _guardar_producto(self):
        if not self._validar_campos():
            return
        codigo = self.entries["Código"].get().strip()
        producto = self.entries["Producto"].get().strip()
        cantidad = float(self.entries["Cantidad"].get().strip())
        precio = float(self.entries["Precio Unitario"].get().strip())
        valor_total = int(round(cantidad * precio))

        datos = {"Código": codigo, "Producto": producto,
                 "Cantidad": cantidad, "Precio Unitario": precio,
                 "Valor Total": valor_total}

        if self.edit_id is None:
            nuevo = {"id": self.next_id, **datos, "created_at": datetime.now().isoformat()}
            self.productos.append(nuevo)
            self.next_id += 1
            messagebox.showinfo("Guardado", "Producto creado correctamente.")
        else:
            for p in self.productos:
                if p.get("id") == self.edit_id:
                    p.update(datos)
                    p["updated_at"] = datetime.now().isoformat()
                    break
            messagebox.showinfo("Actualizado", "Producto actualizado correctamente.")
            self.edit_id = None

        self._guardar_a_archivo()
        self._refrescar_treeview()
        self._limpiar_formulario()

    def _limpiar_formulario(self):
        for k in self.entries:
            self.entries[k].delete(0, tk.END)
        self.valor_var.set(format_currency(0))
        self.edit_id = None
                 
        for sel in self.tree.selection():
            self.tree.selection_remove(sel)

    def _nuevo(self):
        self._limpiar_formulario()
        self.entries["Código"].focus_set()

    def _refrescar_treeview(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for p in self.productos:
            iid = str(p.get("id"))
            cantidad = p.get("Cantidad", 0)
            precio = p.get("Precio Unitario", 0)
            valor = p.get("Valor Total", 0)
            self.tree.insert("", "end", iid=iid,
                             values=(p.get("Código", ""), p.get("Producto", ""),
                                     f"{cantidad}", format_currency(precio), format_currency(valor)))

    def _cargar_seleccion_para_editar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un producto en la lista para modificar.")
            return
        iid = sel[0]
        try:
            pid = int(iid)
        except Exception:
            messagebox.showerror("Error", "ID de producto inválido.")
            return

        producto = next((p for p in self.productos if p.get("id") == pid), None)
        if producto is None:
            messagebox.showerror("Error", "Producto no encontrado en la base de datos.")
            return

        # cargar en formulario
        self.entries["Código"].delete(0, tk.END); self.entries["Código"].insert(0, producto.get("Código", ""))
        self.entries["Producto"].delete(0, tk.END); self.entries["Producto"].insert(0, producto.get("Producto", ""))
        self.entries["Cantidad"].delete(0, tk.END); self.entries["Cantidad"].insert(0, str(producto.get("Cantidad", "")))
        self.entries["Precio Unitario"].delete(0, tk.END); self.entries["Precio Unitario"].insert(0, str(producto.get("Precio Unitario", "")))
        self.valor_var.set(format_currency(producto.get("Valor Total", 0)))
        self.edit_id = pid

    def _eliminar_producto(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un producto para eliminar.")
            return
        iid = sel[0]
        try:
            pid = int(iid)
        except Exception:
            messagebox.showerror("Error", "ID de producto inválido.")
            return

        if not messagebox.askyesno("Confirmar", "¿Desea eliminar el producto seleccionado? Esta acción no se puede deshacer."):
            return

        self.productos = [p for p in self.productos if p.get("id") != pid]
        self._guardar_a_archivo()
        self._refrescar_treeview()
        self._limpiar_formulario()
        messagebox.showinfo("Eliminado", "Producto eliminado correctamente.")

    def _exportar_excel(self):
        if not self.productos:
            messagebox.showwarning("Atención", "No hay productos para exportar.")
            return

        carpeta = os.path.dirname(EXPORT_FILE)
        if carpeta and not os.path.exists(carpeta):
            os.makedirs(carpeta)

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Inventario"

            encabezados = ["ID", "Código", "Producto", "Cantidad", "Precio Unitario", "Valor Total", "Creado", "Actualizado"]
            ws.append(encabezados)

            for p in self.productos:
                ws.append([
                    p.get("id"),
                    p.get("Código", ""),
                    p.get("Producto", ""),
                    p.get("Cantidad", 0),
                    p.get("Precio Unitario", 0),
                    p.get("Valor Total", 0),
                    p.get("created_at", ""),
                    p.get("updated_at", "")
                ])

            wb.save(EXPORT_FILE)
            messagebox.showinfo("Exportado", f"Inventario exportado correctamente a:\n{EXPORT_FILE}")
        except Exception as e:
            messagebox.showerror("Error al exportar", f"No se pudo crear el Excel.\nDetalle:\n{e}")

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioTaller(root)
    root.mainloop()
    