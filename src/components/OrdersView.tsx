import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { formatCurrency } from '../utils/formatters';
import { debounce } from '../utils/debounce';
import { SkeletonTable, SkeletonKPI } from './Skeletons';
import { ErrorState } from './ErrorState';

export interface Order {
  id: string;
  customer: string;
  date: string;
  status: 'pending' | 'completed' | 'cancelled' | string;
  total: number;
  type: 'buy' | 'sell';
  symbol: string;
  quantity: number;
  price: number;
}

export interface OrdersData {
  orders: Order[];
  buyTotal: number;
  sellTotal: number;
  openPositionValue: number;
  profit: number;
}

interface Filters {
  symbol: string;
  status: string;
  startDate: string | null;
  endDate: string | null;
}

const PAGE_SIZE = 50;

export const OrdersView: React.FC = () => {
  const [data, setData] = useState<OrdersData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<Filters>({ symbol: '', status: '', startDate: null, endDate: null });
  const [symbols, setSymbols] = useState<string[]>([]);
  const [buyPage, setBuyPage] = useState(1);
  const [sellPage, setSellPage] = useState(1);
  const [sort, setSort] = useState<{ key: keyof Order; dir: 'asc' | 'desc' }>({ key: 'date', dir: 'desc' });

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/orders');
      if (!res.ok) throw new Error('Failed to fetch orders');
      const json = await res.json();
      setData(json);
      const syms = Array.from(new Set(json.orders.map((o: Order) => o.symbol))).sort();
      setSymbols(syms);
    } catch (e: any) {
      setError(e.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const filtered = useMemo(() => {
    if (!data) return { buy: [], sell: [] };
    let orders = data.orders;
    if (filters.symbol) {
      orders = orders.filter((o) => o.symbol.toLowerCase().includes(filters.symbol.toLowerCase()));
    }
    if (filters.status) {
      orders = orders.filter((o) => o.status.toLowerCase() === filters.status.toLowerCase());
    }
    if (filters.startDate && filters.endDate) {
      const start = new Date(filters.startDate);
      const end = new Date(filters.endDate);
      orders = orders.filter((o) => {
        const d = new Date(o.date);
        return d >= start && d <= end;
      });
    }
    const sorted = [...orders].sort((a, b) => {
      const aVal = a[sort.key];
      const bVal = b[sort.key];
      if (sort.dir === 'asc') return aVal > bVal ? 1 : -1;
      return aVal < bVal ? 1 : -1;
    });
    const buy = sorted.filter((o) => o.type === 'buy');
    const sell = sorted.filter((o) => o.type === 'sell');
    return { buy, sell };
  }, [data, filters, sort]);

  const paginate = (list: Order[], page: number) => list.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const handleSort = (key: keyof Order) => {
    setSort((s) => ({ key, dir: s.key === key && s.dir === 'asc' ? 'desc' : 'asc' }));
  };

  const handleDatePreset = (preset: string) => {
    const now = new Date();
    let start: Date | null = null;
    let end: Date | null = null;
    if (preset === 'today') {
      start = end = now;
    } else if (preset === 'week') {
      const first = now.getDate() - now.getDay() + 1;
      start = new Date(now.getFullYear(), now.getMonth(), first);
      end = new Date(start);
      end.setDate(start.getDate() + 6);
    } else if (preset === 'month') {
      start = new Date(now.getFullYear(), now.getMonth(), 1);
      end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    } else if (preset === 'quarter') {
      const q = Math.floor(now.getMonth() / 3);
      start = new Date(now.getFullYear(), q * 3, 1);
      end = new Date(now.getFullYear(), (q + 1) * 3, 0);
    }
    setFilters((f) => ({ ...f, startDate: start ? start.toISOString().split('T')[0] : null, endDate: end ? end.toISOString().split('T')[0] : null }));
  };

  const Table: React.FC<{ rows: Order[]; title: string }> = ({ rows, title }) => (
    <div className="bg-white rounded-xl shadow p-4">
      <h3 className="text-lg font-semibold mb-3">{title}</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {(['symbol', 'quantity', 'price', 'date', 'status'] as (keyof Order)[]).map((k) => (
                <th key={k} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" onClick={() => handleSort(k)}>
                  {k} {sort.key === k ? (sort.dir === 'asc' ? '▲' : '▼') : ''}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {rows.map((o) => (
              <tr key={o.id} className="hover:bg-gray-50">
                <td className="px-4 py-2 text-sm font-medium text-gray-900">{o.symbol}</td>
                <td className="px-4 py-2 text-sm text-gray-500">{o.quantity.toLocaleString()}</td>
                <td className="px-4 py-2 text-sm text-gray-500">{formatCurrency(o.price)}</td>
                <td className="px-4 py-2 text-sm text-gray-500">{new Date(o.date).toLocaleDateString()}</td>
                <td className="px-4 py-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${o.status === 'completed' ? 'bg-green-100 text-green-800' : o.status === 'cancelled' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>{o.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <SkeletonKPI />
          <SkeletonKPI />
          <SkeletonKPI />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SkeletonTable />
          <SkeletonTable />
        </div>
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  if (!data) {
    return <ErrorState message="No orders data available" onRetry={fetchData} />;
  }

  const buyPageRows = paginate(filtered.buy, buyPage);
  const sellPageRows = paginate(filtered.sell, sellPage);

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-sm font-medium text-gray-500">Total Bought</div>
          <div className="text-2xl font-bold text-green-600">{formatCurrency(data.buyTotal)}</div>
          <div className="text-xs text-gray-400 mt-1">vs prev period</div>
        </div>
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-sm font-medium text-gray-500">Total Sold / Open Value</div>
          <div className="text-2xl font-bold text-blue-600">{formatCurrency(data.sellTotal)}</div>
          <div className="text-xs text-gray-400 mt-1">Open: {formatCurrency(data.openPositionValue)}</div>
        </div>
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-sm font-medium text-gray-500">Profit</div>
          <div className={`text-2xl font-bold ${data.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>{formatCurrency(data.profit)}</div>
          <div className="text-xs text-gray-400 mt-1">vs prev period</div>
        </div>
      </div>