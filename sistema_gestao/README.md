# Sistema de Gestão Empresarial — Dimensão do Logus

Aplicação em Python para administrar funcionários, clientes, cursos técnicos e preparatórios, matrículas, mensalidades, lembretes e relatórios. A interface é gráfica (CustomTkinter), o banco é SQLite local e os dados permanecem após fechar o programa.

O projeto original em console (`crud.py` na raiz e `lembretes/lembretes.py`) foi preservado. Os cadastros e matrículas existentes foram importados na primeira execução.

## Instalação

Use Python 3.10 ou superior.

```text
cd sistema_gestao
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Na raiz do projeto (`H:\Desktop\CRUD`) também é possível:

```text
pip install -r sistema_gestao\requirements.txt
```

## Execução

Interface gráfica (recomendado):

```text
python main.py
```

ou, a partir da pasta `sistema_gestao`:

```text
python main.py
```

Modo console de matrículas (fluxo antigo, agora no banco unificado):

```text
python sistema_gestao\CRUD.py
```

## Acesso inicial

Na primeira execução, a tela de abertura permite criar o seu usuário de acesso ao sistema:

1. Clique em **Novo cadastro**.
2. Informe o nome completo, o **usuário** e a **senha** (mínimo 8 caracteres).
3. Depois do cadastro, entre com o usuário e a senha criados.

Esse primeiro usuário é criado como administrador. Os demais usuários são cadastrados pelo administrador em **Funcionários**.

Os dados da empresa (nome, CNPJ, telefone, e-mail, endereço, cidade e UF) são preenchidos dentro do programa, em **Configurações → Cadastro da empresa**.

Se preferir, ainda existe a conta padrão de instalação:

| Campo | Valor |
|---|---|
| Usuário | `admin` |
| Senha provisória | `Lg#2026Adm!` |

Altere essa senha no primeiro acesso. O sistema solicita a troca automaticamente. Não compartilhe a senha provisória após a instalação.

Colaboradores importados do arquivo `colaboradores.txt` entram com o primeiro nome (em minúsculas). Exemplo: **Arby du caste** → usuário `arby.caste`, senha original do arquivo (provisória; deve ser trocada). Atendentes criados a partir de matrículas antigas recebem senha provisória `Alterar@123`.

## O que o sistema faz

- **Dashboard:** totais de funcionários, clientes, matrículas, cursos, pendências e lembretes, com gráficos.
- **Funcionários:** CRUD, pesquisa, inativação e perfis (administrador / funcionário). Só o administrador cadastra e exclui.
- **Clientes:** cadastro completo, CPF único, histórico de matrículas, pagamentos e lembretes.
- **Cursos:** 20 cursos técnicos e 6 modalidades de vestibular já cadastrados, com faixa de referência e valor de venda editável.
- **Matrículas:** cliente + um ou mais cursos (uma matrícula por vez), valor negociado congelado, parcelas geradas na inclusão.
- **Financeiro:** parcelas, pagamentos parciais, juros, multa, desconto, atrasos. Parcelas canceladas deixam de ser cobradas, mas os valores já recebidos continuam contando como receita.
- **Lembretes:** compromissos, cobranças, reuniões e vínculos com cliente, funcionário ou matrícula, com avisos na entrada.
- **Relatórios:** filtros de período e exportação para Excel e PDF.
- **Configurações:** cadastro da empresa, troca de senha, backup e restauração do banco, histórico de ações.

## Banco de dados

Arquivo: `sistema_gestao/data/sistema_gestao.db`

Backups: `sistema_gestao/backups/`

Na primeira execução o sistema cria as tabelas, cadastra os cursos, cria o administrador e importa:

- matrícula de **Aldecio Lorival** (curso de Manutenção e Suporte em Informática, atendente Andre Medeiros);
- colaborador **Arby du caste**.

O arquivo antigo `dimensao_logus_interno.db` não é apagado.

## Manual rápido

1. No primeiro acesso, cadastre a empresa e o usuário administrador; depois entre com esse usuário e senha.
2. Cadastre funcionários (somente administrador) e defina o perfil.
3. Cadastre clientes. Informe o CPF para evitar duplicidade.
4. Confira os valores de venda em **Cursos** (os valores da tabela são referência comercial).
5. Em **Matrículas**, escolha o cliente, o curso, o desconto e as parcelas.
6. Em **Financeiro**, registre pagamentos (inclusive parciais) e consulte atrasos.
7. Use **Lembretes** para retornos, cobranças e reuniões; o painel inicial destaca o dia e os atrasados.
8. Gere relatórios e exporte PDF/Excel quando precisar.
9. Faça backup em **Configurações** com frequência.

## Permissões

- **Administrador:** todos os módulos, inclusive cadastro e exclusão de funcionários.
- **Funcionário:** dashboard, clientes, cursos, matrículas, financeiro, lembretes e relatórios.

## Testes

```text
cd sistema_gestao
python tests\test_core.py
```
