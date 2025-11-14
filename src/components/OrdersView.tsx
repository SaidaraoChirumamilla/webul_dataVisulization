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
      const first = now.getDate() - now.getDay() + 