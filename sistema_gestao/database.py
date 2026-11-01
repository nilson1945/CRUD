"""
Camada de banco SQLite: criação, versão de schema, seed de cursos,
migração dos dados do sistema antigo e backup.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

if getattr(sys, "frozen", False):
    # Empacotado (PyInstaller): dados ficam na pasta de instalação, ao lado do .exe
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"
DB_PATH = DATA_DIR / "sistema_gestao.db"
DB_LEGADO = BASE_DIR.parent / "dimensao_logus_interno.db"
COLAB_TXT = BASE_DIR.parent / "colaboradores.txt"
SCHEMA_VERSION = 1

CURSOS_TECNICOS = [
    ("Enfermagem", 250, 450, 12),
    ("Radiologia", 300, 500, 12),
    ("Eletricista Predial", 150, 350, 12),
    ("Segurança do Trabalho", 180, 350, 12),
    ("Administração", 150, 300, 12),
    ("Informática para Internet", 180, 350, 12),
    ("Logística", 150, 300, 12),
    ("Contabilidade", 150, 300, 12),
    ("Edificações", 200, 400, 12),
    ("Recursos Humanos", 150, 300, 12),
    ("Eletrônica", 200, 400, 12),
    ("Mecânica Industrial", 200, 450, 12),
    ("Design de Interiores", 200, 400, 12),
    ("Estética e Cosmética", 200, 450, 12),
    ("Nutrição e Dietética", 200, 400, 12),
    ("Prótese Dentária", 250, 500, 12),
    ("Manutenção e Suporte em Informática", 180, 350, 12),
    ("Automação Industrial", 250, 450, 12),
    ("Agroindústria", 180, 350, 12),
    ("Energias Renováveis", 200, 400, 12),
]

CURSOS_VESTIBULAR = [
    ("Extensivo — Noturno", "Noturno", 400, 600, 11),
    ("Extensivo — Vespertino", "Vespertino", 450, 650, 11),
    ("Extensivo — Matutino", "Matutino", 500, 700, 11),
    ("Semi-extensivo — Noturno", "Noturno", 350, 450, 6),
    ("Semi-extensivo — Vespertino", "Vespertino", 400, 500, 6),
    ("Semi-extensivo — Matutino", "Matutino", 450, 550, 6),
]

PERMISSOES_ADMIN = [
    "dashboard", "funcionarios", "clientes", "cursos", "matriculas",
    "financeiro", "lembretes", "relatorios", "configuracoes",
]
PERMISSOES_FUNCIONARIO = [
    "dashboard", "clientes", "cursos", "matriculas",
    "financeiro", "lembretes", "relatorios",
]


def _conectar_arquivo(caminho: Path) -> sqlite3.Connection:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(caminho))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    return con


def get_connection() -> sqlite3.Connection:
    return _conectar_arquivo(DB_PATH)


@contextmanager
def transacao() -> Iterator[sqlite3.Connection]:
    con = get_connection()
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def inicializar_banco() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "assets" / "icones").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "assets" / "imagens").mkdir(parents=True, exist_ok=True)

    with get_connection() as con:
        _criar_tabelas(con)
        _garantir_versao(con)
        _seed_cursos(con)
        _seed_admin(con)
        _migrar_legado(con)
        con.commit()


def _criar_tabelas(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_meta (
            chave TEXT PRIMARY KEY,
            valor TEXT
        );

        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE,
            rg TEXT,
            data_nascimento TEXT,
            telefone TEXT,
            email TEXT,
            endereco TEXT,
            cargo TEXT,
            data_admissao TEXT,
            salario REAL,
            senha_hash TEXT,
            tipo_usuario TEXT NOT NULL DEFAULT 'funcionario',
            situacao TEXT NOT NULL DEFAULT 'ativo',
            usuario TEXT UNIQUE,
            senha_provisoria INTEGER NOT NULL DEFAULT 0,
            permissoes TEXT,
            criado_em TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            funcionario_id INTEGER NOT NULL UNIQUE,
            usuario TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            tipo TEXT NOT NULL,
            ativo INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
        );

        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT,
            rg TEXT,
            data_nascimento TEXT,
            telefone TEXT,
            whatsapp TEXT,
            email TEXT,
            cep TEXT,
            endereco TEXT,
            numero TEXT,
            bairro TEXT,
            cidade TEXT,
            estado TEXT,
            data_cadastro TEXT NOT NULL,
            observacoes TEXT,
            situacao TEXT NOT NULL DEFAULT 'ativo',
            UNIQUE(cpf)
        );

        CREATE TABLE IF NOT EXISTS cursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            modalidade TEXT,
            valor_minimo REAL,
            valor_maximo REAL,
            valor_venda REAL NOT NULL,
            duracao_meses INTEGER,
            descricao TEXT,
            situacao TEXT NOT NULL DEFAULT 'ativo'
        );

        CREATE TABLE IF NOT EXISTS matriculas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_matricula TEXT NOT NULL UNIQUE,
            cliente_id INTEGER NOT NULL,
            curso_id INTEGER NOT NULL,
            data_matricula TEXT NOT NULL,
            data_inicio TEXT,
            data_termino TEXT,
            valor_original REAL NOT NULL,
            desconto REAL NOT NULL DEFAULT 0,
            valor_final REAL NOT NULL,
            qtd_parcelas INTEGER NOT NULL DEFAULT 1,
            valor_parcela REAL,
            dia_vencimento INTEGER,
            forma_pagamento TEXT,
            observacoes TEXT,
            situacao TEXT NOT NULL DEFAULT 'Ativa',
            funcionario_id INTEGER,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (curso_id) REFERENCES cursos(id),
            FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
        );

        CREATE TABLE IF NOT EXISTS parcelas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula_id INTEGER NOT NULL,
            numero INTEGER NOT NULL,
            valor REAL NOT NULL,
            data_vencimento TEXT NOT NULL,
            situacao TEXT NOT NULL DEFAULT 'pendente',
            juros REAL NOT NULL DEFAULT 0,
            multa REAL NOT NULL DEFAULT 0,
            desconto REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (matricula_id) REFERENCES matriculas(id)
        );

        CREATE TABLE IF NOT EXISTS pagamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            matricula_id INTEGER NOT NULL,
            parcela_id INTEGER NOT NULL,
            valor_pago REAL NOT NULL,
            data_pagamento TEXT NOT NULL,
            forma_pagamento TEXT NOT NULL,
            observacao TEXT,
            funcionario_id INTEGER,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (matricula_id) REFERENCES matriculas(id),
            FOREIGN KEY (parcela_id) REFERENCES parcelas(id),
            FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
        );

        CREATE TABLE IF NOT EXISTS lembretes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT,
            data TEXT NOT NULL,
            horario TEXT,
            prioridade TEXT NOT NULL DEFAULT 'Média',
            categoria TEXT NOT NULL DEFAULT 'Outros',
            funcionario_id INTEGER,
            cliente_id INTEGER,
            matricula_id INTEGER,
            concluido INTEGER NOT NULL DEFAULT 0,
            criado_em TEXT NOT NULL,
            FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (matricula_id) REFERENCES matriculas(id)
        );

        CREATE TABLE IF NOT EXISTS historico_acoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            acao TEXT NOT NULL,
            tabela TEXT,
            registro_id INTEGER,
            detalhes TEXT,
            data_hora TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES funcionarios(id)
        );

        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_clientes_nome ON clientes(nome);
        CREATE INDEX IF NOT EXISTS idx_clientes_telefone ON clientes(telefone);
        CREATE INDEX IF NOT EXISTS idx_matriculas_cliente ON matriculas(cliente_id);
        CREATE INDEX IF NOT EXISTS idx_parcelas_venc ON parcelas(data_vencimento, situacao);
        CREATE INDEX IF NOT EXISTS idx_lembretes_data ON lembretes(data, concluido);
        """
    )
    # CPF vazio não deve violar UNIQUE: índice parcial
    con.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_clientes_cpf_unico "
        "ON clientes(cpf) WHERE cpf IS NOT NULL AND cpf != ''"
    )


