#!/bin/bash

# Function to test HTTP endpoint with fallback methods
test_endpoint() {
    local method="$1"
    local url="$2"
    local expected_status="$3"
    local endpoint_name="$4"

    if command -v curl >/dev/null 2>&1; then
        # Use curl if available
        response=$(curl -s -w "%{http_code}" -X "$method" "$url" 2>/dev/null || echo "000")
        status_code="${response: -3}"
        body="${response%???}"

        if [ "$status_code" = "$expected_status" ]; then
            echo "API_TEST: PASS - $endpoint_name (status: $status_code)"
            return 0
        else
            echo "API_TEST: FAIL - $endpoint_name (expected: $expected_status, got: $status_code)"
            return 1
        fi
    else
        # Fallback using Node.js
        node -e "
        const http = require('http');
        const url = require('url');

        const options = url.parse('$url');
        options.method = '$method';

        const req = http.request(options, (res) => {
            if (res.statusCode == $expected_status) {
                console.log('API_TEST: PASS - $endpoint_name (status: ' + res.statusCode + ')');
                process.exit(0);
            } else {
                console.log('API_TEST: FAIL - $endpoint_name (expected: $expected_status, got: ' + res.statusCode + ')');
                process.exit(1);
            }
        });

        req.on('error', (e) => {
            console.log('API_TEST: FAIL - $endpoint_name (connection error)');
            process.exit(1);
        });

        req.end();
        " 2>/dev/null

        return $?
    fi
}

# Wait for server to be ready
wait_for_server() {
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if test_endpoint "GET" "http://localhost:3000/health" "200" "health check" >/dev/null 2>&1; then
            echo "Server is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done

    echo "Server failed to start within timeout"
    return 1
}

# Start server in background
echo "Starting test server..."
cd /workspace
node test-server.js &
SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"

# Wait for server to be ready
if ! wait_for_server; then
    kill $SERVER_PID 2>/dev/null || true
    echo "API_TEST: FAIL - Server startup failed"
    exit 1
fi

# Run API tests
echo ""
echo "=== RUNNING API INTEGRATION TESTS ==="

test_results=0

# Test health endpoint
test_endpoint "GET" "http://localhost:3000/health" "200" "Health endpoint"
test_results=$((test_results + $?))

# Test chat endpoint
test_endpoint "POST" "http://localhost:3000/api/chat" "200" "Chat endpoint"
test_results=$((test_results + $?))

# Test conversations endpoint
test_endpoint "GET" "http://localhost:3000/api/conversations" "200" "Conversations endpoint"
test_results=$((test_results + $?))

# Test 404 handling
test_endpoint "GET" "http://localhost:3000/api/nonexistent" "404" "404 handling"
test_results=$((test_results + $?))

# Cleanup
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

if [ $test_results -eq 0 ]; then
    echo ""
    echo "API_INTEGRATION: PASS - All endpoints responding correctly"
    exit 0
else
    echo ""
    echo "API_INTEGRATION: FAIL - $test_results test(s) failed"
    exit 1
fi
