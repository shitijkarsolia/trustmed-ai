#!/bin/bash
# Script to verify CSS is loading and show key styles

echo "=== Checking Server Status ==="
if curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo "✅ Server is running"
else
    echo "❌ Server not responding"
    exit 1
fi

echo ""
echo "=== Checking CSS File Content (first 30 lines) ==="
curl -s http://localhost:8000/public/theme.css | head -30

echo ""
echo "=== Checking HTML includes CSS ==="
curl -s http://localhost:8000 | grep -i "theme.css" || echo "❌ CSS link not found in HTML"

echo ""
echo "=== Checking CSS MIME Type ==="
CONTENT_TYPE=$(curl -s -I http://localhost:8000/public/theme.css | grep -i "content-type" | head -1)
if echo "$CONTENT_TYPE" | grep -qi "text/css"; then
    echo "✅ Correct MIME type: $CONTENT_TYPE"
else
    echo "❌ Wrong MIME type: $CONTENT_TYPE"
fi

echo ""
echo "=== Checking CSS File Size ==="
SIZE=$(curl -s -I http://localhost:8000/public/theme.css | grep -i "content-length" | awk '{print $2}' | tr -d '\r')
echo "CSS file size: $SIZE bytes"

echo ""
echo "=== Key CSS Properties Check ==="
CSS_CONTENT=$(curl -s http://localhost:8000/public/theme.css)
if echo "$CSS_CONTENT" | grep -q "var(--bg-primary)"; then
    echo "✅ CSS variables found"
else
    echo "❌ CSS variables not found"
fi

if echo "$CSS_CONTENT" | grep -q "data-author"; then
    echo "✅ Message selectors found"
else
    echo "❌ Message selectors not found"
fi
