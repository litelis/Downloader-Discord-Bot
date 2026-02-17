# ⬇️ Downloader Discord Bot

Bot de Discord en Python que descarga videos automáticamente al detectar enlaces. Comparte cualquier enlace de video y el bot lo descargará y te lo enviará instantáneamente.

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/litelis/Downloader-Discord-Bot.git)



## ✨ Características

- **Detección automática**: Detecta enlaces `http://` o `https://` en mensajes
- **Descarga con yt-dlp**: Soporta múltiples plataformas (YouTube, TikTok, Twitter, etc.)
- **Límite de 15MB**: Archivos pequeños se envían como adjunto
- **Servidor HTTP temporal**: Archivos grandes se publican online por 1 hora
- **Concurrencia controlada**: Solo 1 descarga simultánea (sin cola)
- **Timeout de 5 minutos**: Cancela descargas que tardan más de 300 segundos
- **Sistema de errores**: Códigos de error claros (100, 101, 102, 103, 110)
- **Logs configurables**: Modo detailed o minimal

## 📁 Estructura

```
discord-video-bot/
├── bot.py          # Lógica principal del bot
├── setup.py        # Instalador automático
├── utils.py        # Funciones auxiliares y logging
├── config.json     # Configuración de logs
├── .env            # Variables de entorno (token)
├── temp/           # Carpeta temporal para descargas
└── README.md       # Este archivo
```

## 🚀 Instalación

### Método 1: Instalación Automática (Recomendado)

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/litelis/Downloader-Discord-Bot.git
   cd Downloader-Discord-Bot
   ```


2. **Ejecutar el instalador**:
   ```bash
   python setup.py
   ```

3. **Seguir las instrucciones interactivas**:
   - Ingresa tu token de Discord
   - Selecciona modo de logs (detailed/minimal)
   - El instalador creará automáticamente el entorno virtual e instalará dependencias

4. **Iniciar el bot**:
   ```bash
   # En Windows:
   .venv\Scripts\python bot.py
   
   # En Linux/Mac:
   .venv/bin/python bot.py
   ```

### Método 2: Instalación Manual

1. **Crear entorno virtual**:
   ```bash
   python -m venv .venv
   ```

2. **Activar entorno virtual**:
   ```bash
   # Windows:
   .venv\Scripts\activate
   
   # Linux/Mac:
   source .venv/bin/activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install colorama python-dotenv discord.py yt-dlp
   ```

4. **Configurar variables de entorno**:
   - Copia `.env.example` a `.env` (o usa el proporcionado)
   - Edita `.env` y añade tu token de Discord:
   ```env
   DISCORD_TOKEN=TU_TOKEN_AQUI
   SERVE_MODE=http
   SERVE_PORT=auto
   ```

5. **Configurar logs** (opcional):
   Edita `config.json`:
   ```json
   {
     "log_mode": "detailed"
   }
   ```

6. **Iniciar el bot**:
   ```bash
   python bot.py
   ```

### Obtener Token de Discord

1. Ve a [Discord Developer Portal](https://discord.com/developers/applications)
2. Crea una nueva aplicación
3. Ve a la sección "Bot" y crea un bot
4. Copia el token (¡no lo compartas!)
5. Invita el bot a tu servidor usando OAuth2 → URL Generator
   - Selecciona scope: `bot`
   - Permisos necesarios: `Send Messages`, `Attach Files`, `Read Message History`


## ⚙️ Configuración Manual

### .env
```env
DISCORD_TOKEN=TU_TOKEN_AQUI
SERVE_MODE=http
SERVE_PORT=auto  # o número específico (8000-8999)
```

### config.json
```json
{
  "log_mode": "detailed"  // "detailed" o "minimal"
}
```

## 📋 Comportamiento

### Activación
- Solo responde a mensajes con enlaces `http://` o `https://`
- No usa comandos
- Procesa solo el primer enlace del mensaje
- Ignora mensajes de bots

### Descarga
- Timeout: 300 segundos (5 minutos)
- Si excede timeout → **ERROR 101**
- Si falla descarga → **ERROR 102**

### Envío
- **≤ 15MB**: Enviado como adjunto
  - Mensaje: `✅ Listo — aquí tienes tu archivo.`
  - Archivo se borra inmediatamente

- **> 15MB**: Publicado online
  - Mensaje: `✅ Archivo demasiado grande para adjuntar. 🔗 Enlace temporal (expira en 1 hora): <url>`
  - Servidor HTTP en puerto aleatorio (8000-8999)
  - Archivo disponible por 3600 segundos (1 hora)
  - Se elimina automáticamente después

## 🚨 Códigos de Error

| Código | Descripción |
|--------|-------------|
| ERROR 100 | Bot ocupado (no se notifica) |
| ERROR 101 | Timeout > 5 minutos |
| ERROR 102 | Fallo en descarga (enlace inválido/protegido) |
| ERROR 103 | Fallo al publicar online |
| ERROR 110 | Error interno |

## 🔒 Seguridad

- 1 descarga simultánea (asyncio.Lock)
- Sin cola de espera
- Timeout forzado
- Archivos temporales auto-eliminados
- Sin historial de descargas

## 📝 Requisitos

- Python 3.8+
- Discord Bot Token
- yt-dlp (instalado automáticamente)
- Puerto abierto (para modo online, sin CG-NAT)

## 🎮 Uso

1. Invita el bot a tu servidor o escríbele por DM
2. Envía cualquier mensaje con un enlace a video
3. El bot detecta, descarga y envía automáticamente

## 🛠️ Dependencias

- `discord.py` - Cliente Discord
- `yt-dlp` - Descarga de videos
- `python-dotenv` - Variables de entorno
- `colorama` - Colores en terminal

## 📜 Licencia

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE).

Copyright (c) 2025 litelis

El software se proporciona "tal cual", sin garantía de ningún tipo. Consulta el archivo LICENSE para más detalles.
