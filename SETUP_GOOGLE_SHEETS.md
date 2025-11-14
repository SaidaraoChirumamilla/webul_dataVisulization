# Setting Up Google Sheets Access

The error "Unable to fetch data from Google Sheets" means the app cannot access your sheet. You have two options:

## Option 1: Make Sheet Public (Easiest - No Setup Required)

### Steps:
1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/1pzKHZ5xPT6oMMQ4wNNGL-Z1I-81qa_MtjI_seL5M1Ug
2. Click the **"Share"** button (top right)
3. Click **"Change to anyone with the link"**
4. Set permission to **"Viewer"**
5. Click **"Done"**

That's it! The app will now be able to fetch data.

**Note:** This makes your sheet viewable by anyone with the link. If your data is sensitive, use Option 2 instead.

---

## Option 2: Use Google Sheets API (More Secure)

This method uses API credentials so your sheet can remain private.

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Enter a project name (e.g., "Webull Visualization")
4. Click **"Create"**

### Step 2: Enable APIs

1. In the search bar, type **"Google Sheets API"**
2. Click on **"Google Sheets API"**
3. Click **"Enable"**
4. Repeat for **"Google Drive API"** (search and enable it)

### Step 3: Create Service Account

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"Service Account"**
3. Enter a name (e.g., "webull-visualization")
4. Click **"Create and Continue"**
5. Skip optional steps, click **"Done"**

### Step 4: Create and Download Key

1. Click on the service account you just created
2. Go to **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**
4. Select **"JSON"** format
5. Click **"Create"**
6. A JSON file will download - **save it as `credentials.json`** in your project folder

### Step 5: Share Sheet with Service Account

1. Open the downloaded `credentials.json` file
2. Find the `"client_email"` field (looks like: `webull-visualization@project-name.iam.gserviceaccount.com`)
3. Copy that email address
4. Open your Google Sheet
5. Click **"Share"**
6. Paste the service account email
7. Set permission to **"Viewer"**
8. Uncheck **"Notify people"** (service accounts don't need notifications)
9. Click **"Share"**

### Step 6: Place Credentials File

1. Move `credentials.json` to your project folder:
   ```
   /Users/saidaraochirumamilla/webull visulization/credentials.json
   ```

### Step 7: Run the App

```bash
# Deactivate public access mode
unset USE_PUBLIC_ACCESS

# Or just run (it will try credentials first)
source venv/bin/activate
python app.py
```

---

## Quick Test

After setting up, test if it works:

```bash
# Test public access
curl "https://docs.google.com/spreadsheets/d/1pzKHZ5xPT6oMMQ4wNNGL-Z1I-81qa_MtjI_seL5M1Ug/export?format=csv&gid=1100303320" | head -5
```

If you see CSV data (not HTML), it's working!

---

## Troubleshooting

### "Credentials file not found"
- Make sure `credentials.json` is in the project root folder
- Check the filename is exactly `credentials.json` (not `credentials.json.json`)

### "Permission denied" or "Access denied"
- Make sure you shared the sheet with the service account email
- Check the service account email in `credentials.json` matches what you shared

### "API not enabled"
- Go back to Google Cloud Console
- Make sure both "Google Sheets API" and "Google Drive API" are enabled

### Still getting errors?
- Check the terminal output when running the app - it will show detailed error messages
- Make sure your sheet has data (at least headers and some rows)

