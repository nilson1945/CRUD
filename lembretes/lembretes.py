def cadastrar_colaborador():
    print("\n--- Cadastro do colaborador ---")
    colaborador = input("Digite o nome do colaborador: ")

    while True:
        senha = input("Digite sua senha (apenas números): ")
        if senha.isdigit():
            break
        else:
            print("Erro: digite apenas números.")

    print("\nColaborador cadastrado com sucesso!")
    print(f"Nome: {colaborador}")

    with open("colaboradores.txt", "a", encoding="utf-8") as arquivo:
        arquivo.write(f"Nome: {colaborador} | Senha: {senha}\n")

    return colaborador, senha


def cadastrar_cliente():
    while True:
        print("\n--- Cadastro do cliente ---")

        nome = input("Digite o nome do cliente: ")
        rua = input("Digite o nome da rua: ")
        bairro = input("Digite o nome do bairro: ")

        while True:
            numero = input("Digite o número residencial: ")
            if numero.isdigit():
                numero_residencial = int(numero)
                break
            else:
                print("Erro: digite somente números.")

        cidade = input("Digite a cidade: ")
        telefone = input("Digite o telefone com DDD: ")

        print("\n--- Confira os dados do cliente ---")
        print(f"Nome: {nome}")
        print(f"Rua: {rua}")
        print(f"Bairro: {bairro}")
        print(f"Número: {numero_residencial}")
        print(f"Cidade: {cidade}")
        print(f"Telefone: {telefone}")

        while True:
            confirmacao = input(
                "\nOs dados estão corretos? (s/n): "
            ).strip().lower()

            if confirmacao == "s":
                print("\nDados confirmados com sucesso!")
                with open("clientes.txt", "a", encoding="utf-8") as arquivo:
                    arquivo.write(
                        f"Nome: {nome} | Endereço: {rua}, {numero_residencial}, {bairro} - {cidade} | Telefone: {telefone}\n"
                    )
                return

            elif confirmacao == "n":
                print("\nVamos refazer o cadastro.")
                break
            else:
                print("Resposta inválida. Digite s ou n.")


def cadastro():
    while True:
        print("\n==============================")
        print("     SISTEMA DE CADASTRO      ")
        print("==============================")
        print("1. Cadastrar Colaborador")
        print("2. Cadastrar Cliente")
        print("3. Sair")
        
        opcao = input("Escolha uma opção (1, 2 ou 3): ").strip()
        
        if opcao == "1":
            cadastrar_colaborador()
        elif opcao == "2":
            cadastrar_cliente()
        elif opcao == "3":
            print("\nSaindo do sistema. Até logo!")
            break
        else:
            print("\nOpção inválida! Escolha 1, 2 ou 3.")
            continue

        # Pergunta se o usuário deseja realizar um novo cadastro ou encerrar
        continuar = input("\nDeseja realizar um novo cadastro? (s/n): ").strip().lower()
        if continuar != "s":
            print("\nEncerrando o programa. Até logo!")
            break


# Inicia o programa
cadastro()