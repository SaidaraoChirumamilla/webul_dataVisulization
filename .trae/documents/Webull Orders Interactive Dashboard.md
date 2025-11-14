## Overview

* Implement a two‑view, interactive dashboard: Financial Flow Analysis and Order Analysis, built on existing Flask backend and Chart.js front‑end.

* Preserve current color scheme, typography, and interaction patterns; extend responsive layout for desktop, tablet, and mobile.

## Current State

* Backend provides `/api/data` with processed cash‑flow and order data (app.py:598–623).

* Front‑end uses Chart.js and custom JS in `templates/index.html` for metrics and basic order tables (templates/index.html:485–1087).

* Inconsistencies: missing `view-orders` container while chart logic expects it (templates/index.html:605–609), duplicated `order-tables` blocks, and filter IDs mismatch (`stock-filter` vs existing `stock-search`).

## Architecture

* **Backend**: Keep `/api/data`; add optional endpoints for export and raw orders if needed.

* **Front‑end**: Split into two dedicated view containers: `view-cashflow` and `view-orders`. Extract interactive logic into modular scripts loaded from `index.html`.

* **Workers**: Add a Web Worker for heavy client‑side filtering and KPI calculations.

* **Storage**: Use `localStorage` for session persistence of filters, view preference, and sorting.

## Backend APIs

* Reuse existing processors: `process_monthly_cash_flow`, `process_yearly_transfer_volume`, `process_transaction_status`, `process_transfer_by_type`, `process_order_analysis` (app.py:151–591).

* Add `/api/orders/raw` to return raw orders for advanced segment metrics (time‑of‑day, day‑of‑week) if needed, or compute on client from `order_analysis` payload.

* Add `/api/export` (POST) to accept current filter state and return CSV/Excel; server can stream CSV while Excel/PDF handled client‑side for simplicity.

## Financial Flow View

* **KPIs**: Incoming funds, outgoing funds, net cash flow (already in `calculate_summary_metrics`, app.py:294–328). Display them prominently.

* **Charts**:

  * Monthly cash flow stacked bars + net line (already scaffolded, templates/index.html:616–678).

  * Yearly stacked bars (templates/index.html:680–734).

  * Status distribution donut (templates/index.html:736–778).

  * Transfer by type horizontal bars (templates/index.html:780–826).

* **Filters**: Transaction status, time period picker (custom ranges, MTD/QTD/YTD, comparison), transaction type filter.

* **Trends**: Toggle daily/weekly/monthly aggregation in worker; update charts dynamically.

## Order Analysis View

* **KPIs**:

  * Total orders count and breakdown by status.

  * Win/loss ratio; average P\&L per trade; distribution histogram.

  * Top 5 traded tickers by volume.

  * Performance segmented by time of day, day of week, monthly trends.

* **Visualizations**:

  * Interactive sortable table with pagination (50 per page) and virtual scrolling for large sets.

  * Bar/line charts for trends; pie charts for proportions; sparklines embedded in table rows for per‑symbol patterns.

* **Controls**:

  * Multi‑select symbol filter with typeahead and fuzzy match.

  * Status selector (filled, canceled, pending, etc.).

  * Advanced date range picker with quick selects (today, week, month) and custom ranges.

  * Reset All button.

* **Position Tracking**:

  * Aggregate market value, cost basis, gain/loss %, position duration.

  * Visual indicators for profit/loss thresholds and position size relative to portfolio.

  * Price source abstraction: use optional server quotes (e.g., Yahoo Finance) with env toggle; fall back to last known price if unavailable.

## Web Workers

* Create `processing.worker.js` to:

  * Filter orders by symbol(s), status, and date range.

  * Compute KPIs (win/loss, average P\&L, top tickers, segments).

  * Aggregate cash‑flow at daily/weekly/monthly granularity.

* Message protocol: `{type: 'FILTER_ORDERS', payload: {...}}` → `{type: 'FILTER_RESULT', data: {...}}`.

* Offload large computations to keep UI responsive.

## Filters & Persistence

* Replace mismatched IDs and consolidate filters:

  * `stock-search` keeps typeahead input; add multi‑select list.

  * `status-filter` remains; populate from `order_analysis.statuses`.

  * Add `date-range` inputs powered by Flatpickr.

* Persist `view`, `filters`, and `sorting` in `localStorage` with keys like `wb:view`, `wb:filters`, `wb:sort`.

* Restore on load; provide "Reset All" to clear.

## Export

* **CSV**: Client builds CSV from filtered dataset; download via Blob.

* **Excel**: Integrate SheetJS via CDN for `.xlsx` export.

* **PDF**: Use `jsPDF` + `html2canvas` to export current view.

* Include loading indicators and error handling during exports.

## Visualization Library Integration

* Continue with Chart.js v4 (already loaded, templates/index.html:7).

* Tooltips on hover for all charts; contextual help icons near section titles.

* Choose chart types based on data distributions; ensure legends and scales are meaningful.

## Performance & Data Management

* Pagination at 50 items/page; keyboard accessible controls.

* Virtual scrolling using IntersectionObserver for long tables; render windowed rows only.

* Lazy load historical data: load recent N months initially; fetch older ranges on demand.

* Manual refresh button (already present) and auto refresh with configurable interval.

## Error Handling & UX

* Clear messages for network failures, parsing issues, calculation errors.

* Retry button on error card; fallback to last successful state if available.

* Loading indicators for data fetch, filter apply, and export processing.

## Accessibility & Consistency

* Match existing gradients and typography.

* Add ARIA roles for tabs, tables, and charts; ensure focus states.

* Use semantic headings and labels; high‑contrast feedback for profit/loss.

## Implementation Details (Code References)

* Fix tab labels to "Financial Flow" and "Order Analysis" and add missing `view-orders` container (templates/index.html:335–341, 605–609).

* Consolidate filters block under `view-orders`; remove duplicate `order-tables` and align IDs used in `createOrderAnalysisCharts` and `displayOrderAnalysis` (templates/index.html:861–887, 913–939, 1007–1083).

* Extend `process_order_analysis` to include counts and segment metrics if server‑side calculation is preferred (app.py:341–591).

* Keep index route (app.py:593–596) and `/api/data` contract (app.py:598–623).

## Phased Rollout

* Phase 1: Clean up HTML structure, add `view-orders`, align filters and KPIs; wire existing charts.

* Phase 2: Implement Web Worker and filtering; add date picker and quick ranges; persist settings.

* Phase 3: Add KPIs (win/loss, average P\&L), distribution charts, top tickers; position tracking with price provider abstraction.

* Phase 4: Table pagination and virtual scrolling; export (CSV/Excel/PDF) with loaders and errors.

* Phase 5: Auto refresh, comparison periods (overlay/side‑by‑side), accessibility polish, and help.

## Verification

* Unit test processors in isolation (sample datasets).

* Manual test: large synthetic dataset to validate worker performance and virtualization.

* Visual check across desktop/tablet/mobile.

* Confirm persistence across reloads; verify exports and error states.

Confirm to proceed and I will implement Phase 1, then iterate through subsequent phases with verification after each step.
