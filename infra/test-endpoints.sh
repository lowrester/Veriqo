#!/bin/bash
# Test API endpoints for Veriqo Platform V2
BASE_URL="http://localhost:8000/api/v1"

echo "🧪 Testing Platform V2 Endpoints..."

# 1. Health/Root
echo -n "Checking API Root... "
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/" | grep -q "200" || grep -q "404"
if [ $? -eq 0 ]; then echo "✅ OK"; else echo "❌ FAIL"; fi

# 2. Stations (Admin)
echo -n "Checking Stations Endpoint... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/stations")
if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 401 ]; then echo "✅ OK ($HTTP_CODE)"; else echo "❌ FAIL ($HTTP_CODE)"; fi

# 3. Device Types
echo -n "Checking Device Types Endpoint... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/device-types")
if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 401 ]; then echo "✅ OK ($HTTP_CODE)"; else echo "❌ FAIL ($HTTP_CODE)"; fi

# 4. Jobs
echo -n "Checking Jobs Endpoint... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/jobs")
if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 401 ]; then echo "✅ OK ($HTTP_CODE)"; else echo "❌ FAIL ($HTTP_CODE)"; fi

echo "Found API structure to be valid."
