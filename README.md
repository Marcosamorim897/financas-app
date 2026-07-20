# 💰 Minhas Finanças

App de gestão financeira pessoal (PWA) com login, dashboard de receitas e gastos
mensais/anuais e controle de dívidas parceladas.

## Funcionalidades

- **Login e cadastro** de múltiplos usuários (cada um vê apenas seus dados)
- **Dashboard** com receitas, gastos e saldo do mês e do ano, gráfico de barras
  mensal (receitas × gastos) e parcelas do mês
- **Movimentações**: registro de receitas e gastos com categoria e data
- **Dívidas parceladas**: cadastro com valor total, número de parcelas e vencimento;
  as parcelas entram automaticamente nos gastos de cada mês; botão "Pagar parcela"
  acompanha o progresso
- **PWA**: instalável no celular (Android/iPhone), com ícone, tela cheia e
  página offline

## Rodar localmente

```bash
pip install -r requirements.txt
python app.py
```

Acesse http://localhost:5001. O banco local é SQLite (`instance/financas.db`),
criado automaticamente.

## Deploy no Render

1. Crie um repositório no GitHub e envie este projeto:
   ```bash
   git init
   git add .
   git commit -m "feat: app de gestão financeira (PWA)"
   git remote add origin https://github.com/SEU_USUARIO/financas-app.git
   git push -u origin main
   ```
2. No [Render](https://dashboard.render.com), clique em **New → Blueprint** e
   selecione o repositório. O arquivo `render.yaml` cria automaticamente:
   - o serviço web (gunicorn) com `SECRET_KEY` gerada
   - o banco PostgreSQL gratuito já conectado via `DATABASE_URL`
3. Aguarde o build. A URL final (ex: `https://financas-app.onrender.com`) já
   vem com HTTPS — requisito para instalar o PWA.

## Instalar no celular

- **Android (Chrome)**: abra a URL do app → menu ⋮ → **"Instalar aplicativo"**
  (ou aceite o banner de instalação).
- **iPhone (Safari)**: abra a URL → botão de compartilhar →
  **"Adicionar à Tela de Início"**.

O app abre em tela cheia, com ícone próprio, como um aplicativo nativo.

## Estrutura

```
financas-app/
├── app.py            # rotas Flask (auth, dashboard, transações, dívidas, PWA)
├── models.py         # Usuario, Transacao, Divida (SQLAlchemy)
├── gerar_icones.py   # gera os ícones PNG do PWA
├── render.yaml       # blueprint de deploy no Render
├── templates/        # páginas Jinja2
└── static/
    ├── css/style.css
    ├── js/grafico.js # gráfico de barras em canvas puro (sem dependências)
    ├── manifest.json # manifesto do PWA
    ├── sw.js         # service worker (cache + offline)
    └── icons/
```
