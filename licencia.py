#!/usr/bin/env python3
# licencia.py - Generador interactivo de licencias (RSA firmado)
# Guarda en: C:\RICHARD\RB\2025\Taller-mecánica\licencia.py

import os
import json
import base64
from datetime import datetime, timedelta
import argparse

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import serialization, hashes
except Exception as e:
    print("Falta la librería 'cryptography'. Instálala con:")
    print("  python -m pip install cryptography")
    raise

BASE_DIR = r"C:\RICHARD\RB\2025\Taller-mecánica"
PRIVATE_KEY_FILE = os.path.join(BASE_DIR, "private.pem")
PUBLIC_KEY_FILE = os.path.join(BASE_DIR, "public.pem")
LICENSES_RECORD = os.path.join(BASE_DIR, "licencias.json")

def ensure_dir():
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


def generate_keypair(bits=2048, passphrase: bytes = None):
    ensure_dir()
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    enc_algo = serialization.BestAvailableEncryption(passphrase) if passphrase else serialization.NoEncryption()
    with open(PRIVATE_KEY_FILE, "wb") as f:
        f.write(private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            enc_algo
        ))
    public_key = private_key.public_key()
    with open(PUBLIC_KEY_FILE, "wb") as f:
        f.write(public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    print("Par de claves generado:")
    print(" - Private key:", PRIVATE_KEY_FILE)
    print(" - Public key: ", PUBLIC_KEY_FILE)

def _b64u_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")

def _b64u_decode(s: str) -> bytes:
    s2 = s.encode("ascii")
    rem = len(s2) % 4
    if rem:
        s2 += b"=" * (4 - rem)
    return base64.urlsafe_b64decode(s2)

def create_license(usuario: str, valid_days: int = 365, metadata: dict = None, private_key_path: str = None, save_record: bool = True) -> str:
    ensure_dir()
    if private_key_path is None:
        private_key_path = PRIVATE_KEY_FILE
    if not os.path.exists(private_key_path):
        raise FileNotFoundError(f"No se encontró la clave privada en: {private_key_path}. Genera keys primero.")
    with open(private_key_path, "rb") as f:
        priv = serialization.load_pem_private_key(f.read(), password=None)

    exp = (datetime.utcnow() + timedelta(days=valid_days)).date().isoformat()
    payload = {
        "usuario": usuario,
        "expira": exp,
        "issued": datetime.utcnow().isoformat(),
    }
    if metadata:
        payload["meta"] = metadata

    payload_b = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    payload_b64 = _b64u_encode(payload_b)

    sig = priv.sign(
        payload_b,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )
    sig_b64 = _b64u_encode(sig)

    token = payload_b64 + "." + sig_b64

    if save_record:
        try:
            if os.path.exists(LICENSES_RECORD):
                with open(LICENSES_RECORD, "r", encoding="utf-8") as rf:
                    arr = json.load(rf)
            else:
                arr = []
            arr.append({"usuario": usuario, "expira": exp, "token": token, "issued": payload["issued"]})
            with open(LICENSES_RECORD, "w", encoding="utf-8") as wf:
                json.dump(arr, wf, indent=2, ensure_ascii=False)
        except Exception as e:
            print("Advertencia: no se pudo guardar registro de licencias:", e)
    return token

def interactive_menu():
    print("=== Generador de Licencias (interactivo) ===")
    while True:
        print("\nOpciones:")
        print("  1) Generar par de claves (private.pem + public.pem)")
        print("  2) Crear licencia para cliente")
        print("  3) Mostrar ruta de keys / licencias")
        print("  4) Salir")
        choice = input("Elige una opción [1-4]: ").strip()
        if choice == "1":
            bits = input("Tamaño de clave (2048 recomendado): ").strip()
            bits = int(bits) if bits.isdigit() else 2048
            generate_keypair(bits=bits)
        elif choice == "2":
            usuario = input("Usuario/identificador del cliente: ").strip()
            dias = input("Días de validez (ej. 90): ").strip()
            dias = int(dias) if dias.isdigit() else 365
            try:
                token = create_license(usuario, valid_days=dias)
                print("\nLicencia generada (entregar al cliente):\n")
                print(token)
                guardar = input("\n¿Guardar token en archivo? (ruta) [Enter = no]: ").strip()
                if guardar:
                    with open(guardar, "w", encoding="utf-8") as f:
                        f.write(token)
                    print("Token guardado en:", guardar)
            except Exception as e:
                print("Error generando licencia:", e)
        elif choice == "3":
            print("BASE_DIR:", BASE_DIR)
            print("PRIVATE_KEY_FILE:", PRIVATE_KEY_FILE)
            print("PUBLIC_KEY_FILE :", PUBLIC_KEY_FILE)
            print("LICENSES_RECORD :", LICENSES_RECORD)
        elif choice == "4":
            print("Saliendo.")
            break
        else:
            print("Opción inválida.")

def cli_main():
    parser = argparse.ArgumentParser(description="Generador de licencias firmado (RSA).")
    parser.add_argument("--gen-keys", action="store_true", help="Generar par de claves (private.pem/public.pem).")
    parser.add_argument("--usuario", help="Usuario o identificador para la licencia.")
    parser.add_argument("--days", type=int, default=365, help="Días de validez de la licencia.")
    parser.add_argument("--out", help="Archivo para guardar el token (opcional).")
    args = parser.parse_args()

    if args.gen_keys:
        generate_keypair()
        return

    if args.usuario:
        token = create_license(args.usuario, valid_days=args.days)
        print("\nLicencia generada:\n")
        print(token)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(token)
            print("Token guardado en:", args.out)
        return

    # If no args provided, go interactive
    interactive_menu()

if __name__ == "__main__":
    cli_main()
