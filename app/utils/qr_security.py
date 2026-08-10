import hashlib
import hmac
import os
from pathlib import Path

from dotenv import load_dotenv


# Ruta directa al archivo backend/.env
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"

# Cargar las variables del archivo .env
load_dotenv(dotenv_path=ENV_PATH)


def generar_firma_qr(
    usuario_id: int | str,
    timestamp: int
) -> str:
    """
    Genera una firma segura usando el usuario,
    el timestamp y la SECRET_KEY del proyecto.
    """
    secret_key = os.getenv("SECRET_KEY")

    if not secret_key:
        raise RuntimeError(
            f"No se encontró SECRET_KEY. Archivo buscado: {ENV_PATH}"
        )

    mensaje = f"{usuario_id}:{timestamp}".encode("utf-8")

    firma_completa = hmac.new(
        secret_key.encode("utf-8"),
        mensaje,
        hashlib.sha256
    ).hexdigest()

    return firma_completa[:16]


def validar_firma_qr(
    usuario_id: int | str,
    timestamp: int,
    firma_recibida: str
) -> bool:
    """
    Calcula nuevamente la firma esperada
    y la compara con la firma recibida.
    """
    firma_esperada = generar_firma_qr(
        usuario_id=usuario_id,
        timestamp=timestamp
    )

    return hmac.compare_digest(
        firma_recibida,
        firma_esperada
    )