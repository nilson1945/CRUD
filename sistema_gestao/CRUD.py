"""
Fluxo original de matrícula (console), agora gravando no banco unificado.

Preserva o cadastro de alunos do arquivo crud.py da raiz do projeto:
identificação do atendente, dados do aluno, escolha de curso técnico
ou vestibular, e listagem das matrículas.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datetime import date

import clientes as mod_clientes
import cursos as mod_cursos
import database
import matriculas as mod_matriculas

CURSOS_TECNICOS = [n for n, *_ in database.CURSOS_TECNICOS]


def limpar_tela():
    print("\n" + "=" * 60 + "\n")


def _sessao_funcionario(nome: str) -> dict:
    from database import get_connection

    with get_connection() as con:
        row = con.execute(
            "SELECT * FROM funcionarios WHERE nome LIKE ? AND situacao='ativo'",
            (f"%{nome}%",),
        ).fetchone()
        if row:
            return dict(row)
        admin = con.execute(
            "SELECT * FROM funcionarios WHERE usuario='admin'"
        ).fetchone()
        return dict(admin) if admin else {"id": 1, "tipo_usuario": "administrador", "nome": nome}


def cadastrar_aluno(funcionario: str) -> None:
    limpar_tela()
    print("--- NOVO CADASTRO DE ALUNO / MATRÍCULA ---")
    nome = input("Nome completo do aluno: ").strip()
    if not nome:
        print("\n[ERRO] O nome do aluno não pode estar vazio.")
        return
    print("\n--- Endereço ---")
    rua = input("Rua e Número: ").strip()
    bairro = input("Bairro: ").strip()
    cidade = input("Cidade: ").strip()
    cep = input("CEP (ex: 87000-000): ").strip()
    if not all([rua, bairro, cidade, cep]):
        print("\n[ERRO] Todos os campos de endereço são obrigatórios.")
        return
    print("\n--- Contato ---")
    celular = input("Celular (com DDD e WhatsApp): ").strip()
    telefone_fixo = input("Telefone Fixo (opcional, pressione Enter): ").strip()
    if not celular:
        print("\n[ERRO] O número de celular é obrigatório.")
        return

    limpar_tela()
    print("Selecione a modalidade principal:")
    print("1 - Curso Técnico")
    print("2 - Preparatório para Vestibular")
    escolha = input("Digite o número da opção desejada: ").strip()
    lista = mod_cursos.listar(apenas_ativos=True)
    if escolha == "1":
        tecnicos = [c for c in lista if c["categoria"] == "Curso Técnico"]
        for i, c in enumerate(tecnicos, 1):
            print(f"{i:2d} - {c['nome']}")
        idx = int(input(f"\nDigite o número do curso (1 a {len(tecnicos)}): "))
        curso = tecnicos[idx - 1]
    elif escolha == "2":
        vest = [c for c in lista if "Vestibular" in c["categoria"]]
        for i, c in enumerate(vest, 1):
            print(f"{i:2d} - {c['nome']}")
        idx = int(input("Opção: "))
        curso = vest[idx - 1]
    else:
        print("[ERRO] Opção inválida.")
        return

    sessao = _sessao_funcionario(funcionario)
    cid = mod_clientes.salvar(
        {
            "nome": nome,
            "telefone": celular,
            "whatsapp": celular,
            "cep": cep,
            "endereco": rua,
            "bairro": bairro,
            "cidade": cidade,
            "observacoes": f"Fixo: {telefone_fixo or 'Não informado'}",
        },
        sessao,
    )
    mod_matriculas.salvar(
        {
            "cliente_id": cid,
            "curso_id": curso["id"],
            "data_matricula": date.today().isoformat(),
            "valor_original": curso["valor_venda"],
            "desconto": 0,
            "valor_final": curso["valor_venda"],
            "qtd_parcelas": curso["duracao_meses"] or 1,
            "dia_vencimento": 10,
            "forma_pagamento": "PIX",
            "situacao": "Ativa",
            "observacoes": f"Atendente: {funcionario}",
        },
        sessao,
    )
    print(f"\n[SUCESSO] Matrícula salva no sistema por {funcionario}!")


def listar_matriculas() -> None:
    limpar_tela()
    print("--- RELATÓRIO DE MATRÍCULAS REGISTRADAS ---")
    regs = mod_matriculas.listar()
    if not regs:
        print("\nNenhuma matrícula encontrada no sistema.")
        return
    for r in regs:
        print(f"\n{r['numero_matricula']} | Aluno: {r['cliente_nome']}")
        print(f"Curso: {r['curso_nome']} | Situação: {r['situacao']}")
        print("-" * 50)


def main() -> None:
    database.inicializar_banco()
    limpar_tela()
    print("=== SISTEMA INTERNO - DIMENSÃO DO LOGUS ===")
    print("(Modo console — a interface gráfica é iniciada por main.py)")
    funcionario = input("Identifique-se (Nome do Funcionário/Atendente): ").strip()
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
