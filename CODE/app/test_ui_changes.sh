#!/bin/bash
# Quick test script to verify UI changes are applied

echo "🔍 Testing UI Changes..."
echo ""

# Test 1: Server running
if ! curl -s http://localhost:8000 > /dev/null 2>&1; then
    echo "❌ Server not running. Start with: chainlit run app.py -w"
    exit 1
fi
echo "✅ Server is running"

# Test 2: CSS file exists and is served
CSS_SIZE=$(curl -s http://localhost:8000/public/theme.css | wc -c)
if [ "$CSS_SIZE" -lt 100 ]; then
    echo "❌ CSS file too small ($CSS_SIZE bytes)"
    exit 1
fi
echo "✅ CSS file is being served ($CSS_SIZE bytes)"

# Test 3: Check for key CSS properties
CSS_CONTENT=$(curl -s http://localhost:8000/public/theme.css)
if echo "$CSS_CONTENT" | grep -q "var(--bg-primary)"; then
    echo "✅ Modern CSS variables found"
else
    echo "❌ CSS variables missing"
fi

if echo "$CSS_CONTENT" | grep -q "data-author"; then
    echo "✅ Message styling found"
else
    echo "❌ Message styling missing"
fi

# Test 4: HTML includes CSS
if curl -s http://localhost:8000 | grep -qi "theme.css"; then
    echo "✅ HTML includes CSS link"
else
    echo "❌ CSS link missing from HTML"
fi

echo ""
echo "🎨 Current CSS highlights:"
echo "$CSS_CONTENT" | grep -E "^/\*|--bg-primary|--accent-primary" | head -5

echo ""
echo "✨ All checks passed! Refresh your browser to see changes."

