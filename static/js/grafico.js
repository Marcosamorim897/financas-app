// Gráfico de barras (receitas × gastos) desenhado em canvas puro — sem dependências.
(function () {
  const canvas = document.getElementById('grafico');
  if (!canvas) return;

  const container = canvas.parentElement;
  const seletorAno = document.getElementById('seletor-ano');
  const estilo = getComputedStyle(document.documentElement);
  const COR_RECEITA = estilo.getPropertyValue('--receita').trim() || '#34d399';
  const COR_DESPESA = estilo.getPropertyValue('--despesa').trim() || '#f87171';
  const COR_TEXTO = estilo.getPropertyValue('--texto-suave').trim() || '#94a3b8';
  const COR_GRADE = estilo.getPropertyValue('--borda').trim() || '#334155';

  // tooltip mostrado ao passar o mouse (ou tocar) sobre uma barra
  const tooltip = document.createElement('div');
  tooltip.className = 'grafico-tooltip';
  container.appendChild(tooltip);

  let barras = [];
  let dadosAtuais = null;

  function formatarEixo(v) {
    if (v >= 1000) return 'R$ ' + (v / 1000).toFixed(v % 1000 === 0 ? 0 : 1) + ' mil';
    return 'R$ ' + v.toFixed(0);
  }

  function formatarMoeda(v) {
    return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  }

  function desenhar(dados) {
    const dpr = window.devicePixelRatio || 1;
    const larguraCss = container.clientWidth;
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
      ctx.fillText(formatarEixo((teto * i) / divisoes), margemEsq - 8, y + 4);
    }

    // barras (guarda a posição de cada uma para o tooltip)
    barras = [];
    const larguraMes = areaLargura / 12;
    const larguraBarra = Math.min(14, larguraMes / 3);
    dados.meses.forEach((mes, i) => {
      const centroX = margemEsq + larguraMes * i + larguraMes / 2;

      const hR = (dados.receitas[i] / teto) * areaAltura;
      const hD = (dados.despesas[i] / teto) * areaAltura;
      const base = margemSup + areaAltura;

      const xR = centroX - larguraBarra - 2;
      ctx.fillStyle = COR_RECEITA;
      ctx.beginPath();
      ctx.roundRect(xR, base - hR, larguraBarra, hR, 3);
      ctx.fill();
      if (dados.receitas[i] > 0) {
        barras.push({
          x: xR, y: base - hR, w: larguraBarra, h: hR,
          rotulo: 'Receitas', mes, valor: dados.receitas[i], cor: COR_RECEITA,
        });
      }

      const xD = centroX + 2;
      ctx.fillStyle = COR_DESPESA;
      ctx.beginPath();
      ctx.roundRect(xD, base - hD, larguraBarra, hD, 3);
      ctx.fill();
      if (dados.despesas[i] > 0) {
        barras.push({
          x: xD, y: base - hD, w: larguraBarra, h: hD,
          rotulo: 'Gastos', mes, valor: dados.despesas[i], cor: COR_DESPESA,
        });
      }

      ctx.fillStyle = COR_TEXTO;
      ctx.textAlign = 'center';
      ctx.fillText(mes, centroX, alturaCss - 8);
    });
  }

  function barraSob(x, y) {
    // margem de 3px para facilitar acertar barras finas ou baixas
    return barras.find(
      (b) => x >= b.x - 3 && x <= b.x + b.w + 3 && y >= b.y - 4 && y <= b.y + b.h
    );
  }

  function mostrarTooltip(evento) {
    const r = canvas.getBoundingClientRect();
    const x = evento.clientX - r.left;
    const y = evento.clientY - r.top;
    const barra = barraSob(x, y);

    if (!barra || !dadosAtuais) {
      tooltip.style.display = 'none';
      canvas.style.cursor = 'default';
      return;
    }

    tooltip.innerHTML =
      '<span class="tooltip-titulo"><i style="background:' + barra.cor + '"></i>' +
      barra.rotulo + ' · ' + barra.mes + '/' + dadosAtuais.ano + '</span>' +
      '<span class="tooltip-valor">' + formatarMoeda(barra.valor) + '</span>';
    tooltip.style.display = 'block';
    canvas.style.cursor = 'pointer';

    // posiciona ao lado do cursor, sem sair do container
    let esquerda = x + 14;
    if (esquerda + tooltip.offsetWidth > container.clientWidth) {
      esquerda = x - tooltip.offsetWidth - 14;
    }
    tooltip.style.left = Math.max(0, esquerda) + 'px';
    tooltip.style.top = Math.max(0, y - tooltip.offsetHeight - 8) + 'px';
  }

  canvas.addEventListener('mousemove', mostrarTooltip);
  canvas.addEventListener('click', mostrarTooltip); // toque no celular
  canvas.addEventListener('mouseleave', () => {
    tooltip.style.display = 'none';
  });

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
