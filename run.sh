#!/bin/bash

# Install dependencies if needed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Set public access mode (comment out if using credentials.json)
export USE_PUBLIC_ACCESS=true

# Run the Flask app
echo "Starting Flask application..."
echo "Open your browser to: http://127.0.0.1:5000"
python3 app.py

