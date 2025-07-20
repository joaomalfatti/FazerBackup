import os
import shutil
import getpass
from datetime import datetime

def verificar_unidade_livre(drive_letter):
    """Verifica se a unidade está disponível para uso"""
    return not os.path.exists(drive_letter)

def encontrar_unidade_livre():
    """Encontra uma unidade disponível começando da Z: para trás"""
    for letra in range(90, 67, -1):  # De Z: até D:
        drive = f"{chr(letra)}:"
        if verificar_unidade_livre(drive):
            return drive
    return None

def mapear_unidade(host, usuario, senha):
    """Mapeia o disco C: do computador remoto usando uma unidade livre"""
    print(f"\n  Conectando ao computador {host}...")
    
    drive_letter = encontrar_unidade_livre()
    if not drive_letter:
        print("  Todas as unidades de rede estão em uso. Libere uma unidade e tente novamente.")
        return None
    
    comando = f'net use {drive_letter} \\\\{host}\\C$ {senha} /user:{usuario} /persistent:no'
    resultado = os.system(comando)

    os.system("cls")

    if resultado == 0:
        print(f"  Conexão estabelecida! (Unidade {drive_letter} mapeada para \\\\{host}\\C$)")
        return drive_letter
    
    print("\n  Falha na conexão. Verifique:")
    print(f"- Código do erro: {resultado}")
    print("- Credenciais incorretas ou sem privilégios")
    print("- Compartilhamento C$ não habilitado")
    return None

def listar_usuarios(drive_letter):
    """Lista usuários disponíveis para backup"""
    print("\n  Analisando usuários disponíveis...")
    users_path = os.path.join(drive_letter, 'Users')
    
    if not os.path.exists(users_path):
        print("  Pasta 'Users' não encontrada no computador remoto")
        return []
    
    usuarios = []
    pastas_ignoradas = ['Public', 'Default', 'All Users']
    
    for item in os.listdir(users_path):
        full_path = os.path.join(users_path, item)
        if item not in pastas_ignoradas and os.path.isdir(full_path):
            try:
                size = sum(f.stat().st_size for f in os.scandir(full_path) if f.is_file())
                usuarios.append({
                    'nome': item,
                    'tamanho': f"{size/(1024*1024):.2f} MB"
                })
            except:
                usuarios.append({'nome': item, 'tamanho': 'Tamanho não disponível'})
    
    if not usuarios:
        print("  Nenhum usuário encontrado (exceto pastas padrão)")
    else:
        print("\n  Usuários disponíveis para backup:")
        for i, user in enumerate(usuarios, 1):
            print(f" {i}. {user['nome']} ({user['tamanho']})")
    
    return usuarios

def calcular_tamanho_pasta(pasta):
    total_arquivos = 0
    total_tamanho = 0
    for root, dirs, files in os.walk(pasta):
        total_arquivos += len(files)
        for file in files:
            try:
                total_tamanho += os.path.getsize(os.path.join(root, file))
            except:
                continue
    return total_arquivos, total_tamanho

def mostrar_barra_progresso(progresso, total, tamanho_copiado, largura=40):
    
    percentual = progresso / total if total > 0 else 0
    barras_preenchidas = int(percentual * largura)
    barra = '█' * barras_preenchidas + '-' * (largura - barras_preenchidas)
    tamanho_mb = tamanho_copiado / (1024 * 1024)
    print(f"\r[{barra}] {percentual:.1%} | Arquivos: {progresso}/{total} | Tamanho: {tamanho_mb:.2f} MB", 
          end='', flush=True)
    if progresso == total:
        print()

def fazer_backup(origem, destino):
    """Executa o backup com feedback visual"""
    print(f"\n  Origem: {origem}")
    print(f"  Destino: {destino}\n")
    
    try:
        # Calcular total de arquivos
        print("  Calculando total de arquivos...")
        total_arquivos = calcular_tamanho_pasta(origem)
        
        if total_arquivos == 0:
            print("  Nenhum arquivo encontrado para backup!")
            return False
        
        print(f"  Total de arquivos a copiar: {total_arquivos}")
        
        # Criar estrutura de pastas
        os.makedirs(destino, exist_ok=True)
        
        # Contadores
        copiados = 0
        erros = 0
        
        print("\n ⏳ Iniciando backup...")
        mostrar_barra_progresso(0, total_arquivos)
        
        for root, dirs, files in os.walk(origem):
            rel_path = os.path.relpath(root, origem)
            dest_dir = os.path.join(destino, rel_path)
            
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            
            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dest_dir, file)
                
                try:
                    shutil.copy2(src_file, dst_file)
                    copiados += 1
                    if copiados % 100 == 0 or copiados == total_arquivos:
                        mostrar_barra_progresso(copiados, total_arquivos)
                except Exception as e:
                    erros += 1
                    continue
        
        # Resultado final
        print("\n" + "="*50)
        print("  RESUMO DO BACKUP")
        print("="*50)
        print(f"  Arquivos copiados com sucesso: {copiados}")
        print(f"  Arquivos com erro: {erros}")
        print(f"  Tamanho estimado: {os.path.getsize(origem)/(1024*1024):.2f} MB")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"\n  Erro crítico: {str(e)}")
        print(" Por favor, verifique as permissões e tente novamente.")
        return False

def main():
    os.system("cls")
    print("\n" + "="*50)
    print("=== BACKUP DE USUÁRIOS REMOTOS - v1.1 ===")
    print("="*50)
    
    # Configuração do usuário administrador
    host = ""
    while not host:
        host = input("\n  IP/nome do PC (ex: 10.150.7.123/DC01TIN04): ").strip()
    
    usuario = ""
    while not usuario:
        usuario = input("  Usuário administrador (ex: [USUARIO] ou [USUARIO]@dcoimbra.com.br): ").strip()
    
    senha = getpass.getpass("  Senha: ")
    
    # Conexão
    drive = mapear_unidade(host, usuario, senha)
    if not drive:
        return
    
    try:
        # Listar usuários
        usuarios = listar_usuarios(drive)
        if not usuarios:
            return
        
        # Seleção do usuário
        print("\n" + "-"*50)
        print(" Escolha o usuário para backup:")
        for i, user in enumerate(usuarios, 1):
            print(f" {i}. {user['nome']} ({user['tamanho']})")
        
        while True:
            try:
                opcao = int(input("\n  Digite o número do usuário para backup: "))
                if 1 <= opcao <= len(usuarios):
                    usuario_selecionado = usuarios[opcao-1]
                    break
                print("  Número inválido. Tente novamente.")
            except ValueError:
                print("  Por favor, digite um número válido.")
        
        # Destino do backup
        destino_base = input("\n  Digite a pasta local para salvar o backup (ex: C:\\Backups): ").strip()
        if not os.path.exists(destino_base):
            os.makedirs(destino_base)
        
        data_hora = datetime.now().strftime('%Y%m%d_%H%M%S')
        destino_final = os.path.join(destino_base, f"Backup_{usuario_selecionado['nome']}_{data_hora}")
        
        # Executar backup
        origem = os.path.join(drive, 'Users', usuario_selecionado['nome'])
        fazer_backup(origem, destino_final)
        
    finally:
        print("\n  Desconectando do computador remoto...")
        os.system(f'net use {drive} /delete >nul 2>&1')
        print("  Operação concluída!\n")

if __name__ == "__main__":
    main()