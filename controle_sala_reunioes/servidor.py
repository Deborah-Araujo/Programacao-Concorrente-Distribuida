# Importando bibliotecas do python
import socket
import threading as th

# Atribuindo valores de retorno das funções para variáveis
capacidade_sala = th.Semaphore(5)  # Criando o semáforo com limite 5
clientes_na_sala = set()  # Lista de nomes de clientes
conn_clientes_sala = []  # Lista de todos os conexoes com clientes
lock = th.Lock()  # Criando Lock

# Definindo função para lidar com requisições do cliente
def tratar_requisicoes(conn, addr):
    global clientes_na_sala # Globalizando variavel
    nome = conn.recv(1024).decode()
    print(f"{nome} conectado de {addr}")

    entrou_na_sala = False  # Flag de controle para saber se cliente está na sala

    while True:
        try:
            msg = conn.recv(1024).decode() # Recebe a requisição do cliente
            if not msg:
                break

            if msg == "/entrar": #comando especial para entrar na sala 
                with lock:
                    if nome in clientes_na_sala: # Verifica se o cliente já não está na sala
                        conn.sendall("Você já está na sala.".encode())
                        print(f"{nome} tentou entrar novamente, mas já está na sala.")

                    elif capacidade_sala.acquire(blocking=False):  # Junçao de acquire + blocking=False resulta entrar na hora caso tenha vaga ao invés de esperar 
                        clientes_na_sala.add(nome) # Adicionando nome à lista de clientes
                        conn_clientes_sala.append(conn) # Adiciona a conexao do cliente a lista de conexoes da sala
                        conn.sendall("Entrada permitida.".encode())
                        entrou_na_sala = True
                        mensagem = f"{nome} entrou na sala. Ocupação atual: {len(clientes_na_sala)}" # Avisa os demais participantes da reunião que um novo cliente entrou
                        print(mensagem)
                        enviar_mensagem_global(mensagem.encode(), conn)
                    else:
                        conn.sendall("Sala cheia. Tente novamente mais tarde.".encode())
                        print(f"{nome} tentou entrar, mas a sala está cheia.")

            elif msg == "/sair": #comando especial para entrar sair da sala
                with lock:
                    if nome in clientes_na_sala:
                        clientes_na_sala.remove(nome) # Remove o nome da lista de nome de clientes
                        capacidade_sala.release() # Libera o semáfaro
                        conn.sendall("Você saiu da sala".encode()) # Indica ao cliente para interromper a thread de recebimento

                        if conn in conn_clientes_sala: # Remove a conexao do cliente da sala
                            conn_clientes_sala.remove(conn)

                        mensagem = f"{nome} saiu da sala. Ocupação atual: {len(clientes_na_sala)}"
                        print(mensagem)
                        enviar_mensagem_global(mensagem.encode(), conn)
                        entrou_na_sala = False
                    else:
                        conn.sendall("Você não está na sala.".encode())

            elif msg == "/sair_do_sistema": #comando especial para sair do sistema 
                with lock:
                    if nome in clientes_na_sala: # Cerifica-se de que o cliente será realmente desconectado da sala
                        clientes_na_sala.remove(nome)
                        capacidade_sala.release()
                    if conn in conn_clientes_sala:
                        conn_clientes_sala.remove(conn)
                conn.sendall("Saída realizada com sucesso".encode())
                break

            else: # Se nenhuma das mensagens ao servidor for um comando, será uma mensagem do cliente aos outros participantes da sala
                if entrou_na_sala:
                    mensagem = f"[{nome}] {msg}"
                    enviar_mensagem_global(mensagem.encode(), conn)
                else:
                    conn.sendall("Você precisa entrar na sala para enviar mensagens.".encode())

        except Exception as e:
            print(f"A conexão com {nome} foi encerrada. Erro: {e}")
            break

    conn.close()
    print(f"{nome} desconectado.")
    with lock:
        if nome in clientes_na_sala: # Cerifica-se de que o cliente será realmente desconectado da sala
            clientes_na_sala.remove(nome)
            capacidade_sala.release()
        if conn in conn_clientes_sala:
            conn_clientes_sala.remove(conn)

# Função que envia mensagem para todos na sala de reuniao, com excecao de quem a enviou (para nao ocorrer duplicidades no chat)
def enviar_mensagem_global(mensagem, conn_origem):
    for conexao in list(conn_clientes_sala):
        if conexao != conn_origem:
            try:
                conexao.sendall(mensagem)
            except:
                conn_clientes_sala.remove(conexao)

# Função que inicializa o servidor
def iniciar_servidor():
    host = 'localhost'
    porta = 12345

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((host, porta))
    servidor.listen()

    print(f"Servidor rodando em {host}:{porta}...")

    while True:
        conn, addr = servidor.accept()

        # Cria a thread com a funcao que ficará tratando das requisicoes do usuario
        thread = th.Thread(target=tratar_requisicoes, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    iniciar_servidor()