from datetime import date
from decimal import Decimal

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

CENTAVOS = Decimal("0.01")


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)

    transacoes = db.relationship(
        "Transacao", backref="usuario", lazy=True, cascade="all, delete-orphan"
    )
    dividas = db.relationship(
        "Divida", backref="usuario", lazy=True, cascade="all, delete-orphan"
    )


class Transacao(db.Model):
    __tablename__ = "transacoes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id"), nullable=False, index=True
    )
    tipo = db.Column(db.String(10), nullable=False)  # "receita" ou "despesa"
    descricao = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(50), nullable=False, default="Outros")
    valor = db.Column(db.Numeric(12, 2), nullable=False)
    data = db.Column(db.Date, nullable=False, default=date.today)


class Divida(db.Model):
    __tablename__ = "dividas"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id"), nullable=False, index=True
    )
    descricao = db.Column(db.String(200), nullable=False)
    valor_total = db.Column(db.Numeric(12, 2), nullable=False)
    num_parcelas = db.Column(db.Integer, nullable=False)
    parcelas_pagas = db.Column(db.Integer, nullable=False, default=0)
    data_primeira_parcela = db.Column(db.Date, nullable=False)

    @property
    def valor_parcela(self) -> Decimal:
        return (Decimal(self.valor_total) / self.num_parcelas).quantize(CENTAVOS)

    @property
    def quitada(self) -> bool:
        return self.parcelas_pagas >= self.num_parcelas

    @property
    def valor_restante(self) -> Decimal:
        restantes = self.num_parcelas - self.parcelas_pagas
        return (self.valor_parcela * restantes).quantize(CENTAVOS)

    def indice_parcela(self, ano: int, mes: int) -> int:
        """Índice (0-based) da parcela que vence no mês/ano dado."""
        inicio = self.data_primeira_parcela
        return (ano - inicio.year) * 12 + (mes - inicio.month)

    def parcela_no_mes(self, ano: int, mes: int) -> Decimal:
        """Valor da parcela que vence neste mês (0 se não houver)."""
        idx = self.indice_parcela(ano, mes)
        if 0 <= idx < self.num_parcelas:
            return self.valor_parcela
        return Decimal("0")