def _garantir_versao(con: sqlite3.Connection) -> None:
    atual = con.execute(
        "SELECT valor FROM schema_meta WHERE chave='versao'"
    ).fetchone()
    if not atual:
        con.execute(
            "INSERT INTO schema_meta(chave, valor) VALUES('versao', ?)",
            (str(SCHEMA_VERSION),),
        )
    if not con.execute(
        "SELECT 1 FROM configuracoes WHERE chave='nome_empresa'"
    ).fetchone():
        con.execute(
            "INSERT INTO configuracoes(chave, valor) VALUES(?, ?)",
            ("nome_empresa", "Dimensão do Logus"),
        )


def _seed_cursos(con: sqlite3.Connection) -> None:
    existentes = {
        r["nome"] for r in con.execute("SELECT nome FROM cursos")
    }
    for nome, vmin, vmax, dur in CURSOS_TECNICOS:
        if nome in existentes:
            continue
        venda = round((vmin + vmax) / 2, 2)
        con.execute(
            """
            INSERT INTO cursos (nome, categoria, modalidade, valor_minimo, valor_maximo,
                valor_venda, duracao_meses, descricao, situacao)
            VALUES (?, 'Curso Técnico', 'Presencial', ?, ?, ?, ?, ?, 'ativo')
            """,
            (
                nome, vmin, vmax, venda, dur,
                f"Curso técnico de {nome}. Valores de referência comercial "
                f"entre R$ {vmin:.0f} e R$ {vmax:.0f}.",
            ),
        )
    for nome, periodo, vmin, vmax, dur in CURSOS_VESTIBULAR:
        if nome in existentes:
            continue
        venda = round((vmin + vmax) / 2, 2)
        con.execute(
            """
            INSERT INTO cursos (nome, categoria, modalidade, valor_minimo, valor_maximo,
                valor_venda, duracao_meses, descricao, situacao)
            VALUES (?, 'Preparatório Vestibular', ?, ?, ?, ?, ?, ?, 'ativo')
            """,
            (
                nome, periodo, vmin, vmax, venda, dur,
                f"Preparatório {nome}. Duração de referência: {dur} meses.",
            ),
        )


