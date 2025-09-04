import threading as th # Criamos um 'apelido' para a biblioteca para facilitar a organização do código.
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from time import time

def buscar_palavra_no_site_paralelizada(url_inicial, palavra, profundidade_maxima=3):
    """
    Busca recursivamente uma palavra específica em todas as páginas de um site.

    Parâmetros:
        url_inicial (str): A URL inicial do site.
        palavra (str): A palavra a ser buscada.
        profundidade_maxima (int): A profundidade máxima de navegação (padrão: 3).

    Retorna:
        dict: Um dicionário onde as chaves são URLs e os valores indicam se a palavra foi encontrada.
    """
    # Estruturas para armazenar resultados e evitar loops
    urls_visitados = set()
    resultados = {}
    lock = th.Lock() # Criamos um lock para evitar problemas com threads compartilhando os mesmos recursos.
    threads = [] # Criamos um array que receberá todas as threads, para que seja possível dar join() em todas ao final.

    def buscar_recursivo(url_atual, profundidade_atual):
        # Verifica se atingimos a profundidade máxima ou já visitamos essa URL
        if profundidade_atual > profundidade_maxima or url_atual in urls_visitados:
            return
        
        with lock: # Usamos 'With lock' para travar e liberar a variável automáticamente e evitar DeadLocks. 
            urls_visitados.add(url_atual)

        try:
            # Faz a requisição HTTP
            print(f"Buscando em: {url_atual} (Profundidade: {profundidade_atual})")
            response = requests.get(url_atual, timeout=10)
            response.raise_for_status()  # Lança exceção para erros HTTP

            # Analisa o conteúdo HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Verifica se a palavra está no conteúdo da página
            conteudo = soup.get_text().lower()
            palavra_encontrada = palavra.lower() in conteudo

            with lock: # Novamente 'With lock' para evitar DeadLocks.
                resultados[url_atual] = palavra_encontrada

            # Extrai todos os links da página
            links = soup.find_all('a', href=True)
            for link in links:
                url_completa = urljoin(url_inicial, link['href'])

                # Garante que só navegamos dentro do mesmo domínio
                if url_completa.startswith(url_inicial):
                    thread = th.Thread(target=lambda: buscar_recursivo(url_completa, profundidade_atual + 1)) # Cria uma thread
                    threads.append(thread) # Adiciona no array
                    thread.start() # Dispara a thread

        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar {url_atual}: {e}")

    # Inicia a busca recursiva
    buscar_recursivo(url_inicial, profundidade_atual=1)

    # Join em todas as threads do array para que seja possível continuar o programa.
    for thread in threads:
        thread.join()

    return resultados

# OBSERVAÇÂO:
# Deixamos aqui a função original, sem a utilização de threads, para possibilitar a comparação de tempo gasto. 
def buscar_palavra_no_site(url_inicial, palavra, profundidade_maxima=3):
    # Estruturas para armazenar resultados e evitar loops
    urls_visitados = set()
    resultados = {}

    def buscar_recursivo(url_atual, profundidade_atual):
        # Verifica se atingimos a profundidade máxima ou já visitamos essa URL
        if profundidade_atual > profundidade_maxima or url_atual in urls_visitados:
            return
        
        urls_visitados.add(url_atual)

        try:
            # Faz a requisição HTTP
            print(f"Buscando em: {url_atual} (Profundidade: {profundidade_atual})")
            response = requests.get(url_atual, timeout=10)
            response.raise_for_status()  # Lança exceção para erros HTTP

            # Analisa o conteúdo HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Verifica se a palavra está no conteúdo da página
            conteudo = soup.get_text().lower()
            palavra_encontrada = palavra.lower() in conteudo
            resultados[url_atual] = palavra_encontrada

            # Extrai todos os links da página
            links = soup.find_all('a', href=True)
            for link in links:
                url_completa = urljoin(url_inicial, link['href'])

                # Garante que só navegamos dentro do mesmo domínio
                if url_completa.startswith(url_inicial):
                    buscar_recursivo(url_completa, profundidade_atual + 1)

        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar {url_atual}: {e}")

    # Inicia a busca recursiva
    buscar_recursivo(url_inicial, profundidade_atual=1)
    return resultados

# Exemplo de uso
if __name__ == "__main__":
    url_inicial = input("Digite a URL inicial do site (ex.: https://www.exemplo.com): ")
    palavra = input("Digite a palavra a ser buscada: ")

    print("\nIniciando busca paralela: \n")
    inicio = time() # Realizar a medida de tempo
    resultados = buscar_palavra_no_site_paralelizada(url_inicial, palavra)
    fim = time()
    tempo_gasto_com_threads = fim - inicio

    print("\nResultados da busca paralela:")
    for url, encontrada in resultados.items():
        status = "Encontrada" if encontrada else "Não encontrada"
        print(f"{url}: Palavra '{palavra}' {status}")

    # Realizamos a medida de tempo gasto
    print(f"\nTempo gasto na pesquisa paralela: {tempo_gasto_com_threads:.5f} segundos.\n")

    # OBSERVAÇÃO IMPORTANTE:

    # para realizar a comparação de tempo, basta descomentar o bloco de códico a seguir. No entanto, realizar as duas 
    # pesquisas levará algum tempo dependendo da quantidade de resultados. Por isso, optamos por deixar uma das chamadas
    # comentadas, mas a comparação pode ser realizada sem levar muito tempo se feita em sites que resultem em menos resultados. 
     
    # print("Iniciando busca sequencial: \n")
    # inicio = time() # Realizar a medida de tempo
    # resultados_sem_thread = buscar_palavra_no_site(url_inicial, palavra)
    # fim = time()
    # tempo_gasto_sem_threads = fim - inicio

    # print("\nResultado da busca sequencial:")
    # for url, encontrada in resultados_sem_thread.items():
    #     status = "Encontrada" if encontrada else "Não encontrada"
    #     print(f"{url}: Palavra '{palavra}' {status}")

    # print(f"\nTempo gasto na pesquisa SEM threads: {tempo_gasto_sem_threads:.5f} segundos.")
    # print(f"Tempo gasto na pesquisa COM threads:: {tempo_gasto_com_threads:.5f} segundos.\n")

    # print("Resultado do teste: ")
    # if tempo_gasto_com_threads < tempo_gasto_sem_threads:
    #     print(f"A execução paralela foi {(tempo_gasto_sem_threads - tempo_gasto_com_threads):.4f} segundos mais rápida.\n")
    # else:
    #     print(f"A execução sem threads foi {(tempo_gasto_com_threads - tempo_gasto_sem_threads):.4f} segundos mais rápida.\n")