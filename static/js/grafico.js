// Gráfico de barras (receitas × gastos) desenhado em canvas puro — sem dependências.
(function () {
  const canvas = document.getElementById('grafico');
  if (!canvas) return;

  const seletorAno = document.getElementById('seletor-ano');
  const estilo = getComputedStyle(document.documentElement);
  const COR_RECEITA = estilo.getPropertyValue('--receita').trim() || '#34d399';
  const COR_DESPESA = estilo.getPropertyValue('--despesa').trim() || '#f87171';
  const COR_TEXTO = estilo.getPropertyValue('--texto-suave').trim() || '#94a3b8';
  const COR_GRADE = estilo.getPropertyValue('--borda').trim() || '#334155';

  function formatarReal(v) {
    if (v >= 1000) return 'R$ ' + (v / 1000).toFixed(v % 1000 === 0 ? 0 : 1) + ' mil';
    return 'R$ ' + v.toFixed(0);
  }

  function desenhar(dados) {
    const dpr = window.devicePixelRatio || 1;
    const larguraCss = canvas.parentElement.clientWidth;
    const alturaCss = 260;
    canvas.width = larguraCss * dpr;
    canvas.height = alturaCss * dpr;
    canvas.style.height = alturaCss + 'px';

    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, larguraCss, alturaCss);

    const margemEsq = 56;
    const margemInf = 26;
    const margemSup = 12;
    const areaLargura = larguraCss - margemEsq - 10;
    const areaAltura = alturaCss - margemSup - margemInf;

    const maximo = Math.max(...dados.receitas, ...dados.despesas, 1);
    const teto = maximo * 1.15;

    // linhas de grade + rótulos do eixo Y
    ctx.font = '11px sans-serif';
    ctx.fillStyle = COR_TEXTO;
    ctx.strokeStyle = COR_GRADE;
    ctx.lineWidth = 1;
    const divisoes = 4;
    for (let i = 0; i <= divisoes; i++) {
      const y = margemSup + areaAltura - (areaAltura * i) / divisoes;
      ctx.beginPath();
      ctx.moveTo(margemEsq, y);
      ctx.lineTo(margemEsq + areaLargura, y);
      ctx.stroke();
      ctx.textAlign = 'right';
      ctx.fillText(formatarReal((teto * i) / divisoes), margemEsq - 8, y + 4);
    }

    // barras
    const larguraMes = areaLargura / 12;
    const larguraBarra = Math.min(14, larguraMes / 3);
    dados.meses.forEach((mes, i) => {
      const centroX = margemEsq + larguraMes * i + larguraMes / 2;

      const hR = (dados.receitas[i] / teto) * areaAltura;
      const hD = (dados.despesas[i] / teto) * areaAltura;
      const base = margemSup + areaAltura;

      ctx.fillStyle = COR_RECEITA;
      ctx.beginPath();
      ctx.roundRect(centroX - larguraBarra - 2, base - hR, larguraBarra, hR, 3);
      ctx.fill();

      ctx.fillStyle = COR_DESPESA;
      ctx.beginPath();
      ctx.roundRect(centroX + 2, base - hD, larguraBarra, hD, 3);
      ctx.fill();

      ctx.fillStyle = COR_TEXTO;
      ctx.textAlign = 'center';
      ctx.fillText(mes, centroX, alturaCss - 8);
    });
  }

  let dadosAtuais = null;

  function carregar(ano) {
    fetch('/api/grafico?ano=' + ano)
      .then((r) => r.json())
      .then((dados) => {
        dadosAtuais = dados;
        desenhar(dados);
      });
  }

  seletorAno.addEventListener('change', () => carregar(seletorAno.value));
  window.addEventListener('resize', () => dadosAtuais && desenhar(dadosAtuais));

  carregar(seletorAno.value);
})();
