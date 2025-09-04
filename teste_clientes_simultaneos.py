import socket
import threading
import time

def simular_cliente(nome):
    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect(('localhost', 12345))

        cliente.sendall(nome.encode())  # envia o nome

        time.sleep(0.1)
        cliente.sendall("entrar".encode())  # tenta entrar

        resposta = cliente.recv(1024).decode()
        print(f"{nome}: {resposta}")

        time.sleep(1)
        cliente.sendall("sair_do_sistema".encode())  # desconecta

        cliente.close()
    except Exception as e:
        print(f"Erro com {nome}: {e}")

def teste_concorrente():
    nomes = [f"Funcionario{i}" for i in range(1, 11)]  # 10 clientes
    threads = []

    for nome in nomes:
        t = threading.Thread(target=simular_cliente, args=(nome,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

if __name__ == "__main__":
    teste_concorrente()
