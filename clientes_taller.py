import tkinter as tk
from tkinter import ttk, messagebox
import os, json
from datetime import datetime
import openpyxl

# Ruta de persistencia y exportación
BASE_DIR = r"C:\RICHARD\RB\2025\Taller_mecánica"
DB_FILE = os.path.join(BASE_DIR, "clientes.json")
EXPORT_FILE = os.path.join(BASE_DIR, "clientes_taller.xlsx")

class ClientesTaller:
    def __init__(self, root):
        self.root = root
        self.root.title("👥 Registro de Clientes - Taller Mecánico")
        self.root.geometry("1000x600")
        self.root.minsize(820, 520)
        self.root.configure(bg="#0f172a")  # fondo oscuro

        self.clientes = []
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
        title = ttk.Label(self.root, text="👥 Registro de Clientes", style="Title.TLabel")
        title.pack(pady=10, anchor="w")

        main = tk.Frame(self.root, bg="#0f172a")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        left = tk.Frame(main, bg="#1e293b")
        left.pack(side="left", fill="y", padx=10, pady=10)

        right = tk.Frame(main, bg="#1e293b")
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        etiquetas = ["Nombre", "Teléfono", "Correo", "Vehículo"]
        self.entries = {}
        for i, etiqueta in enumerate(etiquetas):
            ttk.Label(left, text=etiqueta).grid(row=i, column=0, sticky="e", padx=8, pady=6)
            entry = ttk.Entry(left, width=28, style="Form.TEntry")
            entry.grid(row=i, column=1, sticky="w", padx=8, pady=6)
            self.entries[etiqueta] = entry

        ttk.Button(left, text="💾 Guardar", style="Menu.TButton", command=self._guardar_cliente).grid(row=len(etiquetas)+1, column=1, sticky="w", pady=6)
        ttk.Button(left, text="🧹 Limpiar", style="Menu.TButton", command=self._limpiar_formulario).grid(row=len(etiquetas)+2, column=1, sticky="w", pady=6)

        cols = ("Nombre","Teléfono","Correo","Vehículo")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", style="Treeview")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=140 if c in ("Nombre","Vehículo") else 120, anchor="center")
        self.tree.pack(fill="both", expand=True)

        btn_frame = tk.Frame(right, bg="#1e293b")
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="🆕 Nuevo", style="Menu.TButton", command=self._nuevo).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="✏️ Modificar", style="Menu.TButton", command=self._cargar_seleccion_para_editar).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="🗑️ Eliminar", style="Menu.TButton", command=self._eliminar_cliente).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="📤 Exportar Excel", style="Menu.TButton", command=self._exportar_excel).pack(side="left", padx=6)

    # -------------------------
    # Persistencia
    # -------------------------
    def _cargar_datos(self):
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            self.clientes = []
            self.next_id = 1
            return
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                self.clientes = json.load(f)
            ids = [c.get("id", 0) for c in self.clientes]
            self.next_id = max(ids, default=0) + 1
            self._refrescar_treeview()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer la base de datos:\n{e}")
            self.clientes = []

    def _guardar_a_archivo(self):
        try:
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(self.clientes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la base de datos:\n{e}")

    # -------------------------
    # Lógica CRUD
    # -------------------------
    def _validar_campos(self):
        nombre = self.entries["Nombre"].get().strip()
        telefono = self.entries["Teléfono"].get().strip()
        if not nombre:
            messagebox.showwarning("Validación", "El campo Nombre es obligatorio.")
            return False
        if not telefono:
            messagebox.showwarning("Validación", "El campo Teléfono es obligatorio.")
            return False
        return True

    def _guardar_cliente(self):
        if not self._validar_campos():
            return

        datos = {
            "Nombre": self.entries["Nombre"].get().strip(),
            "Teléfono": self.entries["Teléfono"].get().strip(),
            "Correo": self.entries["Correo"].get().strip(),
            "Vehículo": self.entries["Vehículo"].get().strip(),
        }

        if self.edit_id is None:
            nuevo = {"id": self.next_id, **datos, "created_at": datetime.now().isoformat()}
            self.clientes.append(nuevo)
            self.next_id += 1
            messagebox.showinfo("Cliente guardado", "Cliente creado correctamente.")
        else:
            for c in self.clientes:
                if c.get("id") == self.edit_id:
                    c.update(datos)
                    c["updated_at"] = datetime.now().isoformat()
                    break
            messagebox.showinfo("Cliente actualizado", "Los cambios se guardaron correctamente.")
            self.edit_id = None

        self._guardar_a_archivo()
        self._refrescar_treeview()
        self._limpiar_formulario()

    def _limpiar_formulario(self):
        for k in self.entries:
            self.entries[k].delete(0, tk.END)
        self.edit_id = None
        for sel in self.tree.selection():
            self.tree.selection_remove(sel)

    def _nuevo(self):
        self._limpiar_formulario()
        self.entries["Nombre"].focus_set()

    def _refrescar_treeview(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for c in self.clientes:
            iid = str(c.get("id"))
            self.tree.insert("", "end", iid=iid,
                             values=(c.get("Nombre", ""), c.get("Teléfono", ""), c.get("Correo", ""), c.get("Vehículo", "")))

    def _cargar_seleccion_para_editar(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un cliente en la lista para modificar.")
            return
        iid = sel[0]
        try:
            cid = int(iid)
        except Exception:
            messagebox.showerror("Error", "ID de cliente inválido.")
            return

        cliente = next((c for c in self.clientes if c.get("id") == cid), None)
        if cliente is None:
            messagebox.showerror("Error", "Cliente no encontrado en la base de datos.")
            return

                # cargar en formulario
        self.entries["Nombre"].delete(0, tk.END); self.entries["Nombre"].insert(0, cliente.get("Nombre", ""))
        self.entries["Teléfono"].delete(0, tk.END); self.entries["Teléfono"].insert(0, cliente.get("Teléfono", ""))
        self.entries["Correo"].delete(0, tk.END); self.entries["Correo"].insert(0, cliente.get("Correo", ""))
        self.entries["Vehículo"].delete(0, tk.END); self.entries["Vehículo"].insert(0, cliente.get("Vehículo", ""))

        self.edit_id = cid

    def _eliminar_cliente(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un cliente para eliminar.")
            return
        iid = sel[0]
        try:
            cid = int(iid)
        except Exception:
            messagebox.showerror("Error", "ID de cliente inválido.")
            return

        if not messagebox.askyesno("Confirmar", "¿Desea eliminar el cliente seleccionado? Esta acción no se puede deshacer."):
            return

        self.clientes = [c for c in self.clientes if c.get("id") != cid]
        self._guardar_a_archivo()
        self._refrescar_treeview()
        self._limpiar_formulario()
        messagebox.showinfo("Eliminado", "Cliente eliminado correctamente.")

    def _exportar_excel(self):
        if not self.clientes:
            messagebox.showwarning("Atención", "No hay clientes para exportar.")
            return

        # asegúrate de que la carpeta exista
        carpeta = os.path.dirname(EXPORT_FILE)
        if carpeta and not os.path.exists(carpeta):
            try:
                os.makedirs(carpeta)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear la carpeta de exportación:\n{e}")
                return

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Clientes"

            encabezados = ["ID", "Nombre", "Teléfono", "Correo", "Vehículo", "Creado", "Actualizado"]
            ws.append(encabezados)

            for c in self.clientes:
                ws.append([
                    c.get("id"),
                    c.get("Nombre", ""),
                    c.get("Teléfono", ""),
                    c.get("Correo", ""),
                    c.get("Vehículo", ""),
                    c.get("created_at", ""),
                    c.get("updated_at", ""),
                ])

            wb.save(EXPORT_FILE)
            messagebox.showinfo("Exportado", f"Clientes exportados correctamente a:\n{EXPORT_FILE}")
        except Exception as e:
            messagebox.showerror("Error al exportar", f"No se pudo crear el Excel.\nDetalle:\n{e}")

    # -------------------------
    # Redimensionamiento y ajuste de fondo
    # -------------------------
    def _on_canvas_configure(self, event):
        w, h = event.width, event.height
        # redimensionar imagen de fondo si existe
        if self.bg_orig is not None and self.bg_id is not None:
            try:
                resized = self.bg_orig.resize((max(1, w), max(1, h)), Image.Resampling.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(resized)
                self.canvas.itemconfig(self.bg_id, image=self.bg_image)
            except Exception:
                pass

        # ajustar tamaño del content_frame (ventana interna) para que siempre tenga márgenes
        new_w = min(1000, max(480, w - 60))   # límites razonables
        new_h = min(720, max(320, h - 80))
        # reposicionar en el centro del canvas y ajustar ancho/alto del window
        try:
            self.canvas.coords(self.window_id, w // 2, h // 2)
            self.canvas.itemconfig(self.window_id, width=new_w, height=new_h)
        except Exception:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = ClientesTaller(root)
    root.mainloop()
