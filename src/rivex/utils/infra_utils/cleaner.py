import os
import shutil
from pathlib import Path

def nuke_zombies():
    root = Path('.')
    print(f"💀 Iniciando varredura em: {root.absolute()}")
    
    # Lista de extensões/nomes para matar
    targets = ['*.egg-info', 'build', 'dist']
    found_any = False

    # Varre tudo (equivalente ao recursivo)
    for target in targets:
        for path in root.rglob(target):
            # Protege seu ambiente virtual (não queremos deletar o pip de novo)
            if '.venv' in str(path).split(os.sep):
                continue
            
            if path.exists():
                print(f"   🚩 ALVO ENCONTRADO: {path}")
                try:
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    print("      🔥 DESTRUÍDO com sucesso.")
                    found_any = True
                except Exception as e:
                    print(f"      ❌ ERRO ao tentar deletar: {e}")

    if not found_any:
        print("\n✨ Nenhuma sujeira encontrada. O problema pode ser a configuração gerando duplicatas em tempo real.")
    else:
        print("\n✅ Limpeza concluída. Tente instalar agora.")

if __name__ == "__main__":
    nuke_zombies()