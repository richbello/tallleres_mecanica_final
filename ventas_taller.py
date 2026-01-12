import tkinter as tk
from tkinter import ttk, messagebox
import os, json
from datetime import datetime
import openpyxl

BASE_DIR = r"C:\RICHARD\RB\2025\Taller_mecánica"
DB_FILE = os.path.join(BASE_DIR, "ventas.json")
EXPORT_FILE = os.path.join(BASE_DIR, "ventas_taller.xlsx")

def format_currency(v):
    try:
        return f"${int(v):,}"
    except Exception:
        return f"${v}"

class VentasTaller:
    def __init__(self, root):
        self.root = root
        self.root.title("📊 Registrar Venta - Taller Mecánico")
        self.root.geometry("1000x600")
        self.root.minsize(820, 520)
        self.root.configure(bg="#0f172a")

        self.ventas = []
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
        # Título
        title = ttk.Label(self.root, text="📊 Registrar Venta", style="Title.TLabel")
        title.pack(pady=10, anchor="w")

        main = tk.Frame(self.root, bg="#0f172a")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        left = tk.Frame(main, bg="#1e293b")
        left.pack(side="left", fill="y", padx=10, pady=10)

        right = tk.Frame(main, bg="#1e293b")
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Formulario
        etiquetas = ["Cliente", "Producto", "Cantidad", "Precio"]
        self.entries = {}
        for i, etiqueta in enumerate(etiquetas):
            ttk.Label(left, text=etiqueta).grid(row=i, column=0, sticky="e", padx=8, pady=6)
            entry = ttk.Entry(left, width=28, style="Form.TEntry")
            entry.grid(row=i, column=1, sticky="w", padx=8, pady=6)
            self.entries[etiqueta] = entry

        ttk.Label(left, text="Total").grid(row=len(etiquetas), column=0, sticky="e", padx=8, pady=6)
        self.total_var = tk.StringVar(value=format_currency(0))
        ttk.Label(left, textvariable=self.total_var).grid(row=len(etiquetas), column=1, sticky="w")

        ttk.Button(left, text="💾 Guardar", style="Menu.TButton", command=self._guardar).grid(row=len(etiquetas)+1, column=1, sticky="w", pady=6)
        ttk.Button(left, text="🧹 Limpiar", style="Menu.TButton", command=self._limpiar).grid(row=len(etiquetas)+2, column=1, sticky="w", pady=6)

        # Treeview
        cols = ("Cliente","Producto","Cantidad","Precio","Total")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", style="Treeview")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120 if c in ("Cliente","Producto") else 90, anchor="center")
        self.tree.pack(fill="both", expand=True)

        btn_frame = tk.Frame(right, bg="#1e293b")
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="🆕 Nuevo", style="Menu.TButton", command=self._nuevo).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="✏️ Modificar", style="Menu.TButton", command=self._cargar_seleccion).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="🗑️ Eliminar", style="Menu.TButton", command=self._eliminar).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="📤 Exportar Excel", style="Menu.TButton", command=self._exportar).pack(side="left", padx=6)

    # -------------------------
    # Persistencia
    # -------------------------
    def _cargar_datos(self):
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            self.ventas = []
            self.next_id = 1
            return
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                self.ventas = json.load(f)
            ids = [v.get("id", 0) for v in self.ventas]
            self.next_id = max(ids, default=0) + 1
            self._refrescar()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer la base de datos:\n{e}")
            self.ventas = []

    def _guardar_archivo(self):
        try:
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(self.ventas, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la base de datos:\n{e}")

    # -------------------------
    # Lógica
    # -------------------------
    def _validar(self):
        cliente = self.entries["Cliente"].get().strip()
        producto = self.entries["Producto"].get().strip()
        cantidad = self.entries["Cantidad"].get().strip()
        precio = self.entries["Precio"].get().strip()
        if not cliente or not producto:
            messagebox.showwarning("Validación", "Cliente y Producto son obligatorios.")
            return False
        try:
            c = float(cantidad)
            if c <= 0: raise ValueError()
        except Exception:
            messagebox.showwarning("Validación", "Cantidad debe ser un número mayor que 0.")
            return False
        try:
            p = float(precio)
            if p < 0: raise ValueError()
        except Exception:
            messagebox.showwarning("Validación", "Precio debe ser un número válido (>= 0).")
            return False
        return True

    def _guardar(self):
        if not self._validar():
            return
        cliente = self.entries["Cliente"].get().strip()
        producto = self.entries["Producto"].get().strip()
        cantidad = float(self.entries["Cantidad"].get().strip())
        precio = float(self.entries["Precio"].get().strip())
        total = int(round(cantidad * precio))

        datos = {"Cliente": cliente, "Producto": producto,
                 "Cantidad": cantidad, "Precio": precio, "Total": total}

        if self.edit_id is None:
            nuevo = {"id": self.next_id, **datos, "created_at": datetime.now().isoformat()}
            self.ventas.append(nuevo)
            self.next_id += 1
            messagebox.showinfo("Venta guardada", "Venta creada correctamente.")
        else:
            for v in self.ventas:
                if v.get("id") == self.edit_id:
                    v.update(datos)
                    v["updated_at"] = datetime.now().isoformat()
                    break
            messagebox.showinfo("Venta actualizada", "Los cambios se guardaron correctamente.")
            self.edit_id = None

        self._guardar_archivo()
        self._refrescar()
        self._limpiar()

    def _limpiar(self):
        for k in self.entries:
            self.entries[k].delete(0, tk.END)
        self.total_var.set(format_currency(0))
        self.edit_id = None
        for sel in self.tree.selection():
            self.tree.selection_remove(sel)

    def _nuevo(self):
        self._limpiar()
        self.entries["Cliente"].focus_set()

    def _refrescar(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for v in self.ventas:
            iid = str(v.get("id"))

            self.tree.insert("", "end", iid=iid,
                             values=(v.get("Cliente", ""), v.get("Producto", ""),
                                     f"{v.get('Cantidad',0)}",
                                     format_currency(v.get("Precio",0)),
                                     format_currency(v.get("Total",0))))
    def _cargar_seleccion(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una venta en la lista para modificar.")
            return
        iid = sel[0]
        try:
            vid = int(iid)
        except Exception:
            messagebox.showerror("Error", "ID de venta inválido.")
            return
        venta = next((v for v in self.ventas if v.get("id") == vid), None)
        if venta is None:
            messagebox.showerror("Error", "Venta no encontrada en la base de datos.")
            return
        self.entries["Cliente"].delete(0, tk.END); self.entries["Cliente"].insert(0, venta.get("Cliente",""))
        self.entries["Producto"].delete(0, tk.END); self.entries["Producto"].insert(0, venta.get("Producto",""))
        self.entries["Cantidad"].delete(0, tk.END); self.entries["Cantidad"].insert(0, str(venta.get("Cantidad",0)))
        self.entries["Precio"].delete(0, tk.END); self.entries["Precio"].insert(0, str(venta.get("Precio",0)))
        self.total_var.set(format_currency(venta.get("Total",0)))
        self.edit_id = vid

    def _eliminar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una venta para eliminar.")
            return
        iid = sel[0]
        try:
            vid = int(iid)
        except Exception:
            messagebox.showerror("Error", "ID de venta inválido.")
            return
        if not messagebox.askyesno("Confirmar", "¿Desea eliminar la venta seleccionada?"):
            return
        self.ventas = [v for v in self.ventas if v.get("id") != vid]
        self._guardar_archivo()
        self._refrescar()
        self._limpiar()
        messagebox.showinfo("Eliminado", "Venta eliminada correctamente.")

    def _exportar(self):
        if not self.ventas:
            messagebox.showwarning("Atención", "No hay ventas para exportar.")
            return
        carpeta = os.path.dirname(EXPORT_FILE)
        if carpeta and not os.path.exists(carpeta):
            os.makedirs(carpeta)
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Ventas"
            encabezados = ["ID","Cliente","Producto","Cantidad","Precio","Total","Creado","Actualizado"]
            ws.append(encabezados)
            for v in self.ventas:
                ws.append([v.get("id"), v.get("Cliente",""), v.get("Producto",""),
                           v.get("Cantidad",0), v.get("Precio",0), v.get("Total",0),
                           v.get("created_at",""), v.get("updated_at","")])
            wb.save(EXPORT_FILE)
            messagebox.showinfo("Exportado", f"Ventas exportadas correctamente a:\n{EXPORT_FILE}")
        except Exception as e:
            messagebox.showerror("Error al exportar", f"No se pudo crear el Excel.\n{e}")
    # -------------------------
    # Redimensionamiento
    # -------------------------
    def _on_resize(self, event):
        w, h = event.width, event.height
        if self.bg_orig is not None and self.bg_id is not None:
            try:
                resized = self.bg_orig.resize((max(1,w), max(1,h)), Image.Resampling.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(resized)
                self.canvas.itemconfig(self.bg_id, image=self.bg_image)
            except Exception:
                pass
        try:
            self.canvas.coords(self.card_id, w//2, h//2)
            self.canvas.itemconfig(self.card_id,
                                   width=min(1000, max(700, w-80)),
                                   height=min(700, max(420, h-80)))
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = VentasTaller(root)
    root.mainloop()