def _seed_admin(con: sqlite3.Connection) -> None:
    if con.execute("SELECT 1 FROM funcionarios WHERE usuario='admin'").fetchone():
        return
    from autenticacao import hash_senha, SENHA_ADMIN_INICIAL

    agora = datetime.now().isoformat(timespec="seconds")
    senha = hash_senha(SENHA_ADMIN_INICIAL)
    cur = con.execute(
        """
        INSERT INTO funcionarios (
            nome, cpf, email, cargo, tipo_usuario, situacao, usuario,
            senha_hash, senha_provisoria, permissoes, data_admissao, criado_em
        ) VALUES (?, ?, ?, ?, 'administrador', 'ativo', 'admin', ?, 1, ?, ?, ?)
        """,
        (
            "Administrador do Sistema",
            None,
            "admin@dimensaologus.local",
            "Proprietário",
            senha,
            json.dumps(PERMISSOES_ADMIN),
            datetime.now().date().isoformat(),
            agora,
        ),
    )
    fid = cur.lastrowid
    con.execute(
        """
        INSERT INTO usuarios (funcionario_id, usuario, senha_hash, tipo, ativo)
        VALUES (?, 'admin', ?, 'administrador', 1)
        """,
        (fid, senha),
    )


def _migrar_legado(con: sqlite3.Connection) -> None:
    flag = con.execute(
        "SELECT valor FROM schema_meta WHERE chave='migracao_legado'"
    ).fetchone()
    if flag and flag["valor"] == "1":
        return

    from autenticacao import hash_senha

    agora = datetime.now().isoformat(timespec="seconds")
    hoje = datetime.now().date().isoformat()

    if COLAB_TXT.exists():
        for linha in COLAB_TXT.read_text(encoding="utf-8").splitlines():
            if "Nome:" not in linha:
                continue
            try:
                nome = linha.split("Nome:")[1].split("|")[0].strip()
                senha = linha.split("Senha:")[1].strip() if "Senha:" in linha else ""
            except IndexError:
                continue
            if not nome:
                continue
            usuario = _usuario_de_nome(nome)
            if con.execute(
                "SELECT 1 FROM funcionarios WHERE usuario=? OR nome=?",
                (usuario, nome),
            ).fetchone():
                continue
            sh = hash_senha(senha or "123456")
            cur = con.execute(
                """
                INSERT INTO funcionarios (
                    nome, cargo, tipo_usuario, situacao, usuario, senha_hash,
                    senha_provisoria, permissoes, data_admissao, criado_em
                ) VALUES (?, 'Colaborador', 'funcionario', 'ativo', ?, ?, 1, ?, ?, ?)
                """,
                (nome, usuario, sh, json.dumps(PERMISSOES_FUNCIONARIO), hoje, agora),
            )
            con.execute(
                """
                INSERT INTO usuarios (funcionario_id, usuario, senha_hash, tipo, ativo)
                VALUES (?, ?, ?, 'funcionario', 1)
                """,
                (cur.lastrowid, usuario, sh),
            )

    if DB_LEGADO.exists():
        legado = sqlite3.connect(str(DB_LEGADO))
        legado.row_factory = sqlite3.Row
        try:
            rows = legado.execute("SELECT * FROM matriculas").fetchall()
        except sqlite3.Error:
            rows = []
        legado.close()

        for reg in rows:
            nome_aluno = reg["nome_aluno"]
            cliente = con.execute(
                "SELECT id FROM clientes WHERE nome=? AND telefone=?",
                (nome_aluno, reg["celular"]),
            ).fetchone()
            if cliente:
                cid = cliente["id"]
            else:
                cur = con.execute(
                    """
                    INSERT INTO clientes (
                        nome, telefone, whatsapp, cep, endereco, bairro, cidade,
                        data_cadastro, observacoes, situacao
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ativo')
                    """,
                    (
                        nome_aluno,
                        reg["celular"],
                        reg["celular"],
                        reg["cep"],
                        reg["rua"],
                        reg["bairro"],
                        reg["cidade"],
                        hoje,
                        f"Migrado do sistema anterior. Fixo: {reg['telefone_fixo']}",
                    ),
                )
                cid = cur.lastrowid

            curso_id = _resolver_curso_legado(con, reg["tipo_curso"], reg["opcao_escolhida"])
            resp = reg["funcionario_responsavel"]
            func = con.execute(
                "SELECT id FROM funcionarios WHERE nome=?", (resp,)
            ).fetchone()
            if not func and resp:
                usuario = _usuario_de_nome(resp)
                sh = hash_senha("Alterar@123")
                cur = con.execute(
                    """
                    INSERT INTO funcionarios (
                        nome, cargo, tipo_usuario, situacao, usuario, senha_hash,
                        senha_provisoria, permissoes, data_admissao, criado_em
                    ) VALUES (?, 'Atendente', 'funcionario', 'ativo', ?, ?, 1, ?, ?, ?)
                    """,
                    (resp, usuario, sh, json.dumps(PERMISSOES_FUNCIONARIO), hoje, agora),
                )
                fid = cur.lastrowid
                con.execute(
                    """
                    INSERT INTO usuarios (funcionario_id, usuario, senha_hash, tipo, ativo)
                    VALUES (?, ?, ?, 'funcionario', 1)
                    """,
                    (fid, usuario, sh),
                )
            else:
                fid = func["id"] if func else None

            numero = f"MAT-LEG-{reg['id']:04d}"
            if con.execute(
                "SELECT 1 FROM matriculas WHERE numero_matricula=?", (numero,)
            ).fetchone():
                continue
            curso_row = con.execute(
                "SELECT valor_venda, duracao_meses FROM cursos WHERE id=?",
                (curso_id,),
            ).fetchone()
            valor = float(curso_row["valor_venda"]) if curso_row else 0
            con.execute(
                """
                INSERT INTO matriculas (
                    numero_matricula, cliente_id, curso_id, data_matricula,
                    valor_original, desconto, valor_final, qtd_parcelas,
                    valor_parcela, forma_pagamento, observacoes, situacao,
                    funcionario_id
                ) VALUES (?, ?, ?, ?, ?, 0, ?, 1, ?, 'Não informado', ?, 'Ativa', ?)
                """,
                (
                    numero, cid, curso_id, hoje, valor, valor, valor,
                    f"Migração: {reg['tipo_curso']} / {reg['opcao_escolhida']}",
                    fid,
                ),
            )

    con.execute(
        "INSERT OR REPLACE INTO schema_meta(chave, valor) VALUES('migracao_legado','1')"
    )


