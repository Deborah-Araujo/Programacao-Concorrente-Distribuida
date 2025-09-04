# Importando bibliotecas do python
import socket
import threading as th

desconectado = False  # Flag global
chat_ativo = False    # Flag de chat

# A funcao receber ficará sempre esperando uma possível mensagem para lidar com ela (por isso ela ocorrerá em uma thread)
def receber(cliente):
    global chat_ativo
    while chat_ativo:
        # Tentativa de recebimento
        try:
            mensagem = cliente.recv(1024).decode()
            if not mensagem:
                break
            print(mensagem)
            if mensagem == "Saída realizada com sucesso":
                break
        # Exceção para desconexão da sala      
        except:
            print("Você se desconectou da sala de reunião.") 
            break

def iniciar_cliente():
    global desconectado, chat_ativo # Flags para controlar a thread de recebimento das mensagens (ela deve acontecer apenas quando o cliente estiver na sala)
    HOST = 'localhost'
    PORT = 12345

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((HOST, PORT)) # Realiza a conexao com o sevidor

    nome = input("\nDigite seu nome para entrar no sistema: ")
    cliente.sendall(nome.encode())

    # Menu principal do sistema
    while not desconectado:
        print("\n[1] - Entrar na sala")
        print("[2] - Sair do sistema")
        opcao = input("Escolha uma opção: ") # Opção aguarda input numérico

        # Caso opção escolhida seja 1 => Entra no sistema
        if opcao == '1':
            cliente.sendall("/entrar".encode())
            resposta = cliente.recv(1024).decode()
            print("Servidor:", resposta)

            if "permitida" in resposta:
                print("\nDigite '/sair' no chat para sair da sala de reunião ou /sair_do_sistema para fechar o programa\n")
                chat_ativo = True # Atualiza a flag para o status ativo no chat

                # Cria a thread da funcao receber para que ela possa rodar simultaneamente com a funcao de enviar mensagens
                thread_receber = th.Thread(target=receber, args=(cliente,), daemon=True)
                # Uso de daemon=True pois é o argumento que permite criação de thread sem necessitar do uso de .join(); 
                thread_receber.start()

                # Loop que espera o envio de mensagens ao servidor => podendo ser o comando /sair ou não
                # Se o usuario pede para sair, ele é retirado da sala, se nao, uma mensagem normal é enviada 
                while chat_ativo:
                    mensagem = input("")

                    if mensagem == "/sair":
                        cliente.sendall(mensagem.encode())
                        chat_ativo = False # Atualiza a flag para não ativo no chat
                        break
                    elif mensagem == "/sair_do_sistema":
                        cliente.sendall(mensagem.encode())

                        # Atualiza as flags para não ativo no chat e desconectado do servidor
                        chat_ativo = False
                        desconectado = True
                        return
                    else:
                        cliente.sendall(mensagem.encode())

                thread_receber.join() # Aguarda a thread acabar

        # Caso opção escolhida seja 2 => Sai do sistema e finaliza o programa
        elif opcao == '2':
            cliente.sendall("/sair_do_sistema".encode())
            resposta = cliente.recv(1024).decode()
            print("Servidor: ", resposta)
            desconectado = True # Atualiza a flag para o status de desconectado do servidor
            break

        else:
            print("Opção inválida")

    cliente.close() # Fecha a conexao

if __name__ == "__main__":
    print("\n\t + Bem-vinda ao Times sala de reunião e chat! +\n")
    iniciar_cliente()