# Troubleshooting Guide

## HTTP 403 Error on Localhost

If you're getting a "Access to localhost was denied" (HTTP 403) error, try these solutions:

### Solution 1: Install Dependencies First

Make sure all Python packages are installed:

```bash
pip3 install -r requirements.txt
```

Or if using a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Solution 2: Use the Correct URL

Make sure you're accessing:
- `http://127.0.0.1:5000` (recommended)
- `http://localhost:5000` (alternative)

**NOT** `https://localhost:5000` (no HTTPS for local development)

### Solution 3: Check if Flask is Running

1. Make sure the Flask app is actually running. You should see output like:
   ```
   * Running on http://127.0.0.1:5000
   * Debug mode: on
   ```

2. If you don't see this, start the app:
   ```bash
   python3 app.py
   ```

### Solution 4: Try Different Browser

Some browsers have strict localhost security. Try:
- Chrome/Edge
- Firefox
- Safari

### Solution 5: Clear Browser Cache

Sometimes cached security policies cause issues:
- Chrome: Ctrl+Shift+Delete (Cmd+Shift+Delete on Mac)
- Clear cached images and files

### Solution 6: Check Firewall/Security Software

macOS might be blocking localhost access. Check:
- System Preferences → Security & Privacy → Firewall
- Temporarily disable to test

### Solution 7: Use the Run Script

Use the provided run script which handles setup:

```bash
./run.sh
```

### Solution 8: Check Port Availability

Make sure port 5000 is not in use:

```bash
lsof -i :5000
```

If something is using it, either:
- Stop that process, or
- Change the port in `app.py` (line 288) to something else like 5001

### Solution 9: Try Alternative Port

If port 5000 has issues, change it in `app.py`:

```python
app.run(debug=True, host='127.0.0.1', port=8080)
```

Then access: `http://127.0.0.1:8080`

## Common Issues

### "ModuleNotFoundError: No module named 'flask'"
**Solution**: Install dependencies with `pip3 install -r requirements.txt`

### "Connection refused"
**Solution**: Make sure Flask app is running. Start it with `python3 app.py`

### "Unable to fetch data from Google Sheets"
**Solution**: 
- If using public access: Make sure your sheet is publicly accessible
- If using credentials: Check that `credentials.json` exists and the service account has access

### Charts not loading
**Solution**: 
- Check browser console (F12) for JavaScript errors
- Make sure you're accessing via HTTP (not HTTPS)
- Check that `/api/data` endpoint returns data (visit `http://127.0.0.1:5000/api/data`)

