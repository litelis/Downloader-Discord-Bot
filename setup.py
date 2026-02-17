#!/usr/bin/env python3
"""
Instalador automático para Discord Video Bot
Crea entorno virtual, instala dependencias y configura el bot.
"""

import os
import sys
import subprocess
import venv
from pathlib import Path

# Colores para output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    YELLOW = Fore.YELLOW
    GREEN = Fore.GREEN
    RED = Fore.RED
    CYAN = Fore.CYAN
    RESET = Style.RESET_ALL
except ImportError:
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

def print_status(message, color=CYAN):
    """Imprime mensaje con color"""
    print(f"{color}{message}{RESET}")

def print_installing(package):
    """Muestra mensaje de instalación"""
    print(f"{YELLOW}📦 Instalando {package}...{RESET}")

def print_installed(package):
    """Muestra mensaje de instalado"""
    print(f"{GREEN}✅ {package} instalado{RESET}")

def print_error(message):
    """Muestra mensaje de error"""
    print(f"{RED}❌ Error: {message}{RESET}")

def run_command(cmd, capture=True):
    """Ejecuta comando y captura output"""
    try:
        if capture:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True,
                check=True
            )
            return result
        else:
            subprocess.run(cmd, shell=True, check=True)
            return None
    except subprocess.CalledProcessError as e:
        raise e

def create_venv():
    """Crea entorno virtual"""
    print_status("🐍 Creando entorno virtual...")
    venv_path = Path(".venv")
    
    if venv_path.exists():
        print_status("⚠️  Entorno virtual ya existe, usando existente", YELLOW)
        return str(venv_path)
    
    venv.create(venv_path, with_pip=True)
    print_status("✅ Entorno virtual creado", GREEN)
    return str(venv_path)

def get_venv_python():
    """Obtiene ruta al python del venv"""
    if os.name == 'nt':  # Windows
        return r".venv\Scripts\python.exe"
    else:  # Linux/Mac
        return ".venv/bin/python"

def get_venv_pip():
    """Obtiene ruta al pip del venv"""
    if os.name == 'nt':  # Windows
        return r".venv\Scripts\pip.exe"
    else:  # Linux/Mac
        return ".venv/bin/pip"

def install_dependencies():
    """Instala dependencias una a una"""
    dependencies = [
        "colorama",
        "python-dotenv",
        "discord.py",
        "yt-dlp"
    ]
    
    pip = get_venv_pip()
    
    for package in dependencies:
        print_installing(package)
        try:
            cmd = f'"{pip}" install {package} -q'
            run_command(cmd)
            print_installed(package)
        except subprocess.CalledProcessError as e:
            print_error(f"No se pudo instalar {package}")
            print(f"{RED}{e}{RESET}")
            return False
    
    return True

def setup_env():
    """Configura archivo .env"""
    print_status("\n🔧 Configuración de Discord Bot", CYAN)
    print("=" * 50)
    
    env_path = Path(".env")
    
    if env_path.exists():
        overwrite = input(f"{YELLOW}⚠️  .env ya existe. ¿Sobrescribir? (s/n): {RESET}").lower()
        if overwrite != 's':
            print_status("⏭️  Saltando configuración de .env", YELLOW)
            return
    
    token = input(f"{CYAN}🔑 Ingresa tu DISCORD_TOKEN: {RESET}").strip()
    
    print(f"\n{CYAN}🌐 Modo de servidor:{RESET}")
    print("  1. http (servidor HTTP local - recomendado)")
    serve_mode = "http"
    
    port_choice = input(f"{CYAN}📡 Puerto (auto para aleatorio 8000-8999, o número específico): {RESET}").strip()
    serve_port = port_choice if port_choice else "auto"
    
    env_content = f"""DISCORD_TOKEN={token}
SERVE_MODE={serve_mode}
SERVE_PORT={serve_port}
"""
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print_status("✅ Archivo .env creado", GREEN)

def setup_config():
    """Configura archivo config.json"""
    print_status("\n📝 Configuración de logs", CYAN)
    print("=" * 50)
    
    print(f"{CYAN}Modos disponibles:{RESET}")
    print("  1. detailed - Muestra usuario, ID, canal, servidor, enlace, resultado")
    print("  2. minimal - Solo uso y hora")
    
    choice = input(f"{CYAN}Selecciona modo (1/2) [default: 1]: {RESET}").strip()
    
    log_mode = "minimal" if choice == "2" else "detailed"
    
    config = {
        "log_mode": log_mode
    }
    
    import json
    with open("config.json", 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    print_status(f"✅ Configuración guardada: modo {log_mode}", GREEN)

def create_temp_dir():
    """Crea carpeta temporal"""
    temp_path = Path("temp")
    if not temp_path.exists():
        temp_path.mkdir()
        print_status("📁 Carpeta temp/ creada", GREEN)

def start_bot():
    """Pregunta si iniciar el bot"""
    print_status("\n🚀 ¿Deseas iniciar el bot ahora?", CYAN)
    choice = input(f"{CYAN}Iniciar bot? (s/n): {RESET}").lower()
    
    if choice == 's':
        print_status("🤖 Iniciando bot...", GREEN)
        python = get_venv_python()
        try:
            subprocess.run(f'"{python}" bot.py', shell=True)
        except KeyboardInterrupt:
            print_status("\n👋 Bot detenido", YELLOW)
    else:
        print_status("⏹️  Puedes iniciar el bot después con: python bot.py", CYAN)

def main():
    """Función principal del instalador"""
    print_status("=" * 60, CYAN)
    print_status("  DISCORD VIDEO BOT - INSTALADOR", CYAN)
    print_status("=" * 60, CYAN)
    print()
    
    # Verificar que estamos en el directorio correcto
    if not Path(".").resolve().name == "download with discord":
        print_status(f"📂 Directorio actual: {Path('.').resolve()}", YELLOW)
    
    # Crear estructura
    create_venv()
    create_temp_dir()
    
    # Instalar dependencias
    print_status("\n📥 Instalando dependencias...", CYAN)
    if not install_dependencies():
        print_error("Falló la instalación de dependencias")
        sys.exit(1)
    
    # Configuración
    setup_env()
    setup_config()
    
    print_status("\n" + "=" * 60, GREEN)
    print_status("  ✅ INSTALACIÓN COMPLETADA", GREEN)
    print_status("=" * 60, GREEN)
    
    # Preguntar si iniciar
    start_bot()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_status("\n\n👋 Instalación cancelada por usuario", YELLOW)
        sys.exit(0)
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        sys.exit(1)
