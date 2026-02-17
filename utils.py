"""
Utilidades para Discord Video Bot
Funciones de logging y manejo de archivos
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Intentar importar colorama, si no está disponible usar strings vacíos
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    YELLOW = Fore.YELLOW
    GREEN = Fore.GREEN
    RED = Fore.RED
    CYAN = Fore.CYAN
    MAGENTA = Fore.MAGENTA
    RESET = Style.RESET_ALL
except ImportError:
    YELLOW = GREEN = RED = CYAN = MAGENTA = RESET = ""

def load_config():
    """Carga configuración desde config.json"""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"log_mode": "detailed"}

def get_timestamp():
    """Obtiene timestamp actual formateado"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_detailed(message_type, data):
    """
    Logging detallado con toda la información
    
    Args:
        message_type: Tipo de mensaje (download, success, error, etc.)
        data: Diccionario con datos del mensaje
    """
    timestamp = get_timestamp()
    
    if message_type == "download_start":
        print(f"{CYAN}[{timestamp}] 📥 INICIANDO DESCARGA{RESET}")
        print(f"  👤 Usuario: {data.get('username')} (ID: {data.get('user_id')})")
        print(f"  💬 Canal: {data.get('channel')}")
        print(f"  🏠 Servidor: {data.get('guild')}")
        print(f"  🔗 Enlace: {data.get('url')}")
        
    elif message_type == "download_success":
        print(f"{GREEN}[{timestamp}] ✅ DESCARGA COMPLETADA{RESET}")
        print(f"  📁 Archivo: {data.get('filename')}")
        print(f"  📊 Tamaño: {data.get('size_formatted')}")
        print(f"  ⏱️  Duración: {data.get('duration'):.2f}s")
        
    elif message_type == "attachment_sent":
        print(f"{GREEN}[{timestamp}] 📎 ENVIADO COMO ADJUNTO{RESET}")
        print(f"  📁 Archivo: {data.get('filename')}")
        
    elif message_type == "serving_file":
        print(f"{MAGENTA}[{timestamp}] 🌐 PUBLICADO ONLINE{RESET}")
        print(f"  📁 Archivo: {data.get('filename')}")
        print(f"  🔗 URL: {data.get('url')}")
        print(f"  ⏰ Expira en: {data.get('expires')}s")
        
    elif message_type == "error":
        print(f"{RED}[{timestamp}] ❌ ERROR {data.get('code')}{RESET}")
        print(f"  📝 Mensaje: {data.get('message')}")
        if data.get('details'):
            print(f"  🔍 Detalles: {data.get('details')}")
            
    elif message_type == "timeout":
        print(f"{RED}[{timestamp}] ⏱️  TIMEOUT{RESET}")
        print(f"  📝 La descarga excedió el tiempo límite")
        
    elif message_type == "busy":
        print(f"{YELLOW}[{timestamp}] 🔒 BOT OCUPADO{RESET}")
        print(f"  ⏭️  Mensaje ignorado - descarga en progreso")
        
    elif message_type == "cleanup":
        print(f"{YELLOW}[{timestamp}] 🧹 LIMPIEZA{RESET}")
        print(f"  🗑️  Archivo eliminado: {data.get('filename')}")
        
    elif message_type == "server_shutdown":
        print(f"{MAGENTA}[{timestamp}] 🔌 SERVIDOR APAGADO{RESET}")
        print(f"  🌐 Puerto: {data.get('port')}")

def log_minimal(message_type, data=None):
    """
    Logging minimal - solo uso básico y hora
    
    Args:
        message_type: Tipo de mensaje
        data: Datos opcionales
    """
    timestamp = get_timestamp()
    
    icons = {
        "download_start": "📥",
        "download_success": "✅",
        "attachment_sent": "📎",
        "serving_file": "🌐",
        "error": "❌",
        "timeout": "⏱️",
        "busy": "🔒",
        "cleanup": "🧹",
        "server_shutdown": "🔌"
    }
    
    icon = icons.get(message_type, "ℹ️")
    
    if message_type == "error":
        print(f"{RED}[{timestamp}] {icon} ERROR {data.get('code') if data else ''}{RESET}")
    elif message_type == "download_success":
        print(f"{GREEN}[{timestamp}] {icon} Descarga OK{RESET}")
    elif message_type == "serving_file":
        print(f"{MAGENTA}[{timestamp}] {icon} Online: {data.get('url') if data else ''}{RESET}")
    else:
        print(f"{CYAN}[{timestamp}] {icon} {message_type}{RESET}")

def log(message_type, data=None):
    """
    Función principal de logging que selecciona el modo
    
    Args:
        message_type: Tipo de mensaje
        data: Diccionario con datos adicionales
    """
    config = load_config()
    mode = config.get("log_mode", "detailed")
    
    if mode == "minimal":
        log_minimal(message_type, data)
    else:
        log_detailed(message_type, data)

def format_size(size_bytes):
    """
    Formata tamaño en bytes a formato legible
    
    Args:
        size_bytes: Tamaño en bytes
    Returns:
        String formateado (ej: "14.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def cleanup_file(filepath):
    """
    Elimina archivo si existe
    
    Args:
        filepath: Ruta al archivo
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            log("cleanup", {"filename": os.path.basename(filepath)})
            return True
    except Exception as e:
        print(f"{RED}Error al eliminar archivo: {e}{RESET}")
    return False

def ensure_temp_dir():
    """Asegura que existe el directorio temp"""
    temp_path = Path("temp")
    if not temp_path.exists():
        temp_path.mkdir()
    return str(temp_path)

def get_temp_path(filename):
    """
    Obtiene ruta completa en directorio temp
    
    Args:
        filename: Nombre del archivo
    Returns:
        Ruta completa
    """
    temp_dir = ensure_temp_dir()
    return os.path.join(temp_dir, filename)
