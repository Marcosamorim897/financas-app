import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from models import Divida, Meta, MovimentoMeta, Transacao, Usuario, db

MESES_ABREV = [
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez",
]

CATEGORIAS_DESPESA = [
    "Alimentação", "Moradia", "Transporte", "Saúde", "Educação",
    "Lazer", "Assinaturas", "Vestuário", "Outros",
]
CATEGORIAS_RECEITA = ["Salário", "Freelance", "Investimentos", "Vendas", "Outros"]


def criar_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-chave-trocar-em-producao")

    database_url = os.environ.get("DATABASE_URL", "sqlite:///financas.db")
    # O Render fornece "postgres://", mas o SQLAlchemy exige "postgresql://"
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    with app.app_context():
        db.create_all()

    return app


app = criar_app()


# ---------------------------------------------------------------- helpers


def login_obrigatorio(f):
    @wraps(f)
    def decorada(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorada


def usuario_atual():
    return db.session.get(Usuario, session["user_id"])


def parse_valor(texto):
    """Aceita '1.234,56' ou '1234.56' e devolve Decimal positivo, ou None."""
    texto = (texto or "").strip()
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        valor = Decimal(texto).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None
    return valor if valor > 0 else None


def parse_data(texto):
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def resumo_periodo(usuario, ano, mes=None):
    """Totais de receitas e despesas (transações + parcelas de dívidas)."""
    receitas = Decimal("0")
    despesas = Decimal("0")
    for t in usuario.transacoes:
        if t.data.year != ano or (mes and t.data.month != mes):
            continue
        if t.tipo == "receita":
            receitas += Decimal(t.valor)
        else:
            despesas += Decimal(t.valor)

    parcelas = Decimal("0")
    meses = [mes] if mes else range(1, 13)
    for divida in usuario.dividas:
        for m in meses:
            parcelas += divida.parcela_no_mes(ano, m)

    return {
        "receitas": receitas,
        "despesas": despesas,
        "parcelas": parcelas,
        "despesas_total": despesas + parcelas,
        "saldo": receitas - despesas - parcelas,
    }


@app.template_filter("moeda")
def filtro_moeda(valor):
    """Formata Decimal como R$ 1.234,56."""
    valor = Decimal(valor or 0)
    inteiro, _, centavos = f"{valor:,.2f}".partition(".")
    inteiro = inteiro.replace(",", ".")
    return f"R$ {inteiro},{centavos}"


@app.template_filter("data_br")
def filtro_data_br(d):
    return d.strftime("%d/%m/%Y") if d else ""


# ---------------------------------------------------------------- PWA


@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json")


@app.route("/sw.js")
def service_worker():
    # Servido na raiz para que o escopo do service worker cubra o app inteiro
    resposta = send_from_directory("static", "sw.js")
    resposta.headers["Cache-Control"] = "no-cache"
    return resposta


@app.route("/offline")
def offline():
    return render_template("offline.html")


# ---------------------------------------------------------------- auth


@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not nome or not email or len(senha) < 6:
            flash("Preencha todos os campos (senha com no mínimo 6 caracteres).", "erro")
        elif Usuario.query.filter_by(email=email).first():
            flash("Este e-mail já está cadastrado.", "erro")
        else:
            usuario = Usuario(
                nome=nome, email=email, senha_hash=generate_password_hash(senha)
            )
            db.session.add(usuario)
            db.session.commit()
            session["user_id"] = usuario.id
            return redirect(url_for("dashboard"))

    return render_template("registrar.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.senha_hash, senha):
            session["user_id"] = usuario.id
            return redirect(url_for("dashboard"))
        flash("E-mail ou senha incorretos.", "erro")

    return render_template("login.html")


@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------- dashboard


@app.route("/")
@login_obrigatorio
def dashboard():
    usuario = usuario_atual()
    hoje = date.today()

    mes_atual = resumo_periodo(usuario, hoje.year, hoje.month)
    ano_atual = resumo_periodo(usuario, hoje.year)

    parcelas_mes = []
    for divida in usuario.dividas:
        valor = divida.parcela_no_mes(hoje.year, hoje.month)
        if valor > 0 and not divida.quitada:
            numero = divida.indice_parcela(hoje.year, hoje.month) + 1
            parcelas_mes.append({"divida": divida, "numero": numero, "valor": valor})

    ultimas = (
        Transacao.query.filter_by(user_id=usuario.id)
        .order_by(Transacao.data.desc(), Transacao.id.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard.html",
        usuario=usuario,
        hoje=hoje,
        nome_mes=MESES_ABREV[hoje.month - 1],
        mes=mes_atual,
        ano=ano_atual,
        parcelas_mes=parcelas_mes,
        ultimas=ultimas,
    )


@app.route("/api/grafico")
@login_obrigatorio
def api_grafico():
    usuario = usuario_atual()
    try:
        ano = int(request.args.get("ano", date.today().year))
    except ValueError:
        ano = date.today().year

    receitas = [0.0] * 12
    despesas = [0.0] * 12
    for t in usuario.transacoes:
        if t.data.year != ano:
            continue
        idx = t.data.month - 1
        if t.tipo == "receita":
            receitas[idx] += float(t.valor)
        else:
            despesas[idx] += float(t.valor)

    for divida in usuario.dividas:
        for m in range(1, 13):
            despesas[m - 1] += float(divida.parcela_no_mes(ano, m))

    return jsonify(
        {"ano": ano, "meses": MESES_ABREV, "receitas": receitas, "despesas": despesas}
    )


# ---------------------------------------------------------------- transações


@app.route("/transacoes", methods=["GET", "POST"])
@login_obrigatorio
def transacoes():
    usuario = usuario_atual()

    if request.method == "POST":
        tipo = request.form.get("tipo")
        descricao = request.form.get("descricao", "").strip()
        categoria = request.form.get("categoria", "Outros").strip() or "Outros"
        valor = parse_valor(request.form.get("valor"))
        data_mov = parse_data(request.form.get("data")) or date.today()

        if tipo not in ("receita", "despesa") or not descricao or valor is None:
            flash("Preencha descrição e um valor válido maior que zero.", "erro")
        else:
            db.session.add(
                Transacao(
                    user_id=usuario.id,
                    tipo=tipo,
                    descricao=descricao,
                    categoria=categoria,
                    valor=valor,
                    data=data_mov,
                )
            )
            db.session.commit()
            flash("Movimentação registrada!", "ok")
        return redirect(url_for("transacoes"))

    lista = (
        Transacao.query.filter_by(user_id=usuario.id)
        .order_by(Transacao.data.desc(), Transacao.id.desc())
        .all()
    )
    return render_template(
        "transacoes.html",
        usuario=usuario,
        transacoes=lista,
        hoje=date.today(),
        categorias_despesa=CATEGORIAS_DESPESA,
        categorias_receita=CATEGORIAS_RECEITA,
    )


@app.route("/transacoes/<int:transacao_id>/excluir", methods=["POST"])
@login_obrigatorio
def excluir_transacao(transacao_id):
    transacao = Transacao.query.filter_by(
        id=transacao_id, user_id=session["user_id"]
    ).first_or_404()
    db.session.delete(transacao)
    db.session.commit()
    flash("Movimentação excluída.", "ok")
    return redirect(url_for("transacoes"))


# ---------------------------------------------------------------- dívidas


@app.route("/dividas", methods=["GET", "POST"])
@login_obrigatorio
def dividas():
    usuario = usuario_atual()

    if request.method == "POST":
        descricao = request.form.get("descricao", "").strip()
        modo = request.form.get("modo_valor", "total")
        valor = parse_valor(request.form.get("valor"))
        data_inicio = parse_data(request.form.get("data_primeira_parcela"))
        try:
            num_parcelas = int(request.form.get("num_parcelas", "0"))
        except ValueError:
            num_parcelas = 0

        if not descricao or valor is None or num_parcelas < 1 or not data_inicio:
            flash("Preencha todos os campos da dívida corretamente.", "erro")
        else:
            if modo == "parcela":
                valor_total = (valor * num_parcelas).quantize(Decimal("0.01"))
            else:
                valor_total = valor
            db.session.add(
                Divida(
                    user_id=usuario.id,
                    descricao=descricao,
                    valor_total=valor_total,
                    num_parcelas=num_parcelas,
                    data_primeira_parcela=data_inicio,
                )
            )
            db.session.commit()
            flash("Dívida parcelada cadastrada!", "ok")
        return redirect(url_for("dividas"))

    lista = (
        Divida.query.filter_by(user_id=usuario.id)
        .order_by(Divida.data_primeira_parcela.desc())
        .all()
    )
    return render_template(
        "dividas.html", usuario=usuario, dividas=lista, hoje=date.today()
    )


@app.route("/dividas/<int:divida_id>/pagar", methods=["POST"])
@login_obrigatorio
def pagar_parcela(divida_id):
    divida = Divida.query.filter_by(
        id=divida_id, user_id=session["user_id"]
    ).first_or_404()
    if not divida.quitada:
        divida.parcelas_pagas += 1
        db.session.commit()
        if divida.quitada:
            flash(f'Dívida "{divida.descricao}" quitada! 🎉', "ok")
        else:
            flash("Parcela marcada como paga.", "ok")
    return redirect(url_for("dividas"))


@app.route("/dividas/<int:divida_id>/excluir", methods=["POST"])
@login_obrigatorio
def excluir_divida(divida_id):
    divida = Divida.query.filter_by(
        id=divida_id, user_id=session["user_id"]
    ).first_or_404()
    db.session.delete(divida)
    db.session.commit()
    flash("Dívida excluída.", "ok")
    return redirect(url_for("dividas"))


# ---------------------------------------------------------------- metas


@app.route("/metas", methods=["GET", "POST"])
@login_obrigatorio
def metas():
    usuario = usuario_atual()
    hoje = date.today()

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        valor_alvo = parse_valor(request.form.get("valor_alvo"))
        data_prevista = parse_data(request.form.get("data_prevista"))

        if not nome or valor_alvo is None or not data_prevista:
            flash("Preencha nome, valor e data de previsão corretamente.", "erro")
        elif data_prevista <= hoje:
            flash("A data de previsão precisa ser uma data futura.", "erro")
        else:
            db.session.add(
                Meta(
                    user_id=usuario.id,
                    nome=nome,
                    valor_alvo=valor_alvo,
                    data_prevista=data_prevista,
                )
            )
            db.session.commit()
            flash("Meta criada! Bora guardar dinheiro. 🎯", "ok")
        return redirect(url_for("metas"))

    lista = (
        Meta.query.filter_by(user_id=usuario.id)
        .order_by(Meta.data_prevista.asc())
        .all()
    )
    # metas em andamento primeiro, concluídas por último
    lista.sort(key=lambda m: m.concluida)
    return render_template("metas.html", usuario=usuario, metas=lista, hoje=hoje)


@app.route("/metas/<int:meta_id>/movimentar", methods=["POST"])
@login_obrigatorio
def movimentar_meta(meta_id):
    meta = Meta.query.filter_by(id=meta_id, user_id=session["user_id"]).first_or_404()
    tipo = request.form.get("tipo")
    valor = parse_valor(request.form.get("valor"))

    if tipo not in ("aporte", "retirada") or valor is None:
        flash("Informe um valor válido maior que zero.", "erro")
    elif tipo == "retirada" and valor > meta.valor_captado:
        flash(
            f"A retirada não pode ser maior que o valor guardado "
            f"({filtro_moeda(meta.valor_captado)}).",
            "erro",
        )
    else:
        db.session.add(MovimentoMeta(meta_id=meta.id, tipo=tipo, valor=valor))
        db.session.commit()
        if tipo == "aporte" and meta.concluida:
            flash(f'Meta "{meta.nome}" alcançada! 🎉', "ok")
        elif tipo == "aporte":
            flash("Valor adicionado à meta!", "ok")
        else:
            flash("Valor retirado da meta.", "ok")
    return redirect(url_for("metas"))


@app.route(
    "/metas/<int:meta_id>/movimentos/<int:movimento_id>/excluir", methods=["POST"]
)
@login_obrigatorio
def excluir_movimento_meta(meta_id, movimento_id):
    meta = Meta.query.filter_by(id=meta_id, user_id=session["user_id"]).first_or_404()
    movimento = MovimentoMeta.query.filter_by(
        id=movimento_id, meta_id=meta.id
    ).first_or_404()
    db.session.delete(movimento)
    db.session.commit()
    flash("Movimento removido.", "ok")
    return redirect(url_for("metas"))


@app.route("/metas/<int:meta_id>/excluir", methods=["POST"])
@login_obrigatorio
def excluir_meta(meta_id):
    meta = Meta.query.filter_by(id=meta_id, user_id=session["user_id"]).first_or_404()
    db.session.delete(meta)
    db.session.commit()
    flash("Meta excluída.", "ok")
    return redirect(url_for("metas"))


if __name__ == "__main__":
    app.run(
        debug=True,
        use_reloader=False,
        port=int(os.environ.get("PORT", 5001)),
    )
