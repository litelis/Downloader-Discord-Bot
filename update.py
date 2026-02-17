#!/usr/bin/env python3
"""
Updater para Discord Video Bot
Compara versión local con remota y permite actualizar
"""

import subprocess
import sys
import os

def run_command(cmd, capture=True):
    """
    Ejecuta comando de shell y retorna resultado
    
    Args:
        cmd: Comando a ejecutar (lista o string)
        capture: Si capturar output
    Returns:
        (returncode, stdout, stderr)
    """
    try:
        if isinstance(cmd, str):
            cmd = cmd.split()
        
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def get_local_commit():
    """
    Obtiene el hash del commit local actual
    
    Returns:
        Hash del commit o None si hay error
    """
    code, stdout, stderr = run_command(["git", "rev-parse", "HEAD"])
    if code == 0:
        return stdout.strip()
    return None

def get_remote_commit():
    """
    Obtiene el hash del último commit en el remoto
    
    Returns:
        Hash del commit o None si hay error
    """
    # Fetch latest info from remote without merging
    code, _, stderr = run_command(["git", "fetch", "origin"])
    if code != 0:
        print(f"⚠️  Error al obtener información remota: {stderr}")
        return None
    
    # Get remote HEAD commit
    code, stdout, stderr = run_command(["git", "rev-parse", "origin/master"])
    if code == 0:
        return stdout.strip()
    
    # Try main branch if master doesn't exist
    code, stdout, stderr = run_command(["git", "rev-parse", "origin/main"])
    if code == 0:
        return stdout.strip()
    
    return None

def get_commit_info(commit_hash):
    """
    Obtiene información legible de un commit
    
    Args:
        commit_hash: Hash del commit
    Returns:
        String con info del commit
    """
    code, stdout, _ = run_command([
        "git", "log", "-1", "--pretty=format:%h - %s (%cr)", commit_hash
    ])
    if code == 0:
        return stdout.strip()
    return commit_hash[:7]

def check_updates():
    """
    Verifica si hay actualizaciones disponibles
    
    Returns:
        (needs_update: bool, local_commit: str, remote_commit: str)
    """
    print("🔍 Verificando actualizaciones...")
    
    # Verificar que estamos en un repositorio git
    code, _, _ = run_command(["git", "rev-parse", "--git-dir"])
    if code != 0:
        print("❌ Error: No se encuentra un repositorio git válido")
        return False, None, None
    
    local = get_local_commit()
    remote = get_remote_commit()
    
    if not local:
        print("❌ Error: No se pudo obtener la versión local")
        return False, None, None
    
    if not remote:
        print("❌ Error: No se pudo obtener la versión remota")
        return False, None, None
    
    print(f"📦 Versión local:  {get_commit_info(local)}")
    print(f"🌐 Versión remota: {get_commit_info(remote)}")
    
    needs_update = local != remote
    return needs_update, local, remote

def perform_update():
    """
    Realiza la actualización con git pull
    
    Returns:
        True si fue exitoso, False si falló
    """
    print("\n⬇️  Descargando actualización...")
    
    code, stdout, stderr = run_command(["git", "pull"])
    
    if code == 0:
        print("✅ Actualización completada exitosamente!")
        print("\n📝 Cambios aplicados:")
        print(stdout if stdout else "  (Sin cambios adicionales)")
        return True
    else:
        print(f"❌ Error al actualizar: {stderr}")
        print("\n💡 Puedes intentar manualmente con: git pull")
        return False

def main():
    """Función principal"""
    print("=" * 50)
    print("🔄 Discord Video Bot - Updater")
    print("=" * 50)
    
    # Verificar que git está instalado
    code, _, _ = run_command(["git", "--version"])
    if code != 0:
        print("❌ Error: Git no está instalado o no se encuentra en PATH")
        sys.exit(1)
    
    # Verificar actualizaciones
    needs_update, local, remote = check_updates()
    
    if not needs_update:
        print("\n✅ Ya tienes la última versión instalada.")
        print("👍 No hay actualizaciones disponibles.")
        sys.exit(0)
    
    # Hay actualización disponible
    print("\n⚠️  Hay una nueva versión disponible!")
    
    # Preguntar al usuario
    while True:
        try:
            response = input("\n🤔 ¿Deseas actualizar a la última versión? (y/n): ").strip().lower()
            
            if response in ['y', 'yes', 's', 'si', 'sí']:
                success = perform_update()
                if success:
                    print("\n🚀 ¡Listo! Reinicia el bot para aplicar los cambios.")
                    print("   Ejecuta: python bot.py")
                sys.exit(0 if success else 1)
            
            elif response in ['n', 'no']:
                print("\n⏭️  Actualización cancelada.")
                print("💡 Puedes actualizar manualmente más tarde con: git pull")
                sys.exit(0)
            
            else:
                print("⚠️  Por favor responde 'y' (sí) o 'n' (no)")
                
        except KeyboardInterrupt:
            print("\n\n👋 Cancelado por el usuario.")
            sys.exit(0)
        except EOFError:
            print("\n❌ Error de entrada. Cancelando.")
            sys.exit(1)

if __name__ == "__main__":
    main()
