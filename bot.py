#!/usr/bin/env python3
"""
Discord Video Bot - Bot de descarga automática de videos
Detecta enlaces, descarga con yt-dlp y envía archivos o publica online.
"""

import discord
import asyncio
import subprocess
import os
import re
import json
import time
import random
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from dotenv import load_dotenv

# Importar utilidades
from utils import log, format_size, cleanup_file, get_temp_path, ensure_temp_dir

# Cargar variables de entorno
load_dotenv()

# ==================== CONSTANTES ====================
TIMEOUT_SECONDS = 300
MAX_ATTACHMENT_BYTES = 15_728_640  # 15 MB exactos
FILE_RETENTION_SECONDS = 3600  # 1 hora

# ==================== VARIABLES GLOBALES ====================
download_lock = asyncio.Lock()
active_servers = {}  # {port: server_instance}
server_threads = {}  # {port: thread}

# ==================== CLIENTE DISCORD ====================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ==================== SERVIDOR HTTP ====================
class CustomHandler(SimpleHTTPRequestHandler):
    """Handler personalizado para servir archivos"""
    
    def __init__(self, *args, file_path=None, **kwargs):
        self.file_path = file_path
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Maneja peticiones GET"""
        try:
            # Servir solo el archivo específico
            if self.file_path and os.path.exists(self.file_path):
                self.send_response(200)
                
                # Detectar content-type
                filename = os.path.basename(self.file_path)
                if filename.endswith('.mp4'):
                    self.send_header('Content-type', 'video/mp4')
                elif filename.endswith('.webm'):
                    self.send_header('Content-type', 'video/webm')
                elif filename.endswith('.mkv'):
                    self.send_header('Content-type', 'video/x-matroska')
                else:
                    self.send_header('Content-type', 'application/octet-stream')
                
                self.send_header('Content-Disposition', f'inline; filename="{filename}"')
                self.send_header('Content-Length', str(os.path.getsize(self.file_path)))
                self.end_headers()
                
                # Enviar archivo
                with open(self.file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Archivo no encontrado")
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")
    
    def log_message(self, format, *args):
        """Silenciar logs del servidor HTTP"""
        pass

def create_server(file_path, port):
    """
    Crea servidor HTTP para servir archivo
    
    Args:
        file_path: Ruta al archivo a servir
        port: Puerto para el servidor
    Returns:
        Instancia del servidor
    """
    handler = lambda *args, **kwargs: CustomHandler(*args, file_path=file_path, **kwargs)
    server = ThreadingHTTPServer(('', port), handler)
    return server

def start_file_server(file_path, port):
    """
    Inicia servidor en thread separado
    
    Args:
        file_path: Ruta al archivo
        port: Puerto del servidor
    Returns:
        True si se inició correctamente
    """
    try:
        server = create_server(file_path, port)
        active_servers[port] = server
        
        def serve():
            server.serve_forever()
        
        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        server_threads[port] = thread
        
        return True
    except Exception as e:
        log("error", {"code": "103", "message": "No se pudo iniciar servidor", "details": str(e)})
        return False

def stop_file_server(port):
    """
    Detiene servidor HTTP
    
    Args:
        port: Puerto del servidor a detener
    """
    try:
        if port in active_servers:
            active_servers[port].shutdown()
            del active_servers[port]
            log("server_shutdown", {"port": port})
    except Exception as e:
        print(f"Error al detener servidor: {e}")

def get_public_ip():
    """
    Obtiene IP pública (simplificado - retorna localhost para desarrollo)
    En producción, podría usar servicios externos o configuración
    """
    # Por defecto usa localhost, en producción configurar IP pública
    return "localhost"

def schedule_cleanup(file_path, port=None, delay=FILE_RETENTION_SECONDS):
    """
    Programa limpieza de archivo y servidor después de delay segundos
    
    Args:
        file_path: Ruta al archivo a eliminar
        port: Puerto del servidor a detener (opcional)
        delay: Segundos antes de limpiar
    """
    def cleanup():
        time.sleep(delay)
        
        # Detener servidor si existe
        if port:
            stop_file_server(port)
        
        # Eliminar archivo
        cleanup_file(file_path)
    
    thread = threading.Thread(target=cleanup, daemon=True)
    thread.start()

# ==================== DESCARGA YT-DLP ====================
async def run_ytdlp(url, output_path):
    """
    Ejecuta yt-dlp para descargar video
    
    Args:
        url: URL del video
        output_path: Ruta donde guardar el archivo
    Returns:
        (success: bool, result: str) - result es ruta del archivo o mensaje de error
    """
    try:
        # Comando yt-dlp
        cmd = [
            "yt-dlp",
            "-o", output_path,
            "--no-playlist",
            "-f", "best[filesize<50M]/best",  # Preferir archivos <50MB
            "--max-filesize", "100M",  # Límite de seguridad
            url
        ]
        
        # Ejecutar con timeout
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return False, "TIMEOUT"
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Error desconocido"
            return False, error_msg
        
        # Verificar que se creó el archivo
        if os.path.exists(output_path):
            # yt-dlp puede añadir extensión automáticamente
            # Buscar archivo descargado
            for ext in ['.mp4', '.webm', '.mkv', '.mov', '.avi']:
                potential_file = output_path + ext
                if os.path.exists(potential_file):
                    return True, potential_file
            
            # Si no tiene extensión añadida, verificar el archivo exacto
            return True, output_path
        
        # Buscar cualquier archivo reciente en temp
        temp_dir = ensure_temp_dir()
        files = os.listdir(temp_dir)
        if files:
            # Retornar el más reciente
            latest = max(files, key=lambda f: os.path.getctime(os.path.join(temp_dir, f)))
            return True, os.path.join(temp_dir, latest)
        
        return False, "No se generó archivo"
        
    except Exception as e:
        return False, str(e)

# ==================== MANEJO DE MENSAJES ====================
def extract_url(text):
    """
    Extrae primera URL http/https del texto
    
    Args:
        text: Texto a analizar
    Returns:
        URL encontrada o None
    """
    # Patrón para detectar URLs
    url_pattern = r'https?://[^\s<>\"{}|\\^`\\[\\]]+'
    match = re.search(url_pattern, text)
    
    if match:
        return match.group(0)
    return None

async def process_download(message, url):
    """
    Procesa descarga y envío de archivo
    
    Args:
        message: Objeto mensaje de Discord
        url: URL a descargar
    """
    start_time = time.time()
    
    # Logging de inicio
    log_data = {
        "username": str(message.author),
        "user_id": message.author.id,
        "channel": str(message.channel),
        "guild": str(message.guild) if message.guild else "DM",
        "url": url
    }
    log("download_start", log_data)
    
    # Generar nombre de archivo único
    timestamp = int(time.time())
    safe_name = f"download_{timestamp}_{message.author.id}"
    output_path = get_temp_path(safe_name)
    
    # Descargar
    success, result = await run_ytdlp(url, output_path)
    
    if not success:
        if result == "TIMEOUT":
            log("timeout", None)
            await message.channel.send("❌ ERROR 101: La descarga ha tardado más de 5 minutos y ha sido cancelada.")
        else:
            log("error", {"code": "102", "message": "No se pudo descargar", "details": result})
            await message.channel.send("❌ ERROR 102: No se pudo descargar el enlace. Puede ser inválido o estar protegido.")
        return
    
    # Verificar archivo resultante
    downloaded_file = result
    if not os.path.exists(downloaded_file):
        log("error", {"code": "102", "message": "Archivo no encontrado tras descarga"})
        await message.channel.send("❌ ERROR 102: No se pudo descargar el enlace. Puede ser inválido o estar protegido.")
        return
    
    # Obtener tamaño
    file_size = os.path.getsize(downloaded_file)
    duration = time.time() - start_time
    
    # Logging de éxito
    log("download_success", {
        "filename": os.path.basename(downloaded_file),
        "size_formatted": format_size(file_size),
        "duration": duration
    })
    
    # Decidir si adjuntar o servir online
    if file_size <= MAX_ATTACHMENT_BYTES:
        # Enviar como adjunto
        await send_as_attachment(message, downloaded_file)
    else:
        # Publicar online
        await serve_online(message, downloaded_file)

async def send_as_attachment(message, file_path):
    """
    Envía archivo como adjunto de Discord
    
    Args:
        message: Objeto mensaje
        file_path: Ruta al archivo
    """
    try:
        filename = os.path.basename(file_path)
        
        log("attachment_sent", {"filename": filename})
        
        # Enviar mensaje con archivo
        with open(file_path, 'rb') as f:
            discord_file = discord.File(f, filename=filename)
            await message.channel.send("✅ Listo — aquí tienes tu archivo.", file=discord_file)
        
        # Limpiar archivo inmediatamente
        cleanup_file(file_path)
        
    except Exception as e:
        log("error", {"code": "110", "message": "Error al enviar adjunto", "details": str(e)})
        await message.channel.send("❌ ERROR 110: Error interno al enviar el archivo.")
        cleanup_file(file_path)

async def serve_online(message, file_path):
    """
    Publica archivo en servidor HTTP temporal
    
    Args:
        message: Objeto mensaje
        file_path: Ruta al archivo
    """
    try:
        filename = os.path.basename(file_path)
        
        # Determinar puerto
        port_config = os.getenv('SERVE_PORT', 'auto')
        if port_config.lower() == 'auto':
            port = random.randint(8000, 8999)
        else:
            port = int(port_config)
        
        # Intentar iniciar servidor (con reintentos si el puerto está ocupado)
        max_attempts = 10
        for attempt in range(max_attempts):
            if start_file_server(file_path, port):
                break
            port = random.randint(8000, 8999)
        else:
            log("error", {"code": "103", "message": "No se pudo iniciar servidor después de varios intentos"})
            await message.channel.send("❌ ERROR 103: No se pudo publicar el archivo online.")
            cleanup_file(file_path)
            return
        
        # Generar URL
        ip = get_public_ip()
        url = f"http://{ip}:{port}/{filename}"
        
        log("serving_file", {
            "filename": filename,
            "url": url,
            "expires": FILE_RETENTION_SECONDS
        })
        
        # Enviar mensaje con enlace
        await message.channel.send(
            f"✅ Archivo demasiado grande para adjuntar.\\n"
            f"🔗 Enlace temporal (expira en 1 hora): {url}"
        )
        
        # Programar limpieza
        schedule_cleanup(file_path, port, FILE_RETENTION_SECONDS)
        
    except Exception as e:
        log("error", {"code": "103", "message": "Error al publicar online", "details": str(e)})
        await message.channel.send("❌ ERROR 103: No se pudo publicar el archivo online.")
        cleanup_file(file_path)

# ==================== EVENTOS DISCORD ====================
@client.event
async def on_ready():
    """Evento cuando el bot está listo"""
    print(f"🤖 Bot conectado como {client.user}")
    print(f"📊 Latencia: {round(client.latency * 1000)}ms")
    print("=" * 50)

@client.event
async def on_message(message):
    """Evento al recibir mensaje"""
    # Ignorar mensajes del propio bot
    if message.author == client.user:
        return
    
    # Ignorar mensajes de otros bots
    if message.author.bot:
        return
    
    # Permitir mensajes de DM (canales privados) y canales de servidor
    # No filtrar por tipo de canal - procesar todos los mensajes con enlaces
    
    # Extraer URL del mensaje
    url = extract_url(message.content)
    if not url:
        return  # No hay enlace, ignorar
    
    # Verificar si el bot está ocupado
    if download_lock.locked():
        # Notificar en DM que está ocupado
        if isinstance(message.channel, discord.DMChannel):
            await message.channel.send("🔒 ERROR 100: Bot ocupado, intenta más tarde.")
        log("busy", None)
        return
    
    # Procesar descarga con lock
    async with download_lock:
        await process_download(message, url)


# ==================== INICIO ====================
def main():
    """Función principal"""
    # Verificar token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ ERROR: No se encontró DISCORD_TOKEN en .env")
        print("💡 Ejecuta setup.py para configurar el bot")
        return
    
    # Verificar yt-dlp instalado
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True)
        print(f"✅ yt-dlp versión: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ ERROR: yt-dlp no está instalado")
        print("💡 Instálalo con: pip install yt-dlp")
        return
    
    # Crear directorio temp
    ensure_temp_dir()
    
    # Iniciar bot
    print("🚀 Iniciando bot...")
    try:
        client.run(token)
    except discord.LoginFailure:
        print("❌ ERROR: Token de Discord inválido")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    main()
