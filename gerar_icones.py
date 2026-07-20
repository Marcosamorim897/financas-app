"""Gera os ícones PNG do PWA (192, 512 e 512 maskable)."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PASTA = Path(__file__).parent / "static" / "icons"
PASTA.mkdir(parents=True, exist_ok=True)

FUNDO = (15, 23, 42)       # --fundo
VERDE = (16, 185, 129)     # --primaria


def desenhar(tamanho: int, maskable: bool) -> Image.Image:
    img = Image.new("RGBA", (tamanho, tamanho), FUNDO)
    d = ImageDraw.Draw(img)

    # círculo verde central
    margem = tamanho * (0.18 if maskable else 0.10)
    d.ellipse(
        [margem, margem, tamanho - margem, tamanho - margem],
        fill=VERDE,
    )

    # símbolo R$ centralizado
    fonte = ImageFont.load_default(size=int(tamanho * 0.30))
    texto = "R$"
    caixa = d.textbbox((0, 0), texto, font=fonte)
    largura = caixa[2] - caixa[0]
    altura = caixa[3] - caixa[1]
    d.text(
        ((tamanho - largura) / 2 - caixa[0], (tamanho - altura) / 2 - caixa[1]),
        texto,
        font=fonte,
        fill=FUNDO,
    )
    return img


desenhar(192, False).save(PASTA / "icon-192.png")
desenhar(512, False).save(PASTA / "icon-512.png")
desenhar(512, True).save(PASTA / "icon-512-maskable.png")
print("Ícones gerados em", PASTA)
