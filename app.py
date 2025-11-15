from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import os
from datetime import datetime
import json
import requests
import csv
from io import StringIO

app = Flask(__name__)
CORS(app)  # Enable CORS to prevent 403 errors

# Google Sheets configuration
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Google Sheet ID from the URL
SPREADSHEET_ID = "1pzKHZ5xPT6oMMQ4wNNGL-Z1I-81qa_MtjI_seL5M1Ug"
WORKSHEET_GID = "1100303320"

USE_PUBLIC_ACCESS = os.getenv('USE_PUBLIC_ACCESS', 'false').lower() == 'true'
ENABLE_QUOTES = os.getenv('ENABLE_QUOTES', 'true').lower() == 'true'
USE_POSITIONS_SHEET = os.getenv('USE_POSITIONS_SHEET', 'false').lower() == 'true'
POSITIONS_SPREADSHEET_ID = os.getenv('POSITIONS_SPREADSHEET_ID', '')
POSITIONS_WORKSHEET_GID = os.getenv('POSITIONS_WORKSHEET_GID', '')

def get_google_sheets_client():
    """Initialize and return Google Sheets client"""
    try:
        # Try to use service account credentials from environment or file
        creds_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        
        if os.path.exists(creds_file):
            creds = Credentials.from_service_account_file(creds_file, scopes=SCOPE)
            client = gspread.authorize(creds)
            return client
        else:
            print(f"Credentials file not found: {creds_file}")
            return None
    except Exception as e:
        print(f"Error initializing Google Sheets client: {e}")
        return None

def get_sheet_data_public(spreadsheet_id=None, worksheet_gid=None):
    """Fetch data from public Google Sheet using CSV export"""
    try:
        sheet_id = spreadsheet_id or SPREADSHEET_ID
        gid = worksheet_gid if worksheet_gid is not None else WORKSHEET_GID
        
        # Try with gid first
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
        response = requests.get(csv_url, timeout=10)
        
        # Check if we got HTML (login page) instead of CSV
        if response.text.strip().startswith('<!DOCTYPE') or '<html' in response.text.lower():
            print("Sheet is not publicly accessible. Trying without gid...")
            # Try without gid (first sheet)
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            response = requests.get(csv_url, timeout=10)
            
            # Still HTML? Sheet is private
            if response.text.strip().startswith('<!DOCTYPE') or '<html' in response.text.lower():
                print("Error: Google Sheet is not publicly accessible.")
                print("Please either:")
                print("1. Make the sheet public: Share → Change to anyone with the link")
                print("2. Set up Google Sheets API credentials (see README.md)")
                return None
        
        response.raise_for_status()
        
        # Parse CSV
        csv_data = StringIO(response.text)
        reader = csv.DictReader(csv_data)
        data = list(reader)
        
        if not data:
            print("Warning: Sheet appears to be empty or has no data rows")
            return None
            
        print(f"Successfully fetched {len(data)} rows from Google Sheet")
        return data
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching public sheet data: {e}")
        return None
    except Exception as e:
        print(f"Error fetching public sheet data: {e}")
        return None

def get_sheet_data(spreadsheet_id=None, worksheet_gid=None):
    """Fetch data from Google Sheet"""
    sheet_id = spreadsheet_id or SPREADSHEET_ID
    gid = worksheet_gid if worksheet_gid is not None else WORKSHEET_GID
    
    # Try public access first if enabled
    if USE_PUBLIC_ACCESS:
        data = get_sheet_data_public(sheet_id, gid)
        if data:
            return data
    
    # Try authenticated access
    try:
        client = get_google_sheets_client()
        if not client:
            # Fallback to public access
            return get_sheet_data_public(sheet_id, gid)
        
        sheet = client.open_by_key(sheet_id)
        # Try to get worksheet by gid or by index
        try:
            worksheet = sheet.get_worksheet_by_id(int(gid))
        except:
            worksheet = sheet.sheet1  # Fallback to first sheet
        
        # Get all values
        data = worksheet.get_all_records()
        return data
    except Exception as e:
        print(f"Error fetching sheet data: {e}")
        # Fallback to public access
        return get_sheet_data_public(sheet_id, gid)