def _usuario_de_nome(nome: str) -> str:
    partes = "".join(ch if ch.isalnum() else " " for ch in nome.lower()).split()
    if not partes:
        return "user"
    base = partes[0]
    if len(partes) > 1:
        base = f"{partes[0]}.{partes[-1]}"
    return base[:40]


def _resolver_curso_legado(con: sqlite3.Connection, tipo: str, opcao: str) -> int:
    row = con.execute(
        "SELECT id FROM cursos WHERE nome LIKE ?", (f"%{opcao}%",)
    ).fetchone()
    if row:
        return row["id"]
    if "Extensivo" in opcao and "Semi" not in opcao:
        row = con.execute(
            "SELECT id FROM cursos WHERE nome LIKE 'Extensivo%' LIMIT 1"
        ).fetchone()
        if row:
            return row["id"]
    if "Semi" in opcao:
        row = con.execute(
            "SELECT id FROM cursos WHERE nome LIKE 'Semi-extensivo%' LIMIT 1"
        ).fetchone()
        if row:
            return row["id"]
    # curso extra para combinações mistas
    nome = opcao[:80] or tipo
    existente = con.execute(
        "SELECT id FROM cursos WHERE nome=?", (nome,)
    ).fetchone()
    if existente:
        return existente["id"]
    cur = con.execute(
        """
        INSERT INTO cursos (nome, categoria, modalidade, valor_minimo, valor_maximo,
            valor_venda, duracao_meses, descricao, situacao)
        VALUES (?, ?, 'Presencial', 0, 0, 0, 12, 'Importado do sistema anterior', 'ativo')
        """,
        (nome, tipo or "Outros"),
    )
    return cur.lastrowid


