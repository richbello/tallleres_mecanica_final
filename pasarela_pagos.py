# pasarela_pagos.py
# Mantiene colores originales (fondo oscuro y botones naranjas) y agrega métodos:
# Tarjeta crédito, Tarjeta débito, PSE, Nequi, Daviplata, Transferencia Bancolombia, Efectivo.
# Conserva integración con security_core (audit, telemetry) y cifrado con contraseña maestra.

import os
import json
import uuid
import secrets
import time
import base64
import hashlib
from datetime import datetime, timedelta

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

import openpyxl

from security_core import audit, module_opened, module_closed, button_clicked, view_attempt, copy_to_clipboard_then_clear

# ---- Config ----
BASE_DIR = r"C:\RICHARD\RB\2025\Taller_mecánica"
PAYMENT_FILE = os.path.join(BASE_DIR, "payment_methods.json.enc")
TRANSACTIONS_FILE = os.path.join(BASE_DIR, "transactions.json")
MASTER_FILE = os.path.join(BASE_DIR, "master_auth.json")
LEGACY_KEY_FILE = os.path.join(BASE_DIR, "security.key")
AUDIT_LOG = os.path.join(BASE_DIR, "security_audit.log")

KDF_ITERATIONS = 300_000
MAX_MASTER_ATTEMPTS = 5
LOCKOUT_SECONDS = 300
SESSION_TIMEOUT_SECONDS = 600

# ---- Helpers ----
def ensure_base_dir():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR, exist_ok=True)

def _set_private_file_permissions(path):
    try:
        if os.name == "posix":
            os.chmod(path, 0o600)
    except Exception:
        pass

def _derive_fernet_key(password: str, enc_salt_b64: str, iterations: int):
    enc_salt = base64.b64decode(enc_salt_b64)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=enc_salt,
        iterations=iterations,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    return key

# Master session cache
_master_failed_count = 0
_lockout_until = None
_session_fernet = None
_session_expires = None

def master_exists():
    return os.path.exists(MASTER_FILE)

def create_master_interactive(parent):
    ensure_base_dir()
    p1 = simpledialog.askstring("Crear contraseña maestra", "Ingrese contraseña maestra:", show="*", parent=parent)
    if not p1:
        return False
    p2 = simpledialog.askstring("Confirmar contraseña maestra", "Reingrese la contraseña maestra:", show="*", parent=parent)
    if p1 != p2:
        messagebox.showerror("Error", "Las contraseñas no coinciden.")
        return False
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", p1.encode("utf-8"), salt, KDF_ITERATIONS)
    enc_salt = secrets.token_bytes(16)
    data = {
        "salt": base64.b64encode(salt).decode("ascii"),
        "hash": base64.b64encode(dk).decode("ascii"),
        "enc_salt": base64.b64encode(enc_salt).decode("ascii"),
        "iterations": KDF_ITERATIONS
    }
    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    _set_private_file_permissions(MASTER_FILE)
    audit("master_created", "")
    return True

