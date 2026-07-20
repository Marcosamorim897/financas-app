// Gráfico donut de progresso das metas — canvas puro, sem dependências.
(function () {
  const canvases = document.querySelectorAll('.grafico-meta');
  if (!canvases.length) return;

  const estilo = getComputedStyle(document.documentElement);
  const COR_PROGRESSO = estilo.getPropertyValue('--primaria').trim() || '#10b981';
  const COR_COMPLETA = estilo.getPropertyValue('--receita').trim() || '#34d399';
  const COR_TRILHA = estilo.getPropertyValue('--fundo').trim() || '#0f172a';
  const COR_TEXTO = estilo.getPropertyValue('--texto').trim() || '#f1f5f9';
  const COR_TEXTO_SUAVE = estilo.getPropertyValue('--texto-suave').trim() || '#94a3b8';

  canvases.forEach((canvas) => {
    const captado = parseFloat(canvas.dataset.captado) || 0;
    const alvo = parseFloat(canvas.dataset.alvo) || 1;
    const fracao = Math.min(Math.max(captado / alvo, 0), 1);

    const tamanho = 150;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = tamanho * dpr;
    canvas.height = tamanho * dpr;
    canvas.style.width = tamanho + 'px';
    canvas.style.height = tamanho + 'px';

    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    const centro = tamanho / 2;
    const raio = centro - 10;
    const espessura = 14;
    const inicio = -Math.PI / 2; // começa no topo

    // trilha (total da meta)
    ctx.lineWidth = espessura;
    ctx.lineCap = 'round';
    ctx.strokeStyle = COR_TRILHA;
    ctx.beginPath();
    ctx.arc(centro, centro, raio, 0, Math.PI * 2);
    ctx.stroke();

    // arco de progresso (quanto já foi captado)
    if (fracao > 0) {
      ctx.strokeStyle = fracao >= 1 ? COR_COMPLETA : COR_PROGRESSO;
      ctx.beginPath();
      ctx.arc(centro, centro, raio, inicio, inicio + Math.PI * 2 * fracao);
      ctx.stroke();
    }

    // percentual no centro
    const percentual = (captado / alvo) * 100;
    ctx.fillStyle = COR_TEXTO;
    ctx.font = '700 26px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(Math.floor(percentual) + '%', centro, centro - 6);

    ctx.fillStyle = COR_TEXTO_SUAVE;
    ctx.font = '11px sans-serif';
    ctx.fillText('da meta', centro, centro + 16);
  });
})();
