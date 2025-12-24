
# Controle de Chamados • Engenharia (Pague Menos)

**App Streamlit** para visualização e análise dos chamados da Engenharia/Obras.

---

## 📚 Política de Governança de Dados

Esta política define como os dados do time de Engenharia/Obras devem ser 
organizados, versionados, atualizados e consumidos no app.

### 1) Escopo e fontes
- **Fonte primária**: planilha Excel mantida pelo time de Engenharia/Obras.
- **Abrangência**: chamados, fornecedores, coordenadores, projetos, valores e prazos.
- **Responsável pelo dado** (data owner): Engenharia/Obras.
- **Responsável pelo app**: Engenharia/Obras (Tiago F. de Oliveira).

### 2) Estrutura de arquivos (por ano)
- **Arquivo anual**: um arquivo por ano com o mesmo *schema* (mesma estrutura de colunas).
  - `BASE CONTROLE DE PAGAMENTOS_2025.xlsx` (snapshot histórico)
  - `BASE CONTROLE DE PAGAMENTOS_2026.xlsx` (arquivo corrente)
- **Arquivo corrente publicado no app**: usar um *alias* para simplificar o código.
  - `BASE CONTROLE DE PAGAMENTOS.xlsx` → **aponta sempre para o ano vigente** (ex.: 2026).
  - Ao virar o ano, substitua o alias pelo arquivo do novo ano.

### 3) Padrões de nome e colunas
- **Colunas obrigatórias** (schema mínimo):
  - `EMP, FILIAL, LOJA, CNPJ, COORDENADOR, PROJETO, SERVIÇO, NOTA, FORNECEDOR,
     VALOR RC, VALOR A PAGAR, VALOR BI, STATUS RC, PEDIDO, CHAMADO,
     DATA_PGTO_SAP, MIRO, STATUS RESULT1, DATA CRIAÇÃO TICKET,
     DATA CRIAÇÃO TICKET BR, DATA CRIAÇÃO RC, PRAZO`
- **Regra de cabeçalhos**: usar **UPPERCASE** sem espaços extras.
- **Categorias** (ex.: COORDENADOR, FORNECEDOR, PROJETO):
  - Normalização automática pelo app: *trim*, colapso de espaços e **UPPERCASE** (evita duplicidades por caixa).

### 4) Versionamento e snapshots
- **Snapshot anual**:
  - Ao encerrar o ano (ex.: 2025), gerar uma cópia congelada somente leitura: `BASE CONTROLE DE PAGAMENTOS_2025.xlsx`.
- **Controle de versões**:
  - Alterações relevantes (schema, novas colunas) devem ser registradas no **CHANGELOG** (ver seção 10).

### 5) Acesso e segurança
- **Repositório GitHub**: público para fins de compartilhamento do app, mas **sem dados sensíveis**.
- **Conteúdos sensíveis** (CPFs, dados bancários, etc.) **não devem** ser publicados.
- Para dados sensíveis e acesso corporativo (SharePoint/Graph API), use **Secrets** do Streamlit Cloud e permissões adequadas.

### 6) Backup e recuperação
- **Backup mensal** do arquivo corrente (ex.: `BASE CONTROLE DE PAGAMENTOS_2026_backup_YYYYMM.xlsx`).
- **Retenção mínima**: 12 meses.
- **Recuperação**: em caso de problema, substituir o alias `BASE CONTROLE DE PAGAMENTOS.xlsx` pelo último backup válido.

### 7) Qualidade dos dados
- **Checks antes de publicar**:
  - Cabeçalhos no padrão (UPPER e sem variações).
  - Datas válidas (campos de data reconhecidos).
  - Valores monetários numéricos (sem inflar vírgula/ponto).
  - Categorias normalizadas (evitar `Henrique` vs `HENRIQUE`).
- **Linhas lixo**: app remove linhas totalmente vazias nas colunas-chave.

### 8) Atualização de dados no app
- **Passo 1**: substituir `BASE CONTROLE DE PAGAMENTOS.xlsx` no repositório pelo arquivo atualizado (mesmo nome).
- **Passo 2**: o Streamlit Cloud detecta o commit e redeploya automaticamente.
- **Passo 3**: no app, clicar em **“🔄 Atualizar cache”** para recarregar os dados.

### 9) Virada de ano (2026)
- Criar o arquivo anual: `BASE CONTROLE DE PAGAMENTOS_2026.xlsx` seguindo o **mesmo schema**.
- Definir o **alias** para o ano corrente:
  - Substituir `BASE CONTROLE DE PAGAMENTOS.xlsx` → arquivo 2026.
- **Itens em aberto de 2025**:
  - Regra: se o evento relevante (abertura de ticket, MIRO ou pagamento) ocorrer em 2026, registrar na base 2026 mantendo o vínculo com o projeto original.
- **Análise multi-ano (opcional)**:
  - Consolidar anos (concatenação 2025+2026) em um arquivo auxiliar ou em uma rota do app para visão histórica.

### 10) CHANGELOG (exemplo)
- `2025-12-24` — Normalização automática de categorias (UPPER) no app; checkbox “Excluir nulos” inicia como **true**; coluna de referência padrão para MÊS prioriza **DATA CRIAÇÃO TICKET BR**.
- `2026-01-02` — Virada de ano: alias aponta para `BASE CONTROLE DE PAGAMENTOS_2026.xlsx`.

### 11) Critérios de governança
- **Consistência**: manter o mesmo schema entre anos; mudanças devem ser documentadas.
- **Completude**: evitar campos críticos em branco; usar os filtros de exigência do app para minimizar ruídos.
- **Rastreabilidade**: snapshots anuais e backups garantem histórico e auditoria.
- **Conformidade**: não publicar dados pessoais/sensíveis no repositório público.

---

## 🚀 Publicação e manutenção do app

### Deploy no Streamlit Cloud
1. Repositório com: `app_cloud_pretty.py`, `requirements.txt`, `BASE CONTROLE DE PAGAMENTOS.xlsx`.
2. Em **share.streamlit.io** → **New app** → selecionar repositório, branch `main`, arquivo principal `app_cloud_pretty.py`.
3. Deploy automático a cada commit.

### Atualização rápida
- Substitua a planilha (mesmo nome) → commit → aguarde o redeploy → no app clique **“🔄 Atualizar cache”**.

### Dependências
- `streamlit`, `pandas`, `openpyxl`, `xlrd`, `plotly`.

---

## 🧭 Convenções e dicas
- **Nomes**: usar UPPERCASE nas categorias; o app já normaliza, mas manter padrão ajuda.
- **Datas**: priorize `DATA CRIAÇÃO TICKET BR` para análises por mês.
- **Gráficos**: use o checkbox “Excluir nulos do gráfico (eixo)” — já marcado por padrão.
- **Filtros**: utilize a busca rápida do topo e a barra lateral (formulário).

---

## 📄 Licença e autoria
- Uso interno — Engenharia/Obras | Pague Menos.
- Autor: Tiago Felix de Oliveira — Analista Administrativo I.