def verify_master_and_get_fernet(parent, purpose="acción sensible", require_create=True):
    global _master_failed_count, _lockout_until, _session_fernet, _session_expires
    ensure_base_dir()
    now = datetime.now()
    if _session_fernet is not None and _session_expires and now < _session_expires:
        return _session_fernet
    if _lockout_until and now < _lockout_until:
        secs = int((_lockout_until - now).total_seconds())
        messagebox.showerror("Bloqueado", f"Demasiados intentos fallidos. Intenta nuevamente en {secs} segundos.")
        return None
    if not master_exists():
        if require_create and messagebox.askyesno("Contraseña maestra no encontrada", "No existe una contraseña maestra. ¿Desea crearla ahora?"):
            ok = create_master_interactive(parent)
            if not ok:
                return None
        else:
            return None
    try:
        with open(MASTER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        salt = base64.b64decode(data["salt"])
        stored_hash = base64.b64decode(data["hash"])
        enc_salt_b64 = data["enc_salt"]
        iterations = int(data.get("iterations", KDF_ITERATIONS))
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo leer configuración de la maestra: {e}")
        audit("master_read_failed", str(e))
        return None
    attempt = simpledialog.askstring("Contraseña maestra", f"Ingrese la contraseña maestra para {purpose}:", show="*", parent=parent)
    if attempt is None:
        return None
    dk = hashlib.pbkdf2_hmac("sha256", attempt.encode("utf-8"), salt, iterations)
    if not secrets.compare_digest(dk, stored_hash):
        _master_failed_count += 1
        audit("master_failed", purpose)
        if _master_failed_count >= MAX_MASTER_ATTEMPTS:
            _lockout_until = datetime.now() + timedelta(seconds=LOCKOUT_SECONDS)
            _master_failed_count = 0
            messagebox.showerror("Bloqueado", f"Demasiados intentos fallidos. Bloqueado por {LOCKOUT_SECONDS} segundos.")
        else:
            remaining = MAX_MASTER_ATTEMPTS - _master_failed_count
            messagebox.showerror("Error", f"Contraseña maestra incorrecta. Intentos restantes: {remaining}")
        return None
    try:
        key = _derive_fernet_key(attempt, enc_salt_b64, iterations)
        f = Fernet(key)
        _session_fernet = f
        _session_expires = datetime.now() + timedelta(seconds=SESSION_TIMEOUT_SECONDS)
        _master_failed_count = 0
        audit("master_verified", purpose)
        return f
    except Exception as e:
        audit("master_derive_failed", str(e))
        messagebox.showerror("Error", f"No se pudo derivar la clave: {e}")
        return None

# Legacy helper
def _legacy_key_exists():
    return os.path.exists(LEGACY_KEY_FILE)

def _load_legacy_fernet():
    try:
        with open(LEGACY_KEY_FILE, "rb") as f:
            key = f.read()
        return Fernet(key)
    except Exception:
        return None

def _migrate_payment_file_if_needed(fernet_new):
    if not os.path.exists(PAYMENT_FILE):
        return
    try:
        with open(PAYMENT_FILE, "rb") as f:
            enc = f.read()
        _ = fernet_new.decrypt(enc)
        return
    except Exception:
        pass
    if _legacy_key_exists():
        legacy_f = _load_legacy_fernet()
        if legacy_f:
            try:
                with open(PAYMENT_FILE, "rb") as f:
                    enc = f.read()
                data = legacy_f.decrypt(enc)
                bak = PAYMENT_FILE + ".bak-" + datetime.now().strftime("%Y%m%d%H%M%S")
                try:
                    os.replace(PAYMENT_FILE, bak)
                except Exception:
                    try:
                        import shutil
                        shutil.copy2(PAYMENT_FILE, bak)
                    except Exception:
                        pass
                new_enc = fernet_new.encrypt(data)
                with open(PAYMENT_FILE, "wb") as f:
                    f.write(new_enc)
                _set_private_file_permissions(PAYMENT_FILE)
                audit("migrated_payment_file", f"backup={os.path.basename(bak)}")
                try:
                    os.remove(LEGACY_KEY_FILE)
                    audit("legacy_key_removed", "")
                except Exception:
                    pass
            except Exception as e:
                audit("migration_failed", str(e))
                return

# Storage helpers using session fernet
def _fernet_for_storage(parent):
    f = verify_master_and_get_fernet(parent, "operaciones de la pasarela")
    return f

def load_payment_methods(parent):
    ensure_base_dir()
    if not os.path.exists(PAYMENT_FILE):
        return []
    f = _fernet_for_storage(parent)
    if f is None:
        messagebox.showwarning("Acceso denegado", "No se proporcionó la contraseña maestra. No se pueden cargar métodos tokenizados.")
        return []
    try:
        with open(PAYMENT_FILE, "rb") as fh:
            enc = fh.read()
        data = f.decrypt(enc)
        arr = json.loads(data.decode("utf-8"))
        return arr
    except InvalidToken:
        try:
            _migrate_payment_file_if_needed(f)
            with open(PAYMENT_FILE, "rb") as fh:
                enc = fh.read()
            data = f.decrypt(enc)
            arr = json.loads(data.decode("utf-8"))
            return arr
        except Exception as e:
            audit("load_payment_methods_failed", str(e))
            messagebox.showerror("Error", "No se pudo desencriptar métodos tokenizados. Verifica la contraseña maestra o la key legacy.")
            return []
    except Exception as e:
        audit("load_payment_methods_failed", str(e))
        return []

def save_payment_methods(parent, arr):
    ensure_base_dir()
    f = _fernet_for_storage(parent)
    if f is None:
        messagebox.showwarning("Acceso denegado", "No se proporcionó la contraseña maestra. No se pueden guardar métodos tokenizados.")
        return False
    try:
        data = json.dumps(arr, ensure_ascii=False, indent=2).encode("utf-8")
        enc = f.encrypt(data)
        with open(PAYMENT_FILE, "wb") as fh:
            fh.write(enc)
        _set_private_file_permissions(PAYMENT_FILE)
        return True
    except Exception as e:
        audit("save_payment_methods_failed", str(e))
        messagebox.showerror("Error", f"No se pudo guardar métodos tokenizados: {e}")
        return False

def load_transactions():
    ensure_base_dir()
    if not os.path.exists(TRANSACTIONS_FILE):
        return []
    try:
        with open(TRANSACTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_transaction(tx):
    ensure_base_dir()
    txs = load_transactions()
    txs.append(tx)
    with open(TRANSACTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(txs, f, ensure_ascii=False, indent=2)
    _set_private_file_permissions(TRANSACTIONS_FILE)

# ---- UI: Pasarela de Pagos (original colors preserved) ----
PAYMENT_METHODS = [
    "Tarjeta crédito",
    "Tarjeta débito",
    "PSE",
    "Nequi",
    "Daviplata",
    "Transferencia Bancolombia",
    "Efectivo"
]

class PasarelaPagos:
    def __init__(self, root):
        ensure_base_dir()
        self.root = root
        self.root.title("💳 Pasarela de Pagos - Taller Mecánico (Sandbox)")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        module_opened("PasarelaPagos", "window_created")
        self._setup_styles()
        self._build_ui()
        self._load_data()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Menu.TButton", background="#f59e0b", foreground="#111827", font=("Segoe UI Semibold", 11), padding=6)
        style.map("Menu.TButton", background=[("active", "#fbbf24")])
        style.configure("TLabel", background="#0f172a", foreground="#e2e8f0")
        style.configure("TEntry", fieldbackground="#ffffff")
        style.configure("TCombobox", fieldbackground="#ffffff")

    def _build_ui(self):
        frame = tk.Frame(self.root, bg="#0f172a")
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        title = tk.Label(frame, text="Pasarela de Pagos (Sandbox)", bg="#0f172a", fg="#e2e8f0", font=("Segoe UI Semibold", 16))
        title.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,10))

        # Cliente y monto
        tk.Label(frame, text="Cliente:", bg="#0f172a", fg="#e2e8f0").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.client_var = tk.StringVar(); ttk.Entry(frame, textvariable=self.client_var, width=30).grid(row=1, column=1, sticky="w")

        tk.Label(frame, text="Monto (COP):", bg="#0f172a", fg="#e2e8f0").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.amount_var = tk.StringVar(); ttk.Entry(frame, textvariable=self.amount_var, width=20).grid(row=2, column=1, sticky="w")

        # Método de pago
        tk.Label(frame, text="Método de pago:", bg="#0f172a", fg="#e2e8f0").grid(row=3, column=0, sticky="e", padx=6, pady=6)
        self.method_var = tk.StringVar(value=PAYMENT_METHODS[0])
        self.method_cb = ttk.Combobox(frame, values=PAYMENT_METHODS, textvariable=self.method_var, state="readonly", width=28)
        self.method_cb.grid(row=3, column=1, sticky="w")
        self.method_cb.bind("<<ComboboxSelected>>", self._on_method_change)

        # Paneles dinámicos por método
        self.method_panels = {}
        self._build_card_panel(frame)        # Tarjeta crédito/débito
        self._build_pse_panel(frame)         # PSE
        self._build_wallet_panel(frame)      # Nequi/Daviplata
        self._build_transfer_panel(frame)    # Transferencia Bancolombia
        self._build_cash_panel(frame)        # Efectivo

        # Botones acción
        ttk.Button(frame, text="Procesar pago", style="Menu.TButton", command=self._on_process_payment).grid(row=9, column=1, pady=10, sticky="w")
        ttk.Button(frame, text="Tokenizar tarjeta (guardar)", style="Menu.TButton", command=self._on_tokenize_card).grid(row=9, column=2, pady=10, sticky="w")

        # Right: métodos tokenizados y transacciones
        tk.Label(frame, text="Métodos tokenizados:", bg="#0f172a", fg="#e2e8f0").grid(row=1, column=3, sticky="w", padx=12)
        self.methods_tree = ttk.Treeview(frame, columns=("token","mask","brand"), show="headings", height=8)
        self.methods_tree.heading("token", text="Token"); self.methods_tree.heading("mask", text="Tarjeta"); self.methods_tree.heading("brand", text="Marca")
        self.methods_tree.grid(row=2, column=3, rowspan=4, padx=12, sticky="nsew")

        tk.Label(frame, text="Transacciones:", bg="#0f172a", fg="#e2e8f0").grid(row=6, column=3, sticky="w", padx=12, pady=(8,0))
        self.tx_tree = ttk.Treeview(frame, columns=("id","cliente","amount","method","status","time"), show="headings", height=10)
        for c, txt in [("id","ID"),("cliente","Cliente"),("amount","Monto"),("method","Método"),("status","Estado"),("time","Fecha")]:
            self.tx_tree.heading(c, text=txt); self.tx_tree.column(c, width=130)
        self.tx_tree.grid(row=7, column=3, rowspan=4, padx=12, sticky="nsew")

        ttk.Button(frame, text="Ver tarjeta (temporal)", style="Menu.TButton", command=self._on_view_card).grid(row=11, column=3, sticky="w", padx=12, pady=6)
        ttk.Button(frame, text="Eliminar método", style="Menu.TButton", command=self._on_delete_method).grid(row=11, column=3, sticky="e", padx=12, pady=6)

        ttk.Button(frame, text="Exportar transacciones (Excel)", style="Menu.TButton", command=self._on_export_transactions).grid(row=12, column=3, sticky="w", padx=12, pady=6)
        ttk.Button(frame, text="Ver audit log", style="Menu.TButton", command=lambda: self._open_audit()).grid(row=12, column=3, sticky="e", padx=12, pady=6)

        frame.grid_columnconfigure(3, weight=1)
        frame.grid_rowconfigure(7, weight=1)

        # Mostrar panel inicial
        self._show_panel_for_method(self.method_var.get())

    # ---- Panels ----
    def _build_card_panel(self, parent):
        panel = tk.Frame(parent, bg="#0f172a")
        self.method_panels["card"] = panel
        # Tarjeta guardada
        tk.Label(panel, text="Tarjeta guardada:", bg="#0f172a", fg="#e2e8f0").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.saved_cards_cb = ttk.Combobox(panel, values=[], state="readonly", width=36); self.saved_cards_cb.grid(row=0, column=1, sticky="w")
        ttk.Button(panel, text="Usar tarjeta seleccionada", style="Menu.TButton", command=self._use_selected_card).grid(row=0, column=2, padx=6)

        # Número, exp, cvv
        tk.Label(panel, text="Número de tarjeta:", bg="#0f172a", fg="#e2e8f0").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.card_number_var = tk.StringVar(); ttk.Entry(panel, textvariable=self.card_number_var, width=36).grid(row=1, column=1, sticky="w")

        tk.Label(panel, text="MM/AA:", bg="#0f172a", fg="#e2e8f0").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.expiry_var = tk.StringVar(); ttk.Entry(panel, textvariable=self.expiry_var, width=12).grid(row=2, column=1, sticky="w")

        tk.Label(panel, text="CVV:", bg="#0f172a", fg="#e2e8f0").grid(row=3, column=0, sticky="e", padx=6, pady=6)
        self.cvv_var = tk.StringVar(); ttk.Entry(panel, textvariable=self.cvv_var, width=8, show="*").grid(row=3, column=1, sticky="w")

        self.save_card_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(panel, text="Guardar tarjeta tokenizada para futuros pagos", variable=self.save_card_var).grid(row=4, column=1, sticky="w", pady=(4,8))

        panel.grid(row=4, column=0, columnspan=3, sticky="w", padx=0, pady=(8,4))

    def _build_pse_panel(self, parent):
        panel = tk.Frame(parent, bg="#0f172a")
        self.method_panels["pse"] = panel

        tk.Label(panel, text="Banco:", bg="#0f172a", fg="#e2e8f0").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.pse_bank_var = tk.StringVar()
        self.pse_bank_cb = ttk.Combobox(panel, values=["Bancolombia","Davivienda","BBVA","Banco de Bogotá","Occidente","Popular","AV Villas"], textvariable=self.pse_bank_var, state="readonly", width=28)
        self.pse_bank_cb.grid(row=0, column=1, sticky="w")

        tk.Label(panel, text="Tipo de cuenta:", bg="#0f172a", fg="#e2e8f0").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.pse_account_type_var = tk.StringVar()
        self.pse_account_type_cb = ttk.Combobox(panel, values=["Ahorros","Corriente"], textvariable=self.pse_account_type_var, state="readonly", width=20)
        self.pse_account_type_cb.grid(row=1, column=1, sticky="w")

        tk.Label(panel, text="Documento:", bg="#0f172a", fg="#e2e8f0").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.pse_doc_var = tk.StringVar(); ttk.Entry(panel, textvariable=self.pse_doc_var, width=24).grid(row=2, column=1, sticky="w")

        panel.grid(row=5, column=0, columnspan=3, sticky="w", padx=0, pady=(8,4))

    def _build_wallet_panel(self, parent):
        panel = tk.Frame(parent, bg="#0f172a")
        self.method_panels["wallet"] = panel

        tk.Label(panel, text="Proveedor:", bg="#0f172a", fg="#e2e8f0").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.wallet_provider_var = tk.StringVar(value="Nequi")
        self.wallet_provider_cb = ttk.Combobox(panel, values=["Nequi","Daviplata"], textvariable=self.wallet_provider_var, state="readonly", width=20)
        self.wallet_provider_cb.grid(row=0, column=1, sticky="w")

        tk.Label(panel, text="Celular:", bg="#0f172a", fg="#e2e8f0").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.wallet_phone_var = tk.StringVar(); ttk.Entry(panel, textvariable=self.wallet_phone_var, width=24).grid(row=1, column=1, sticky="w")

        tk.Label(panel, text="Referencia:", bg="#0f172a", fg="#e2e8f0").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.wallet_ref_var = tk.StringVar(); ttk.Entry(panel, textvariable=self.wallet_ref_var, width=24).grid(row=2, column=1, sticky="w")

        panel.grid(row=6, column=0, columnspan=3, sticky="w", padx=0, pady=(8,4))

    def _build_transfer_panel(self, parent):
        panel = tk.Frame(parent, bg="#0f172a")
        self.method_panels["transfer"] = panel

        tk.Label(panel, text="Banco:", bg="#0f172a", fg="#e2e8f0").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.transfer_bank_var = tk.StringVar(value="Bancolombia")
        self.transfer_bank_cb = ttk.Combobox(panel, values=["Bancolombia","Davivienda","BBVA","Banco de Bogotá"], textvariable=self.transfer_bank_var, state="readonly", width=24)
        self.transfer_bank_cb.grid(row=0, column=1, sticky="w")

        tk.Label(panel, text="Referencia/Comprobante:", bg="#0f172a", fg="#e2e8f0").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.transfer_ref_var = tk.StringVar(); ttk.Entry(panel, textvariable=self.transfer_ref_var, width=28).grid(row=1, column=1, sticky="w")

        panel.grid(row=7, column=0, columnspan=3, sticky="w", padx=0, pady=(8,4))

    def _build_cash_panel(self, parent):
        panel = tk.Frame(parent, bg="#0f172a")
        self.method_panels["cash"] = panel

        tk.Label(panel, text="Observación:", bg="#0f172a", fg="#e2e8f0").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.cash_note_var = tk.StringVar(); ttk.Entry(panel, textvariable=self.cash_note_var, width=36).grid(row=0, column=1, sticky="w")

        panel.grid(row=8, column=0, columnspan=3, sticky="w", padx=0, pady=(8,4))

    # ---- Data load/refresh ----
    def _load_data(self):
        try:
            self.methods = load_payment_methods(self.root)
        except Exception as e:
            audit("load_methods_exception", str(e))
            self.methods = []
        self._refresh_methods_ui()
        self._refresh_transactions_ui()

    def _refresh_methods_ui(self):
        self.methods_tree.delete(*self.methods_tree.get_children())
        for m in self.methods:
            self.methods_tree.insert("", "end", iid=m.get("token"), values=(m.get("token"), m.get("mask"), m.get("brand","")))
        cb_vals = [f"{m.get('mask')}  ({m.get('token')[:8]})" for m in self.methods]
        # Card panel combobox
        if hasattr(self, "saved_cards_cb"):
            self.saved_cards_cb['values'] = cb_vals

    def _refresh_transactions_ui(self):
        self.tx_tree.delete(*self.tx_tree.get_children())
        txs = load_transactions()
        for t in txs[-300:]:
            self.tx_tree.insert("", "end", values=(t.get("id"), t.get("cliente"), f"{t.get('amount'):.2f}", t.get("method"), t.get("status"), t.get("time")))

    # ---- Method switching ----
    def _on_method_change(self, event=None):
        self._show_panel_for_method(self.method_var.get())

    def _show_panel_for_method(self, method_name):
        # Ocultar todos
        for p in self.method_panels.values():
            p.grid_remove()
        # Mostrar según método
        if method_name in ("Tarjeta crédito","Tarjeta débito"):
            self.method_panels["card"].grid()
        elif method_name == "PSE":
            self.method_panels["pse"].grid()
        elif method_name in ("Nequi","Daviplata"):
            self.method_panels["wallet"].grid()
            self.wallet_provider_var.set(method_name)
        elif method_name == "Transferencia Bancolombia":
            self.method_panels["transfer"].grid()
        elif method_name == "Efectivo":
            self.method_panels["cash"].grid()

    # ---- Tokenization & view/delete ----
    def _on_tokenize_card(self):
        # Solo aplica a tarjetas
        if self.method_var.get() not in ("Tarjeta crédito","Tarjeta débito"):
            messagebox.showinfo("Tokenización", "La tokenización aplica únicamente a tarjetas.")
            return
        card = self.card_number_var.get().strip()
        exp = self.expiry_var.get().strip()
        if not card or not exp:
            messagebox.showwarning("Validación", "Completa número y expiración para tokenizar.")
            return
        if not luhn_checksum(card):
            messagebox.showwarning("Validación", "Número de tarjeta inválido (Luhn).")
            return
        f = verify_master_and_get_fernet(self.root, "tokenizar tarjeta")
        if f is None:
            return
        token = str(uuid.uuid4())
        masked = mask_card(card)
        brand = "CARD"
        payload = {"card": card, "exp": exp}
        try:
            enc = f.encrypt(json.dumps(payload).encode("utf-8"))
            methods = load_payment_methods(self.root) or []
            methods.append({
                "token": token,
                "mask": masked,
                "brand": brand,
                "enc": enc.decode("utf-8"),
                "created_at": datetime.now().isoformat()
            })
            ok = save_payment_methods(self.root, methods)
            if ok:
                audit("tokenize_card", f"token={token} mask={masked}")
                button_clicked("PasarelaPagos", "Tokenizar tarjeta", f"mask={masked}")
                messagebox.showinfo("Tokenizado", f"Tarjeta tokenizada: {masked}")
                self.card_number_var.set("")
                self.cvv_var.set("")
                self.expiry_var.set("")
                self.methods = methods
                self._refresh_methods_ui()
            else:
                messagebox.showerror("Error", "No se pudo guardar la tarjeta tokenizada.")
        except Exception as e:
            audit("tokenize_failed", str(e))
            messagebox.showerror("Error", f"No se pudo tokenizar la tarjeta: {e}")

    def _get_selected_method_token(self):
        sel = self.methods_tree.selection()
        if not sel:
            return None
        return sel[0]

    def _on_view_card(self):
        f = verify_master_and_get_fernet(self.root, "ver tarjeta tokenizada")
        if f is None:
            return
        token = self._get_selected_method_token()
        if token is None:
            messagebox.showwarning("Selecciona", "Selecciona un método tokenizado.")
            return
        m = next((x for x in (self.methods or []) if x.get("token") == token), None)
        if not m:
            messagebox.showerror("Error", "Método no encontrado.")
            return
        try:
            dec = f.decrypt(m.get("enc").encode("utf-8"))
            payload = json.loads(dec.decode("utf-8"))
            audit("view_card", f"token={token}")
            view_attempt("PasarelaPagos", f"token={token}", success=True)
            top = tk.Toplevel(self.root)
            top.title("Tarjeta (temporal)")
            top.configure(bg="#0f172a")
            tk.Label(top, text=f"Token: {token}", bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=10, pady=4)
            tk.Label(top, text=f"Tarjeta: {payload.get('card')}", bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=10, pady=2)
            tk.Label(top, text=f"Exp: {payload.get('exp')}", bg="#0f172a", fg="#e2e8f0").pack(anchor="w", padx=10, pady=2)
            ttk.Button(top, text="Copiar número", style="Menu.TButton", command=lambda: copy_to_clipboard_then_clear(self.root, payload.get("card"))).pack(pady=6)
            ttk.Button(top, text="Cerrar", style="Menu.TButton", command=top.destroy).pack(pady=6)
        except InvalidToken:
            audit("view_card_failed_invalidtoken", f"token={token}")
            view_attempt("PasarelaPagos", f"token={token}", success=False, reason="invalidtoken")
            messagebox.showerror("Error", "No fue posible desencriptar la tarjeta (token inválido).")
        except Exception as e:
            audit("view_card_failed", str(e))
            view_attempt("PasarelaPagos", f"token={token}", success=False, reason=str(e))
            messagebox.showerror("Error", f"No se pudo desencriptar la tarjeta: {e}")

    def _on_delete_method(self):
        f = verify_master_and_get_fernet(self.root, "eliminar método tokenizado")
        if f is None:
            return
        token = self._get_selected_method_token()
        if token is None:
            messagebox.showwarning("Selecciona", "Selecciona un método tokenizado.")
            return
        if not messagebox.askyesno("Confirmar", "Eliminar método tokenizado seleccionado?"):
            view_attempt("PasarelaPagos", f"token={token}", success=False, reason="user_cancel")
            return
        try:
            methods = load_payment_methods(self.root) or []
            methods = [m for m in methods if m.get("token") != token]
            ok = save_payment_methods(self.root, methods)
            if ok:
                audit("delete_method", f"token={token}")
                button_clicked("PasarelaPagos", "Eliminar método", f"token={token}")
                messagebox.showinfo("Eliminado", "Método eliminado.")
                self.methods = methods
                self._refresh_methods_ui()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el método.")
        except Exception as e:
            audit("delete_method_failed", str(e))
            messagebox.showerror("Error", f"No se pudo eliminar el método: {e}")

    def _use_selected_card(self):
        idx = self.saved_cards_cb.current()
        if idx < 0:
            messagebox.showwarning("Selecciona", "Selecciona una tarjeta en el desplegable.")
            return
        m = self.methods[idx]
        self.card_number_var.set(m.get("mask"))
        self.expiry_var.set("")
        self.cvv_var.set("")
        self.save_card_var.set(False)
        audit("use_token_loaded", f"token={m.get('token')}")
        button_clicked("PasarelaPagos", "Usar tarjeta seleccionada", f"token={m.get('token')}")
        messagebox.showinfo("Tarjeta cargada", "La tarjeta tokenizada se ha cargado para uso. Para ver el número real use 'Ver tarjeta (temporal)'.")

    # ---- Processing ----
    def _on_process_payment(self):
        client = self.client_var.get().strip()
        try:
            amount = float(self.amount_var.get())
        except Exception:
            messagebox.showwarning("Validación", "Ingresa un monto numérico válido.")
            return
        if amount <= 0:
            messagebox.showwarning("Validación", "El monto debe ser mayor que 0.")
            return

        method = self.method_var.get()
        audit("process_payment_attempt", f"client={client} amount={amount} method={method}")
        button_clicked("PasarelaPagos", "Procesar pago", f"client={client} amount={amount} method={method}")

        if method in ("Tarjeta crédito","Tarjeta débito"):
            ok, result, mask = self._process_card(amount)
        elif method == "PSE":
            ok, result, mask = self._process_pse(amount)
        elif method in ("Nequi","Daviplata"):
            ok, result, mask = self._process_wallet(amount, provider=method)
        elif method == "Transferencia Bancolombia":
            ok, result, mask = self._process_transfer(amount)
        elif method == "Efectivo":
            ok, result, mask = self._process_cash(amount)
        else:
            messagebox.showerror("Error", "Método de pago no soportado.")
            return

        tx = {
            "id": result.get("id"),
            "cliente": client,
            "amount": amount,
            "method": method,
            "status": result.get("status"),
            "processor_code": result.get("processor_code"),
            "message": result.get("message"),
            "time": datetime.now().isoformat(),
            "card_mask": mask,
            "extra": result.get("extra", {})
        }
        save_transaction(tx)
        audit("process_payment_result", f"id={tx['id']} status={tx['status']} client={client} amount={amount} method={method}")
        self._refresh_transactions_ui()
        if ok:
            messagebox.showinfo("Pago aprobado", f"Pago aprobado. ID: {tx['id']}")
        else:
            messagebox.showwarning("Pago rechazado", f"Pago rechazado: {result.get('message')}")

        # Guardar tarjeta tras cobro si aplica
        if method in ("Tarjeta crédito","Tarjeta débito"):
            tokenized = any(self.card_number_var.get().strip() == (m.get("mask") or "") for m in (self.methods or []))
            if self.save_card_var.get() and not tokenized:
                self._tokenize_after_charge()

    # ---- Method-specific processors ----
    def _process_card(self, amount: float):
        token = None
        entered = self.card_number_var.get().strip()
        selected_method = None
        for m in (self.methods or []):
            if entered and m.get("mask") == entered:
                token = m.get("token")
                selected_method = m
                break

        full_card = None
        if token:
            f = verify_master_and_get_fernet(self.root, "procesar pago con tarjeta tokenizada")
            if f is None:
                return False, {"id": str(uuid.uuid4()), "status": "declined", "processor_code": "99", "message": "Acceso denegado"}, None
            try:
                dec = f.decrypt(selected_method.get("enc").encode("utf-8"))
                payload = json.loads(dec.decode("utf-8"))
                full_card = payload.get("card")
            except Exception as e:
                audit("process_failed_decrypt", str(e))
                messagebox.showerror("Error", "No se pudo acceder a la tarjeta tokenizada.")
                return False, {"id": str(uuid.uuid4()), "status": "declined", "processor_code": "99", "message": "Token inválido"}, None
        else:
            full_card = ''.join(filter(str.isdigit, self.card_number_var.get()))
            if not luhn_checksum(full_card):
                messagebox.showwarning("Validación", "Número de tarjeta inválido (Luhn).")
                return False, {"id": str(uuid.uuid4()), "status": "declined", "processor_code": "05", "message": "Tarjeta inválida"}, None
            exp = self.expiry_var.get().strip()
            if "/" in exp:
                mm, yy = exp.split("/", 1)
                try:
                    mm = int(mm); yy = int(yy)
                    if mm < 1 or mm > 12:
                        raise ValueError()
                except Exception:
                    messagebox.showwarning("Validación", "Formato de expiración inválido (MM/AA).")
                    return False, {"id": str(uuid.uuid4()), "status": "declined", "processor_code": "05", "message": "Expiración inválida"}, None

        ok, result = simulate_charge(full_card, amount)
        mask = mask_card(full_card) if full_card else None
        return ok, result, mask

    def _process_pse(self, amount: float):
        bank = self.pse_bank_var.get().strip()
        acc_type = self.pse_account_type_var.get().strip()
        doc = self.pse_doc_var.get().strip()
        if not bank or not acc_type or not doc:
            messagebox.showwarning("Validación", "Completa banco, tipo de cuenta y documento.")
            return False, {"id": str(uuid.uuid4()), "status": "declined", "processor_code": "05", "message": "Datos PSE incompletos"}, None
        time.sleep(0.8)
        ok = secrets.randbelow(100) >= 8
        result = {
            "id": str(uuid.uuid4()),
            "status": "approved" if ok else "declined",
            "processor_code": "00" if ok else "05",
            "message": "Aprobado PSE" if ok else "Rechazado por banco",
            "amount": amount,
            "extra": {"bank": bank, "account_type": acc_type, "doc": doc}
        }
        return ok, result, f"PSE-{bank}"

    def _process_wallet(self, amount: float, provider: str):
        phone = self.wallet_phone_var.get().strip()
        ref = self.wallet_ref_var.get().strip()
        if not phone or len(''.join(filter(str.isdigit, phone))) < 10:
            messagebox.showwarning("Validación", "Número de celular inválido.")
            return False, {"id": str(uuid.uuid4()), "status": "declined", "processor_code": "05", "message": "Celular inválido"}, None
        if not ref:
            messagebox.showwarning("Validación", "Ingresa una referencia de pago.")
            return False, {"id": str(uuid.uuid4()), "status": "declined", "processor_code": "05", "message": "Referencia requerida"}, None
        time.sleep(0.7)
        ok = secrets.randbelow(100) >= 7
        result = {
            "id": str(uuid.uuid4()),
            "status": "approved" if ok else "declined",
            "processor_code": "00" if ok else "05",
            "message": f"Aprobado {provider}" if ok else f"Rechazado por {provider}",
            "amount": amount,
            "extra": {"provider": provider, "phone": phone, "ref": ref}
        }
        return ok, result, f"{provider}-{phone[-4:]}"

    def _process_transfer(self, amount: float):
        bank = self.transfer_bank_var.get().strip()
        ref = self.transfer_ref_var.get().strip()
        if not bank or not ref:
            messagebox.showwarning("Validación", "Completa banco y referencia/comprobante.")
            return False, {"id": str(uuid.uuid4()), "status": "declined", "processor_code": "05", "message": "Datos de transferencia incompletos"}, None
        time.sleep(0.5)
        ok = True  # Transferencia marcada como recibida manualmente
        result = {
            "id": str(uuid.uuid4()),
            "status": "approved" if ok else "declined",
            "processor_code": "00" if ok else "05",
            "message": "Comprobante verificado",
            "amount": amount,
            "extra": {"bank": bank, "ref": ref}
        }
        return ok, result, f"TR-{bank}"

    def _process_cash(self, amount: float):
        note = self.cash_note_var.get().strip()
        time.sleep(0.2)
        ok = True
        result = {
            "id": str(uuid.uuid4()),
            "status": "approved",
            "processor_code": "00",
            "message": "Pago en efectivo registrado",
            "amount": amount,
            "extra": {"note": note}
        }
        return ok, result, "EFECTIVO"

    def _tokenize_after_charge(self):
        f = verify_master_and_get_fernet(self.root, "guardar tarjeta tras cobro")
        if f is None:
            return
        full_card = ''.join(filter(str.isdigit, self.card_number_var.get()))
        token_new = str(uuid.uuid4())
        masked = mask_card(full_card)
        brand = "CARD"
        payload = {"card": full_card, "exp": self.expiry_var.get().strip()}
        try:
            enc = f.encrypt(json.dumps(payload).encode("utf-8"))
            methods = load_payment_methods(self.root) or []
            methods.append({
                "token": token_new,
                "mask": masked,
                "brand": brand,
                "enc": enc.decode("utf-8"),
                "created_at": datetime.now().isoformat()
            })
            ok2 = save_payment_methods(self.root, methods)
            if ok2:
                audit("tokenize_card_on_charge", f"token={token_new} mask={masked}")
                button_clicked("PasarelaPagos", "Guardar tarjeta tras cobro", f"mask={masked}")
                messagebox.showinfo("Guardado", f"Tarjeta guardada tokenizada como {masked}")
                self.methods = methods
                self._refresh_methods_ui()
            else:
                messagebox.showerror("Error", "No se pudo guardar la tarjeta tokenizada.")
        except Exception as e:
            audit("tokenize_on_charge_failed", str(e))

    # ---- Export & audit ----
    def _on_export_transactions(self):
        f = verify_master_and_get_fernet(self.root, "exportar transacciones")
        if f is None:
            return
        txs = load_transactions()
        if not txs:
            messagebox.showwarning("Sin datos", "No hay transacciones para exportar.")
            return
        fname = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")])
        if not fname:
            return
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Transacciones"
            ws.append(["ID","Cliente","Monto","Método","Estado","Mensaje","Fecha","Tarjeta/Ref","Extra"])
            for t in txs:
                ws.append([
                    t.get("id"),
                    t.get("cliente"),
                    t.get("amount"),
                    t.get("method"),
                    t.get("status"),
                    t.get("message"),
                    t.get("time"),
                    t.get("card_mask"),
                    json.dumps(t.get("extra", {}), ensure_ascii=False)
                ])
            wb.save(fname)
            audit("export_transactions", fname)
            button_clicked("PasarelaPagos", "Exportar transacciones", fname)
            messagebox.showinfo("Exportado", f"Transacciones exportadas a:\n{fname}")
        except Exception as e:
            audit("export_failed", str(e))
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

    def _open_audit(self):
        ensure_base_dir()
        if not os.path.exists(AUDIT_LOG):
            messagebox.showinfo("Audit log", "No hay registros de auditoría aún.")
            return
        with open(AUDIT_LOG, "r", encoding="utf-8") as f:
            data = f.read()
        top = tk.Toplevel(self.root)
        top.title("Audit log")
        txt = tk.Text(top, width=120, height=30)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", data)
        txt.config(state="disabled")
        button_clicked("PasarelaPagos", "Ver audit log", "")

    def _on_close(self):
        module_closed("PasarelaPagos", "window_closed")
        self.root.destroy()

# ---- small utils reused ----
def luhn_checksum(card_number: str) -> bool:
    s = ''.join(filter(str.isdigit, card_number))
    if not s:
        return False
    total = 0
    reverse_digits = s[::-1]
    for i, ch in enumerate(reverse_digits):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0

def mask_card(card_number: str) -> str:
    s = ''.join(filter(str.isdigit, card_number))
    if len(s) <= 4:
        return s
    return "**** **** **** " + s[-4:]

def simulate_charge(card_full: str, amount: float):
    time.sleep(0.6)
    tx_id = str(uuid.uuid4())
    ok = secrets.randbelow(100) >= 5
    result = {
        "id": tx_id,
        "status": "approved" if ok else "declined",
        "processor_code": "00" if ok else "05",
        "message": "Aprobado" if ok else "Rechazado por emisor",
        "amount": amount
    }
    return ok, result

# ---- Run standalone ----
if __name__ == "__main__":
    ensure_base_dir()
    root = tk.Tk()
    app = PasarelaPagos(root)
    root.mainloop()
