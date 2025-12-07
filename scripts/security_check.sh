#!/bin/bash
# Local security check script - mirrors GitHub Actions workflow

set -e

echo "🔒 Running local security checks..."
echo ""

# Check if uv is available, otherwise use standard venv
if command -v uv &> /dev/null; then
    echo "Using uv for package management..."
    uv venv
    uv sync --extra dev
    source .venv/bin/activate
else
    echo "Using standard Python venv (uv not found)..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip setuptools wheel hatchling
    pip install -e ".[dev]"
fi

echo ""
echo "📋 Running Bandit security scan..."
bandit -r data_engineering/ -f json -o bandit-report.json || true

echo ""
echo "📦 Running pip-audit dependency scan..."
pip-audit --format json --output pip-audit-report.json || true

echo ""
echo "🔍 Analyzing results..."

VULN_COUNT=0

# Check Bandit results
if [ -f bandit-report.json ]; then
    HIGH_COUNT=$(python3 -c "
import json
with open('bandit-report.json') as f:
    data = json.load(f)
    results = data.get('results', [])
    count = len([r for r in results if r.get('issue_severity') in ['HIGH', 'MEDIUM']])
    print(count)
" 2>/dev/null || echo "0")

    if [ "$HIGH_COUNT" -gt 0 ]; then
        echo "❌ Found $HIGH_COUNT high/medium severity code issues"
        VULN_COUNT=$((VULN_COUNT + HIGH_COUNT))
    else
        echo "✅ No high/medium severity code issues found"
    fi
else
    echo "⚠️  Bandit report not found"
fi

# Check pip-audit results
if [ -f pip-audit-report.json ]; then
    AUDIT_COUNT=$(python3 -c "
import json
with open('pip-audit-report.json') as f:
    data = json.load(f)
    vulns = data.get('vulnerabilities', [])
    print(len(vulns))
" 2>/dev/null || echo "0")

    if [ "$AUDIT_COUNT" -gt 0 ]; then
        echo "❌ Found $AUDIT_COUNT vulnerable dependencies"
        VULN_COUNT=$((VULN_COUNT + AUDIT_COUNT))
    else
        echo "✅ No vulnerable dependencies found"
    fi
else
    echo "⚠️  pip-audit report not found"
fi

echo ""
if [ "$VULN_COUNT" -gt 0 ]; then
    echo "❌ BLOCKING: Found $VULN_COUNT security issue(s)"
    exit 1
else
    echo "✅ All security checks passed!"
    exit 0
fi

