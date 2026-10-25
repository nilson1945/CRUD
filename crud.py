#estudo para CRUD

import sqlite3
import sys

DB_NAME = "dimensao_logus_interno.db"

# Lista completa com 20 Cursos Técnicos
CURSOS_TECNICOS = [
    "Enfermagem",
    "Radiologia",
    "Eletricista Predial",
    "Segurança do Trabalho",
    "Administração",
    "Informática para Internet",
    "Logística",
    "Contabilidade",
    "Edificações",
    "Recursos Humanos",
    "Eletrônica",
    "Mecânica Industrial",
    "Design de Interiores",
    "Estética e Cosmética",
    "Nutrição e Dietética",
    "Prótese Dentária",
    "Manutenção e Suporte em Informática",
    "Automação Industrial",
    "Agroindústria",
    "Energias Renováveis",
]


def inicializar_banco():
  """Inicializa o banco de dados SQLite com tratamento de erros."""
  try:
    with sqlite3.connect(DB_NAME) as conexao:
      cursor = conexao.cursor()
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS matriculas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_aluno TEXT NOT NULL,
                    rua TEXT NOT NULL,
                    bairro TEXT NOT NULL,
                    cidade TEXT NOT NULL,
                    cep TEXT NOT NULL,
                    celular TEXT NOT NULL,
                    telefone_fixo TEXT,
                    tipo_curso TEXT NOT NULL,
                    opcao_escolhida TEXT NOT NULL,
                    funcionario_responsavel TEXT NOT NULL
                )
            """)
      conexao.commit()
  except sqlite3.Error as e:
    print(f"\n[ERRO CRÍTICO] Falha ao conectar ou criar o banco de dados: {e}")
    sys.exit(1)


def limpar_tela():
  print("\n" + "=" * 60 + "\n")


def cadastrar_aluno(funcionario):
  """Função para o funcionário realizar o cadastro do aluno."""
  limpar_tela()
  print("--- NOVO CADASTRO DE ALUNO / MATRÍCULA ---")

  try:
    # Dados Pessoais
    nome = input("Nome completo do aluno: ").strip()
    if not nome:
      print("\n[ERRO] O nome do aluno não pode estar vazio.")
      return

    # Endereço
    print("\n--- Endereço ---")
    rua = input("Rua e Número: ").strip()
    bairro = input("Bairro: ").strip()
    cidade = input("Cidade: ").strip()
    cep = input("CEP (ex: 87000-000): ").strip()

    if not all([rua, bairro, cidade, cep]):
      print(
          "\n[ERRO] Todos os campos de endereço são obrigatórios para a"
          " empresa."
      )
      return

    # Contato
    print("\n--- Contato ---")
    celular = input("Celular (com DDD e WhatsApp): ").strip()
    telefone_fixo = input("Telefone Fixo (opcional, pressione Enter): ").strip()

    if not celular:
      print("\n[ERRO] O número de celular é obrigatório.")
      return

    # Tipo de Oferta (Técnico ou Vestibular)
    limpar_tela()
    print("Selecione a modalidade principal:")
    print("1 - Curso Técnico (Escolher entre 20 opções)")
    print("2 - Preparatório para Vestibular (Extensivo ou Semi-extensivo)")
    print("3 - Ambos / Misto")

    escolha_modalidade = input("Digite o número da opção desejada: ").strip()

    tipo_curso = ""
    opcao_escolhida = ""

    if escolha_modalidade == "1":
      tipo_curso = "Curso Técnico"
      limpar_tela()
      print("--- ESCOLHA O CURSO TÉCNICO ---")
      for i, curso in enumerate(CURSOS_TECNICOS, 1):
        print(f"{i:2d} - {curso}")

      while True:
        try:
          idx = int(
              input(
                  f"\nDigite o número do curso (1 a {len(CURSOS_TECNICOS)}): "
              )
          )
          if 1 <= idx <= len(CURSOS_TECNICOS):
            opcao_escolhida = CURSOS_TECNICOS[idx - 1]
            break
          else:
            print("[ATENÇÃO] Número inválido. Escolha entre 1 e 20.")
        except ValueError:
          print("[ATENÇÃO] Digite apenas números válidos.")

    elif escolha_modalidade == "2":
      tipo_curso = "Preparatório Vestibular"
      limpar_tela()
      print("--- ESCOLHA A MODALIDADE DO VESTIBULAR ---")
      print("1 - Extensivo")
      print("2 - Semi-extensivo")

      vest_op = input("Digite o número da opção (1 ou 2): ").strip()
      if vest_op == "1":
        opcao_escolhida = "Vestibular Extensivo"
      elif vest_op == "2":
        opcao_escolhida = "Vestibular Semi-extensivo"
      else:
        print("[ERRO] Opção de vestibular inválida.")
        return

    elif escolha_modalidade == "3":
      tipo_curso = "Misto (Técnico + Vestibular)"
      # Simplificando para o exemplo combinando um técnico e o semi/extensivo
      print("\n(Para cadastro misto, selecione o Curso Técnico abaixo):")
      for i, curso in enumerate(CURSOS_TECNICOS, 1):
        print(f"{i:2d} - {curso}")
      idx = int(input("Número do curso técnico: "))
      tec = CURSOS_TECNICOS[idx - 1]

      print("\nQual modalidade de vestibular?")
      print("1 - Extensivo | 2 - Semi-extensivo")
      vest_op = input("Opção (1/2): ")
      vest = "Extensivo" if vest_op == "1" else "Semi-extensivo"

      opcao_escolhida = f"Técnico: {tec} + Vestibular: {vest}"
    else:
      print("[ERRO] Opção inválida.")
      return

    # Salvando no Banco de Dados
    with sqlite3.connect(DB_NAME) as conexao:
      cursor = conexao.cursor()
      cursor.execute(
          """
                INSERT INTO matriculas (
                    nome_aluno, rua, bairro, cidade, cep, celular, 
                    telefone_fixo, tipo_curso, opcao_escolhida, funcionario_responsavel
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
          (
              nome,
              rua,
              bairro,
              cidade,
              cep,
              celular,
              telefone_fixo if telefone_fixo else "Não informado",
              tipo_curso,
              opcao_escolhida,
              funcionario,
          ),
      )
      conexao.commit()

    print(
        "\n[SUCESSO] Matrícula realizada e salva no banco de dados da"
        f" empresa por {funcionario}!"
    )

  except sqlite3.Error as e:
    print(f"\n[ERRO NO BANCO DE DADOS] Não foi possível salvar o registro: {e}")
  except Exception as e:
    print(f"\n[ERRO INESPERADO]: {e}")