def registrar_acao(
    usuario_id: Optional[int],
    acao: str,
    tabela: Optional[str] = None,
    registro_id: Optional[int] = None,
    detalhes: str = "",
) -> None:
    with get_connection() as con:
        con.execute(
            """
            INSERT INTO historico_acoes (usuario_id, acao, tabela, registro_id, detalhes, data_hora)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                usuario_id, acao, tabela, registro_id, detalhes,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        con.commit()


def backup_banco(destino: Optional[Path] = None) -> Path:
    inicializar_banco()
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = destino or (BACKUP_DIR / f"backup_{stamp}.db")
    with get_connection() as con:
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    shutil.copy2(DB_PATH, destino)
    return destino


def restaurar_banco(origem: Path) -> None:
    if not origem.exists():
        raise FileNotFoundError("Arquivo de backup não encontrado.")
    backup_banco()  # salvaguarda antes de restaurar
    with get_connection() as con:
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    shutil.copy2(origem, DB_PATH)


def obter_config(chave: str, padrao: str = "") -> str:
    with get_connection() as con:
        row = con.execute(
            "SELECT valor FROM configuracoes WHERE chave=?", (chave,)
        ).fetchone()
        return row["valor"] if row else padrao


def salvar_config(chave: str, valor: str) -> None:
    with get_connection() as con:
        con.execute(
            "INSERT OR REPLACE INTO configuracoes(chave, valor) VALUES(?, ?)",
            (chave, valor),
        )
        con.commit()