def parse_date(date_str):
    """Parse date string in various formats"""
    if not date_str:
        return None
    
    date_formats = [
        '%m/%d/%Y',      # 11/29/2021
        '%m/%d/%Y %I:%M %p',  # 11/29/2021 11:28 AM
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%Y/%m/%d',
        '%m-%d-%Y',
        '%d-%m-%Y',
        '%B %d, %Y',
        '%b %d, %Y',
        '%d %B %Y',
        '%d %b %Y'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except:
            continue
    
    return None

def process_monthly_cash_flow(data):
    """Process data for monthly cash flow chart"""
    monthly_data = {}
    
    for row in data:
        # Get date from various possible column names
        date_str = (row.get('transfer date') or row.get('Transfer Initiated') or 
                   row.get('Date') or row.get('date') or '')
        
        # Get amount - prefer "Amount Numeric" if available, otherwise parse "Amount"
        amount_str = row.get('Amount Numeric') or row.get('Amount') or '0'
        amount = 0
        
        try:
            # Remove $, commas, and spaces, then convert
            amount = float(str(amount_str).replace('$', '').replace(',', '').replace(' ', '').replace('+', '') or 0)
        except:
            amount = 0
        
        # Determine if incoming or outgoing based on Type or amount sign
        transfer_type = row.get('Type', '').lower()
        is_incoming = amount > 0 or 'incoming' in transfer_type
        
        if date_str:
            date_obj = parse_date(date_str)
            if date_obj:
                month_key = date_obj.strftime('%Y-%m')
                
                if month_key not in monthly_data:
                    monthly_data[month_key] = {'incoming': 0, 'outgoing': 0}
                
                if is_incoming:
                    monthly_data[month_key]['incoming'] += abs(amount)
                else:
                    monthly_data[month_key]['outgoing'] += abs(amount)
    
    # Sort by date
    sorted_months = sorted(monthly_data.keys())
    
    return {
        'months': sorted_months,
        'incoming': [monthly_data[m]['incoming'] for m in sorted_months],
        'outgoing': [monthly_data[m]['outgoing'] for m in sorted_months],
        'net_flow': [monthly_data[m]['incoming'] - monthly_data[m]['outgoing'] for m in sorted_months]
    }

def process_yearly_transfer_volume(data):
    """Process data for yearly transfer volume chart"""
    yearly_data = {}
    
    for row in data:
        # Get date from various possible column names
        date_str = (row.get('transfer date') or row.get('Transfer Initiated') or 
                   row.get('Date') or row.get('date') or '')
        
        # Get amount - prefer "Amount Numeric" if available
        amount_str = row.get('Amount Numeric') or row.get('Amount') or '0'
        amount = 0
        
        try:
            amount = float(str(amount_str).replace('$', '').replace(',', '').replace(' ', '').replace('+', '') or 0)
        except:
            amount = 0
        
        # Determine if incoming or outgoing
        transfer_type = row.get('Type', '').lower()
        is_incoming = amount > 0 or 'incoming' in transfer_type
        
        if date_str:
            date_obj = parse_date(date_str)
            if date_obj:
                year = date_obj.strftime('%Y')
                
                if year not in yearly_data:
                    yearly_data[year] = {'incoming': 0, 'outgoing': 0}
                
                if is_incoming:
                    yearly_data[year]['incoming'] += abs(amount)
                else:
                    yearly_data[year]['outgoing'] += abs(amount)
    
    sorted_years = sorted(yearly_data.keys())
    
    return {
        'years': sorted_years,
        'incoming': [yearly_data[y]['incoming'] for y in sorted_years],
        'outgoing': [yearly_data[y]['outgoing'] for y in sorted_years]
    }

def process_transaction_status(data):
    """Process data for transaction status distribution"""
    status_counts = {}
    
    for row in data:
        status = row.get('Status', row.get('status', ''))
        if status:
            # Normalize status name (capitalize first letter)
            status_normalized = status.strip().capitalize()
            if status_normalized not in status_counts:
                status_counts[status_normalized] = 0
            status_counts[status_normalized] += 1
    
    total = sum(status_counts.values())
    if total == 0:
        return {'labels': [], 'values': [], 'percentages': []}
    
    labels = list(status_counts.keys())
    values = list(status_counts.values())
    percentages = [(v / total * 100) for v in values]
    
    return {
        'labels': labels,
        'values': values,
        'percentages': percentages
    }

def process_transfer_by_type(data):
    """Process data for transfer volume by type"""
    type_data = {}
    
    for row in data:
        transfer_type = row.get('Type', row.get('type', row.get('Transfer Type', '')))
        
        # Get amount - prefer "Amount Numeric" if available
        amount_str = row.get('Amount Numeric') or row.get('Amount') or '0'
        amount = 0
        
        try:
            # Remove $, commas, spaces, and + sign, use absolute value
            amount = abs(float(str(amount_str).replace('$', '').replace(',', '').replace(' ', '').replace('+', '') or 0))
        except:
            amount = 0
        
        if transfer_type:
            if transfer_type not in type_data:
                type_data[transfer_type] = 0
            type_data[transfer_type] += amount
    
    return {
        'types': list(type_data.keys()),
        'amounts': list(type_data.values())
    }

def calculate_summary_metrics(data):
    """Calculate summary metrics from the data"""
    total_incoming_completed = 0
    total_outgoing_completed = 0
    
    for row in data:
        status = row.get('Status', '').strip()
        if status.lower() != 'completed':
            continue
        
        # Get amount
        amount_str = row.get('Amount Numeric') or row.get('Amount') or '0'
        amount = 0
        
        try:
            amount = float(str(amount_str).replace('$', '').replace(',', '').replace(' ', '').replace('+', '') or 0)
        except:
            amount = 0
        
        # Determine if incoming or outgoing
        transfer_type = row.get('Type', '').lower()
        is_incoming = amount > 0 or 'incoming' in transfer_type
        
        if is_incoming:
            total_incoming_completed += abs(amount)
        else:
            total_outgoing_completed += abs(amount)
    
    net_account_value = total_incoming_completed - total_outgoing_completed
    
    return {
        'total_incoming_completed': total_incoming_completed,
        'total_outgoing_completed': total_outgoing_completed,
        'net_account_value': net_account_value
    }

def parse_float(value, default=0):
    """Parse float value from various formats"""
    if not value:
        return default
    try:
        # Remove $, commas, spaces, and other characters
        cleaned = str(value).replace('$', '').replace(',', '').replace(' ', '').replace('+', '').replace('(', '-').replace(')', '')
        return float(cleaned) if cleaned else default
    except:
        return default



def extract_positions_from_sheet(rows):
    positions = []
    if not rows:
        return positions
    for row in rows:
        keys = {k.lower(): k for k in row.keys()}
        symbol = None
        for key in keys:
            if any(x in key for x in ['symbol', 'ticker', 'stock', 'instrument', 'security', 'name']):
                symbol = str(row[keys[key]]).strip()
                if symbol:
                    break
        qty = 0.0
        for key in keys:
            if any(x in key for x in ['quantity', 'qty', 'shares', 'share', 'position']):
                qty = parse_float(row[keys[key]], 0)
                if qty != 0:
                    break
        cost_basis = 0.0
        for key in keys:
            if any(x in key for x in ['cost basis', 'avg price', 'average price', 'cost', 'basis']):
                cost_basis = parse_float(row[keys[key]], 0)
                if cost_basis != 0:
                    break
        status_val = None
        for key in keys:
            if 'status' in key or 'state' in key:
                v = row[keys[key]]
                status_val = str(v).strip() if v is not None else None
                break
        is_open = True
        if status_val:
            s = status_val.lower()
            if 'closed' in s or 'sold' in s or 'exit' in s:
                is_open = False
        if qty <= 0:
            is_open = False
        if symbol and is_open:
            positions.append({'symbol': symbol, 'quantity': float(qty), 'cost_basis': float(cost_basis)})
    return positions

def process_orders_list(orders_data):
    result = []
    if not orders_data:
        return result
    for i, row in enumerate(orders_data):
        keys = {k.lower(): k for k in row.keys()}
        oid = None
        for k in keys:
            if 'side' in k:
                continue
            if any(x in k for x in ['order id', 'orderid', ' id ', 'id', 'trade id', 'transaction id']):
                v = row[keys[k]]
                oid = str(v).strip() if v is not None else None
                if oid:
                    break
        cust = None
        for k in keys:
            if any(x in k for x in ['customer', 'customer name', 'client', 'account', 'account name', 'name']):
                v = row[keys[k]]
                cust = str(v).strip() if v is not None else None
                if cust:
                    break
        status = None
        for k in keys:
            if any(x in k for x in ['status', 'state']):
                v = row[keys[k]]
                status = str(v).strip() if v is not None else None
                if status:
                    break
        date_val = None
        for k in keys:
            if any(x in k for x in ['filled time', 'placed time', 'order date', 'date', 'timestamp']):
                v = row[keys[k]]
                date_val = str(v).strip() if v is not None else None
                if date_val:
                    if ' ' in date_val:
                        date_val = date_val.split(' ')[0]
                    break
        total = 0.0
        for k in keys:
            if any(x in k for x in ['amount', 'value']) and not any(y in k for y in ['qty', 'quantity', 'shares']):
                total = parse_float(row[keys[k]], 0)
                if total != 0:
                    break
        if total == 0:
            price = 0.0
            qty = 0.0
            for k in keys:
                if 'price' in k:
                    price = parse_float(row[keys[k]], 0)
                    if price != 0:
                        break
            for k in keys:
                if any(x in k for x in ['quantity', 'qty', 'shares', 'filled']):
                    qty = parse_float(row[keys[k]], 0)
                    if qty != 0:
                        break
            total = price * qty
        if not oid:
            oid = f"ORD-{i+1}"
        result.append({
            'id': oid,
            'customer': cust or 'N/A',
            'date': date_val or '',
            'status': status or 'N/A',
            'total': float(total)
        })
    return result

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/orders')
def orders():
    """Orders dashboard page"""
    return render_template('orders.html')

@app.route('/tests')
def tests():
    """Unit tests page"""
    return render_template('tests.html')

@app.route('/e2e-tests')
def e2e_tests():
    """End-to-end tests page"""
    return render_template('e2e-tests.html')

@app.route('/api/data')
def get_data():
    """API endpoint to fetch and return processed data"""
    raw_data = get_sheet_data()
    
    if not raw_data:
        error_msg = 'Unable to fetch data from Google Sheets. '
        if USE_PUBLIC_ACCESS:
            error_msg += 'The sheet may not be publicly accessible. Please make it public (Share → Anyone with the link) or set up Google Sheets API credentials.'
        else:
            error_msg += 'Please check your credentials or make the sheet publicly accessible.'
        return jsonify({
            'error': error_msg
        }), 500
    
    return jsonify({
        'monthly_cash_flow': process_monthly_cash_flow(raw_data),
        'yearly_transfer_volume': process_yearly_transfer_volume(raw_data),
        'transaction_status': process_transaction_status(raw_data),
        'transfer_by_type': process_transfer_by_type(raw_data),
        'summary_metrics': calculate_summary_metrics(raw_data)
    })



@app.route('/api/positions')
def api_positions():
    if not USE_POSITIONS_SHEET:
        return jsonify({'positions': []})
    sheet_id = POSITIONS_SPREADSHEET_ID or SPREADSHEET_ID
    gid = POSITIONS_WORKSHEET_GID or WORKSHEET_GID
    rows = get_sheet_data(sheet_id, gid)
    positions = extract_positions_from_sheet(rows or [])
    return jsonify({'positions': positions})

def fetch_quotes(symbols):
    results = {}
    try:
        joined = ','.join(symbols)
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={joined}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            for item in data.get('quoteResponse', {}).get('result', []):
                sym = item.get('symbol')
                price = item.get('regularMarketPrice')
                if sym and price is not None:
                    results[sym] = float(price)
    except Exception:
        pass
    return results

@app.route('/api/quotes')
def api_quotes():
    if not ENABLE_QUOTES:
        return jsonify({'error': 'Quotes disabled'}), 400
    syms = request.args.get('symbols', '')
    symbols = [s.strip() for s in syms.split(',') if s.strip()]
    if not symbols:
        return jsonify({'error': 'No symbols provided'}), 400
    quotes = fetch_quotes(symbols)
    return jsonify({'quotes': quotes})

@app.route('/api/raw')
def get_raw_data():
    """API endpoint to return raw sheet data"""
    data = get_sheet_data()
    if not data:
        return jsonify({'error': 'Unable to fetch data'}), 500
    return jsonify(data)

@app.route('/api/orders')
def extract_field(row, candidates, default=None, transform=lambda x: x):
    for k in row:
        if any(x in k.lower() for x in candidates):
            v = row[k]
            return transform(v) if v is not None else default
    return default
def get_orders():
    raw_data = get_sheet_data()
    
    if not raw_data:
        return jsonify({'buy': [], 'sell': [], 'error': 'Unable to fetch data from Google Sheets'}), 500
    
    # Process orders data - extract buy and sell orders
    buy_orders, sell_orders = [], []
    
    for i, row in enumerate(raw_data):
        symbol = extract_field(row, ['symbol', 'ticker', 'stock', 'instrument'], 'N/A', lambda v: str(v).strip())
        side = extract_field(row, ['side', 'action', 'type', 'buy_sell'], 'buy', lambda v: str(v).strip().lower())
        quantity = extract_field(row, ['quantity', 'qty', 'shares', 'filled'], 0, lambda v: parse_float(v, 0))
        price = extract_field(row, ['price'], 0, lambda v: parse_float(v, 0))
        total = extract_field(row, ['amount', 'value', 'total'], 0, lambda v: parse_float(v, 0))
        status = extract_field(row, ['status', 'state'], 'N/A', lambda v: str(v).strip())
        date_val = extract_field(row, ['date', 'time', 'timestamp'], '', lambda v: str(v).strip())
        order_id = extract_field(row, ['order id', 'orderid', 'trade id', 'id'], f"ORD-{i+1}", lambda v: str(v).strip())
        
        # Fallback for total calculation
        if not total and price > 0 and quantity > 0:
            total = price * quantity

        order = {
            'id': order_id,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'total': total,
            'status': status,
            'date': date_val,
            'side': side
        }

        if 'sell' in side:
            sell_orders.append(order)
        else:
            buy_orders.append(order)

    return jsonify({
        'buy': buy_orders,
        'sell': sell_orders,
        'total_buy': len(buy_orders),
        'total_sell': len(sell_orders)
    })

@app.route('/api/orders/symbols')
def get_order_symbols():
    """API endpoint to fetch unique symbols from orders"""
    raw_data = get_sheet_data()
    
    if not raw_data:
        return jsonify({'symbols': []}), 500
    
    symbols = set()

@app.route('/test-company-filter')
def test_company_filter():
    """Test page for company filter component"""
    return render_template('company-filter-test.html')
    
    for row in raw_data:
        keys = {k.lower(): k for k in row.keys()}
        
        # Extract symbol
        symbol = None
        for k in keys:
            if any(x in k for x in ['symbol', 'ticker', 'stock', 'instrument']):
                v = row[keys[k]]
                symbol = str(v).strip() if v is not None else None
                if symbol and symbol != 'N/A':
                    symbols.add(symbol)
                    break
    
    return jsonify({'symbols': sorted(list(symbols))})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5003)