def listar_matriculas():
  """Lista todas as matrículas cadastradas para controle interno."""
  limpar_tela()
  print("--- RELATÓRIO DE MATRÍCULAS REGISTRADAS ---")

  try:
    with sqlite3.connect(DB_NAME) as conexao:
      conexao.row_factory = sqlite3.Row
      cursor = conexao.cursor()
      cursor.execute("SELECT * FROM matriculas")
      registros = cursor.fetchall()

      if not registros:
        print("\nNenhuma matrícula encontrada no sistema.")
        return

      for reg in registros:
        print(f"\nID: {reg['id']} | Aluno: {reg['nome_aluno']}")
        print(
            f"Endereço: {reg['rua']}, {reg['bairro']} - {reg['cidade']} (CEP:"
            f" {reg['cep']})"
        )
        print(f"Contatos -> Celular: {reg['celular']} | Fixo: {reg['telefone_fixo']}")
        print(f"Modalidade: {reg['tipo_curso']} -> {reg['opcao_escolhida']}")
        print(f"Atendente Responsável: {reg['funcionario_responsavel']}")
        print("-" * 50)

  except sqlite3.Error as e:
    print(f"\n[ERRO] Falha ao consultar o banco de dados: {e}")


def main():
  inicializar_banco()

  limpar_tela()
  print("=== SISTEMA INTERNO - DIMENSÃO DO LOGUS ===")
  funcionario = input(
      "Identifique-se (Nome do Funcionário/Atendente): "
  ).strip()

  if not funcionario:
    funcionario = "Atendente Padrão"

  while True:
    print(f"\nBem-vindo(a), {funcionario}!")
    print("1 - Cadastrar Novo Aluno (Matrícula)")
    print("2 - Listar Alunos Matriculados")
    print("3 - Sair do Sistema")

    opcao = input("\nEscolha uma opção: ").strip()

    if opcao == "1":
      cadastrar_aluno(funcionario)
    elif opcao == "2":
      listar_matriculas()
      input("\nPressione Enter para voltar ao menu...")
    elif opcao == "3":
      print("\nEncerrando o sistema. Bom trabalho!")
      break
    else:
      print("\n[ERRO] Opção inválida, escolha entre 1, 2 ou 3.")


if __name__ == "__main__":
  main()