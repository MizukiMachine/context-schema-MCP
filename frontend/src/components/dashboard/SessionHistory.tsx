import { useMemo, useState } from 'react';

export interface SessionHistoryItem {
  id: string;
  type: 'Prompt' | 'Context' | 'Template';
  beforeTokens: number;
  afterTokens: number;
  savedPercent: number;
  date: string;
}

interface SessionHistoryProps {
  items: SessionHistoryItem[];
  onRowClick?: (item: SessionHistoryItem) => void;
  pageSize?: number;
}

type FilterType = 'All' | SessionHistoryItem['type'];
type SortKey = 'date' | 'savedPercent';
type SortDirection = 'asc' | 'desc';

const FILTER_OPTIONS: FilterType[] = ['All', 'Prompt', 'Context', 'Template'];

function formatDate(value: string): string {
  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(parsed);
}

function getSortValue(item: SessionHistoryItem, sortKey: SortKey): number {
  if (sortKey === 'savedPercent') {
    return item.savedPercent;
  }

  const timestamp = new Date(item.date).getTime();
  return Number.isNaN(timestamp) ? 0 : timestamp;
}

function getSavingsBadge(savedPercent: number) {
  const isSavings = savedPercent >= 0;
  const arrow = isSavings ? '↓' : '↑';
  const tone = isSavings
    ? 'bg-emerald-50 text-emerald-700 ring-emerald-100'
    : 'bg-rose-50 text-rose-700 ring-rose-100';

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${tone}`}
    >
      <span aria-hidden="true">{arrow}</span>
      {Math.abs(savedPercent).toFixed(1)}%
    </span>
  );
}

export function SessionHistory({
  items,
  onRowClick,
  pageSize = 5,
}: SessionHistoryProps) {
  const [filterType, setFilterType] = useState<FilterType>('All');
  const [sortKey, setSortKey] = useState<SortKey>('date');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [currentPage, setCurrentPage] = useState(1);

  const filteredItems = useMemo(() => {
    if (filterType === 'All') {
      return items;
    }

    return items.filter((item) => item.type === filterType);
  }, [filterType, items]);

  const sortedItems = useMemo(() => {
    return [...filteredItems].sort((left, right) => {
      const leftValue = getSortValue(left, sortKey);
      const rightValue = getSortValue(right, sortKey);
      const direction = sortDirection === 'asc' ? 1 : -1;

      if (leftValue === rightValue) {
        return left.id.localeCompare(right.id) * direction;
      }

      return (leftValue - rightValue) * direction;
    });
  }, [filteredItems, sortDirection, sortKey]);

  const totalPages = Math.max(1, Math.ceil(sortedItems.length / pageSize));
  const effectivePage = Math.min(currentPage, totalPages);

  const paginatedItems = useMemo(() => {
    const startIndex = (effectivePage - 1) * pageSize;
    return sortedItems.slice(startIndex, startIndex + pageSize);
  }, [effectivePage, pageSize, sortedItems]);

  const pageNumbers = useMemo(() => {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }, [totalPages]);

  const handleSort = (nextSortKey: SortKey) => {
    if (sortKey === nextSortKey) {
      setCurrentPage(1);
      setSortDirection((currentDirection) =>
        currentDirection === 'asc' ? 'desc' : 'asc'
      );
      return;
    }

    setCurrentPage(1);
    setSortKey(nextSortKey);
    setSortDirection('desc');
  };

  const getSortIndicator = (targetKey: SortKey) => {
    if (sortKey !== targetKey) {
      return '↕';
    }

    return sortDirection === 'asc' ? '↑' : '↓';
  };

  const isClickable = typeof onRowClick === 'function';
  const pageStart = sortedItems.length === 0 ? 0 : (effectivePage - 1) * pageSize + 1;
  const pageEnd = Math.min(effectivePage * pageSize, sortedItems.length);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 border-b border-slate-200 pb-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.24em] text-slate-500">
            Optimization Sessions
          </p>
          <h3 className="mt-2 text-2xl font-semibold text-slate-900">Session History</h3>
          <p className="mt-1 text-sm text-slate-500">
            Review recent optimization runs, compare token savings, and drill into any row.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <label className="flex flex-col gap-1 text-sm text-slate-600">
            <span className="font-medium text-slate-700">Filter by type</span>
            <select
              value={filterType}
              onChange={(event) => {
                setCurrentPage(1);
                setFilterType(event.target.value as FilterType);
              }}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm outline-none transition focus:border-slate-400"
            >
              {FILTER_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>

          <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
            <span className="font-medium text-slate-900">{sortedItems.length}</span> session
            {sortedItems.length === 1 ? '' : 's'}
          </div>
        </div>
      </div>

      <div className="mt-5 overflow-hidden rounded-xl border border-slate-200">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr className="text-left text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                <th scope="col" className="px-4 py-3">#</th>
                <th scope="col" className="px-4 py-3">Type</th>
                <th scope="col" className="px-4 py-3">Before</th>
                <th scope="col" className="px-4 py-3">After</th>
                <th scope="col" className="px-4 py-3">
                  <button
                    type="button"
                    onClick={() => handleSort('savedPercent')}
                    className="inline-flex items-center gap-1 text-left text-xs font-semibold uppercase tracking-[0.16em] text-slate-500 transition hover:text-slate-900"
                  >
                    Saved
                    <span aria-hidden="true">{getSortIndicator('savedPercent')}</span>
                  </button>
                </th>
                <th scope="col" className="px-4 py-3">
                  <button
                    type="button"
                    onClick={() => handleSort('date')}
                    className="inline-flex items-center gap-1 text-left text-xs font-semibold uppercase tracking-[0.16em] text-slate-500 transition hover:text-slate-900"
                  >
                    Date
                    <span aria-hidden="true">{getSortIndicator('date')}</span>
                  </button>
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100 bg-white text-sm text-slate-700">
              {paginatedItems.length > 0 ? (
                paginatedItems.map((item, index) => {
                  const rowNumber = (effectivePage - 1) * pageSize + index + 1;

                  return (
                    <tr
                      key={item.id}
                      onClick={() => onRowClick?.(item)}
                      className={
                        isClickable
                          ? 'cursor-pointer transition hover:bg-slate-50'
                          : 'transition hover:bg-slate-50'
                      }
                    >
                      <td className="px-4 py-4 font-medium text-slate-900">{rowNumber}</td>
                      <td className="px-4 py-4">
                        <span className="inline-flex rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">
                          {item.type}
                        </span>
                      </td>
                      <td className="px-4 py-4 font-medium text-slate-900">
                        {item.beforeTokens.toLocaleString()}
                      </td>
                      <td className="px-4 py-4 font-medium text-slate-900">
                        {item.afterTokens.toLocaleString()}
                      </td>
                      <td className="px-4 py-4">{getSavingsBadge(item.savedPercent)}</td>
                      <td className="px-4 py-4 text-slate-600">{formatDate(item.date)}</td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-sm text-slate-500">
                    No optimization sessions match the selected filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-slate-500">
          Showing {pageStart}-{pageEnd} of {sortedItems.length}
        </p>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
            disabled={effectivePage === 1}
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Previous
          </button>

          {pageNumbers.map((pageNumber) => (
            <button
              key={pageNumber}
              type="button"
              onClick={() => setCurrentPage(pageNumber)}
              className={`h-9 min-w-9 rounded-lg px-3 text-sm font-medium transition ${
                pageNumber === effectivePage
                  ? 'bg-slate-900 text-white'
                  : 'border border-slate-200 text-slate-700 hover:bg-slate-50'
              }`}
            >
              {pageNumber}
            </button>
          ))}

          <button
            type="button"
            onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
            disabled={effectivePage === totalPages}
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </section>
  );
}
