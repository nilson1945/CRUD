"""Testes de persistência, validações, matrículas, financeiro e permissões."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import database

_TMP = Path(tempfile.mkdtemp(prefix="gestao_test_"))
database.DATA_DIR = _TMP
database.BACKUP_DIR = _TMP / "backups"
database.DB_PATH = _TMP / "teste.db"
database.DB_LEGADO = _TMP / "inexistente.db"
database.COLAB_TXT = _TMP / "inexistente.txt"

database.inicializar_banco()

import autenticacao
import clientes
import cursos
import financeiro
import funcionarios
import lembrete
import matriculas
from validacoes import validar_cpf, validar_email


def admin():
    u = autenticacao.autenticar("admin", autenticacao.SENHA_ADMIN_INICIAL)
    assert u, "Falha no login do administrador inicial"
    return u


class TestesNucleo(unittest.TestCase):
    def test_cursos_pre_cadastrados(self):
        lista = cursos.listar()
        self.assertGreaterEqual(len(lista), 26)

    def test_login_admin_e_hash(self):
        u = admin()
        self.assertEqual(u["tipo_usuario"], "administrador")
        self.assertNotEqual(u["senha_hash"], autenticacao.SENHA_ADMIN_INICIAL)
        self.assertTrue(u["senha_hash"].startswith("$2"))

    def test_cpf_e_email(self):
        self.assertTrue(validar_cpf("529.982.247-25"))
        self.assertFalse(validar_cpf("111.111.111-11"))
        self.assertTrue(validar_email("a@b.com"))
        self.assertFalse(validar_email("invalido"))

    def test_cliente_duplicado_cpf(self):
        u = admin()
        cpf = "529.982.247-25"
        clientes.salvar({"nome": "Cliente A", "cpf": cpf}, u)
        with self.assertRaises(ValueError):
            clientes.salvar({"nome": "Cliente B", "cpf": cpf}, u)

    def test_funcionario_nao_admin_nao_cadastra(self):
        u = admin()
        fid = funcionarios.salvar(
            {
                "nome": "Atendente Teste",
                "usuario": "atendente.teste",
                "senha": "SenhaForte1",
                "tipo_usuario": "funcionario",
            },
            u,
        )
        func = funcionarios.obter(fid)
        with self.assertRaises(PermissionError):
            funcionarios.salvar(
                {"nome": "Outro", "usuario": "outro", "senha": "SenhaForte1"},
                func,
            )

    def test_matricula_preserva_valor_e_parcelas(self):
        u = admin()
        cid = clientes.salvar({"nome": "Aluno Valor", "telefone": "44999990000"}, u)
        curso = cursos.listar(apenas_ativos=True)[0]
        original = float(curso["valor_venda"])
        mid = matriculas.salvar(
            {
                "cliente_id": cid,
                "curso_id": curso["id"],
                "valor_original": original,
                "desconto": 50,
                "valor_final": original - 50,
                "qtd_parcelas": 4,
                "dia_vencimento": 10,
                "forma_pagamento": "PIX",
                "data_inicio": date.today().isoformat(),
            },
            u,
        )
        cursos.salvar(
            {**curso, "valor_venda": original + 999},
            u,
        )
        mat = matriculas.obter(mid)
        self.assertEqual(mat["valor_original"], original)
        self.assertEqual(mat["valor_final"], original - 50)
        pars = [p for p in financeiro.listar_parcelas("todas") if p["matricula_id"] == mid]
        self.assertEqual(len(pars), 4)

    def test_pagamento_parcial_e_cancelamento(self):
        u = admin()
        cid = clientes.salvar({"nome": "Aluno Financeiro"}, u)
        curso = cursos.listar(apenas_ativos=True)[1]
        mid = matriculas.salvar(
            {
                "cliente_id": cid,
                "curso_id": curso["id"],
                "valor_original": 100,
                "desconto": 0,
                "valor_final": 100,
                "qtd_parcelas": 1,
                "dia_vencimento": 5,
                "forma_pagamento": "Dinheiro",
            },
            u,
        )
        pars = [p for p in financeiro.listar_parcelas("todas") if p["matricula_id"] == mid]
        pid = pars[0]["id"]
        financeiro.registrar_pagamento(pid, 40, "PIX", date.today().isoformat(), "parcial", u)
        p = financeiro.obter_parcela(pid)
        self.assertEqual(p["situacao"], "parcial")
        matriculas.cancelar(mid, u)
        ind = financeiro.indicadores()
        self.assertGreaterEqual(ind["total_pagamentos"], 40)

    def test_lembretes(self):
        u = admin()
        lid = lembrete.salvar(
            {
                "titulo": "Retornar cliente",
                "data": date.today().isoformat(),
                "horario": "10:00",
                "categoria": "Retorno de cliente",
                "prioridade": "Alta",
            },
            u,
        )
        hoje = lembrete.do_dia()
        self.assertTrue(any(x["id"] == lid for x in hoje))
        lembrete.concluir(lid, u)
        hoje = lembrete.do_dia()
        self.assertFalse(any(x["id"] == lid for x in hoje))

    def test_backup(self):
        path = database.backup_banco()
        self.assertTrue(path.exists())
        self.assertGreater(path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
