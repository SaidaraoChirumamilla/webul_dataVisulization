let dataset = { buy_orders: [], sell_orders: [] };

function parseDate(d) {
  if (!d) return null;
  const s = String(d).trim();
  const m = s.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})/);
  if (m) return new Date(parseInt(m[3]), parseInt(m[1]) - 1, parseInt(m[2]));
  const m2 = s.match(/(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (m2) return new Date(parseInt(m2[1]), parseInt(m2[2]) - 1, parseInt(m2[3]));
  const dt = new Date(s);
  return isNaN(dt.getTime()) ? null : dt;
}

function inRange(date, start, end) {
  if (!start && !end) return true;
  if (!date) return false;
  const t = date.getTime();
  const s = start ? start.getTime() : -Infinity;
  const e = end ? end.getTime() : Infinity;
  return t >= s && t <= e;
}

onmessage = (e) => {
  const { type, payload } = e.data || {};
  if (type === 'INIT') {
    dataset.buy_orders = Array.isArray(payload.buy_orders) ? payload.buy_orders : [];
    dataset.sell_orders = Array.isArray(payload.sell_orders) ? payload.sell_orders : [];
    postMessage({ type: 'INIT_OK' });
  } else if (type === 'FILTER') {
    const q = (payload.search || '').toLowerCase();
    const status = payload.status || '';
    const start = payload.start ? new Date(payload.start) : null;
    const end = payload.end ? new Date(payload.end) : null;

    const filterFn = (order) => {
      const symbolOk = !q || (order.symbol || '').toLowerCase().includes(q);
      const statusOk = !status || (order.status || '') === status;
      const d = parseDate(order.date || '');
      const dateOk = inRange(d, start, end);
      return symbolOk && statusOk && dateOk;
    };

    const filteredBuy = dataset.buy_orders.filter(filterFn);
    const filteredSell = dataset.sell_orders.filter(filterFn);

    const totalBought = filteredBuy.reduce((s, o) => s + (o.total_value || 0), 0);
    const totalSold = filteredSell.reduce((s, o) => s + (o.total_value || 0), 0);
    const totalProfit = totalSold - totalBought;

    const sellPnls = filteredSell.map(o => o.profit || 0);
    const wins = sellPnls.filter(p => p > 0).length;
    const losses = sellPnls.filter(p => p < 0).length;
    const trades = sellPnls.length;
    const avgPnL = trades ? sellPnls.reduce((s, p) => s + p, 0) / trades : 0;
    const winRate = trades ? (wins / trades) : 0;

    const volumeBySymbol = {};
    [...filteredBuy, ...filteredSell].forEach(o => {
      const sym = o.symbol || 'N/A';
      const qty = o.quantity || 0;
      volumeBySymbol[sym] = (volumeBySymbol[sym] || 0) + qty;
    });
    const topSymbols = Object.entries(volumeBySymbol)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([symbol, volume]) => ({ symbol, volume }));

    postMessage({
      type: 'FILTER_RESULT',
      data: {
        filteredBuyOrders: filteredBuy,
        filteredSellOrders: filteredSell,
        totals: { totalBought, totalSold, totalProfit },
        metrics: { wins, losses, trades, avgPnL, winRate },
        topSymbols
      }
    });
  }
}