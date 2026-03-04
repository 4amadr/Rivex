import os
import shutil

def limpar_sujeira():
    raiz = os.getcwd()
    print(f"Iniciando varredura em: {raiz}")
    encontrou = False
    
    # Percorre todas as pastas e subpastas
    for root, dirs, files in os.walk(raiz):
        # Filtra pastas para remover (modificando a lista in-place)
        pastas_para_remover = [d for d in dirs if d.endswith(".egg-info") or d == "build" or d == "dist"]
        
        for d in pastas_para_remover:
            caminho_completo = os.path.join(root, d)
            print(f"ALVO LOCALIZADO: {caminho_completo}")
            try:
                shutil.rmtree(caminho_completo)
                print(f" -> DESTRUÍDO: {d}")
                encontrou = True
            except Exception as e:
                print(f" -> ERRO AO DESTRUIR: {e}")
                
            # Remove da lista de busca para não tentar entrar nela
            dirs.remove(d)

    if not encontrou:
        print("Nenhum alvo (.egg-info ou build) encontrado. O sistema está limpo?")
    else:
        print("Faxina concluída com sucesso.")

if __name__ == "__main__":
    limpar_sujeira()