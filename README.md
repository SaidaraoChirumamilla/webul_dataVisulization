# Webull Visualization Dashboard

A Flask web application that fetches data from Google Sheets and visualizes it using interactive charts.

## Features

- **Monthly Cash Flow Analysis**: Bar chart showing incoming/outgoing cash with net flow line
- **Yearly Transfer Volume Comparison**: Stacked bar chart comparing yearly transfers
- **Transaction Status Distribution**: Donut chart showing transaction status breakdown
- **Transfer Volume by Type**: Horizontal bar chart showing transfer volumes by type

## Setup Instructions

### Option 1: Using Public Google Sheet (Easiest)

If your Google Sheet is publicly accessible (or you want to make it public):

1. **Make your sheet public** (optional):
   - Open your Google Sheet
   - Click "Share" → "Change to anyone with the link"
   - Set permission to "Viewer"

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run with public access**:
   ```bash
   export USE_PUBLIC_ACCESS=true
   python app.py
   ```
   
   Or on Windows:
   ```cmd
   set USE_PUBLIC_ACCESS=true
   python app.py
   ```

The application will automatically fetch data using CSV export (no credentials needed).

### Option 2: Using Google Sheets API (More Secure)

For private sheets or better performance:

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Google Sheets API Setup**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Sheets API and Google Drive API
   - Create credentials (Service Account):
     - Go to "Credentials" → "Create Credentials" → "Service Account"
     - Create a service account and download the JSON key file
     - Save it as `credentials.json` in the project root

3. **Share Google Sheet with Service Account**:
   - Open your Google Sheet
   - Click "Share" button
   - Add the service account email (found in `credentials.json` as `client_email`)
   - Give it "Viewer" permissions

4. **Run the Application**:
   ```bash
   python app.py
   ```

The application will try authenticated access first, then fall back to public access if credentials are not found.

### Update Sheet Configuration

The spreadsheet ID is already configured in `app.py` from your URL. If you need to change it, update:
- `SPREADSHEET_ID` in `app.py`
- `WORKSHEET_GID` if using a specific worksheet

The application will be available at `http://localhost:5000`

## Data Format

Your Google Sheet should have columns like:
- `Date` (format: YYYY-MM-DD)
- `Incoming` (numeric)
- `Outgoing` (numeric)
- `Status` (Completed, Rejected, Canceled)
- `Type` (Ach Incoming, Ach Outgoing, Debit Card Incoming, etc.)
- `Amount` (numeric)

The column names are case-insensitive and the code will try to match variations.

## Troubleshooting

- **"Credentials file not found"**: Make sure `credentials.json` is in the project root
- **"Unable to fetch data"**: Check that the service account has access to the sheet
- **Empty charts**: Verify your sheet data matches the expected column names

## Alternative: Public Sheet Access

If your sheet is public, you can modify the code to use public access without credentials. However, for better security, using service account credentials is recommended.

