// Auditoria automática de layout, executada no navegador com o dashboard aberto (cole no console).
// Aponta, na aba visível: barras com valor que não foram desenhadas, marcas de eixo repetidas,
// texto sobre barra, textos sobrepostos ou cortados pela área do gráfico, elementos que transbordam
// o próprio cartão, marcas do slider encavaladas e rolagem horizontal da página.
(() => {
  const sobrepoe = (a, b, tol = 1) =>
    a.left < b.right - tol && b.left < a.right - tol && a.top < b.bottom - tol && b.top < a.bottom - tol;
  const problemas = [];
  document.querySelectorAll('.js-plotly-plot').forEach((p) => {
    const id = p.closest('[id]') ? p.closest('[id]').id : '?';
    const caixa = p.getBoundingClientRect();
    // barra com valor (acima de 0,5% do maior) que não aparece desenhada
    (p._fullData || []).forEach((tr, k) => {
      if (tr.type !== 'bar') return;
      const vals = Array.from((tr.orientation === 'h' ? tr.x : tr.y) || []).map(Number);
      const mx = Math.max(0, ...vals.filter((v) => !isNaN(v)));
      const esperadas = vals.filter((v) => v > 0.005 * mx).length;
      const g = p.querySelectorAll('.trace.bars')[k];
      const vistas = g ? [...g.querySelectorAll('path')].filter((b) => {
        const r = b.getBoundingClientRect(); return r.width > 0.5 && r.height > 0.5;
      }).length : 0;
      if (vistas < esperadas) problemas.push({ visual: id, tipo: 'barra não desenhada', texto: `${vistas}/${esperadas}` });
    });
    const textos = [...p.querySelectorAll('text')]
      .filter((t) => t.textContent.trim() && !t.closest('.hoverlayer'))
      .map((t) => ({ t: t.textContent.trim(), r: t.getBoundingClientRect() }))
      .filter((x) => x.r.width > 0 && x.r.height > 0);
    // marcas repetidas no mesmo eixo (ex.: anos fracionários arredondados)
    ['xtick', 'ytick'].forEach((c) => {
      const v = [...p.querySelectorAll(`.${c} text`)].map((t) => t.textContent);
      if (new Set(v).size !== v.length) problemas.push({ visual: id, tipo: 'marca repetida', texto: v.join(',') });
    });
    // texto sobre uma barra (rótulo encostando na barra vizinha)
    const barras = [...p.querySelectorAll('.bars path')].map((b) => b.getBoundingClientRect()).filter((r) => r.width > 0 && r.height > 0);
    textos.forEach((t) => barras.forEach((b) => { if (sobrepoe(t.r, b, 1)) problemas.push({ visual: id, tipo: 'texto sobre barra', texto: t.t }); }));
    for (let i = 0; i < textos.length; i++) {
      const a = textos[i];
      if (a.r.left < caixa.left - 1 || a.r.right > caixa.right + 1 || a.r.top < caixa.top - 1 || a.r.bottom > caixa.bottom + 1)
        problemas.push({ visual: id, tipo: 'cortado', texto: a.t });
      for (let j = i + 1; j < textos.length; j++)
        if (sobrepoe(a.r, textos[j].r)) problemas.push({ visual: id, tipo: 'sobreposto', texto: `${a.t} × ${textos[j].t}` });
    }
  });
  document.querySelectorAll('.ds-cartao, .ds-filtros, .ds-cabecalho, .ds-secao__topo, .ds-abas').forEach((c) => {
    const rc = c.getBoundingClientRect();
    c.querySelectorAll('p, h1, h2, h3, label, span, small, .Select-control, .rc-slider-mark-text, button, .ds-aba').forEach((e) => {
      const r = e.getBoundingClientRect();
      if (r.width === 0 || getComputedStyle(e).display === 'none') return;
      if (r.right > rc.right + 1 || r.left < rc.left - 1)
        problemas.push({ visual: c.className.split(' ')[0], tipo: 'transborda', texto: (e.textContent || e.className).trim().slice(0, 40) });
    });
  });
  const marcas = [...document.querySelectorAll('.rc-slider-mark-text')]
    .filter((e) => getComputedStyle(e).display !== 'none').map((e) => e.getBoundingClientRect());
  for (let i = 1; i < marcas.length; i++) if (sobrepoe(marcas[i - 1], marcas[i], 0)) problemas.push({ visual: 'rangeslider', tipo: 'sobreposto', texto: `marca ${i}` });
  return {
    largura: innerWidth,
    rolagem_horizontal: document.documentElement.scrollWidth > innerWidth + 1,
    graficos_com_dados: [...document.querySelectorAll('.js-plotly-plot')].filter((p) => (p.data || []).length > 0).length,
    kpis: document.querySelectorAll('.ds-kpi__valor').length,
    erros_dash: document.querySelectorAll('.dash-fe-error__title').length,
    n: problemas.length,
    problemas: problemas.slice(0, 8),
  };
})();
