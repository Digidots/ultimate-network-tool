"""
List all Flask routes to debug 404 issues
"""
from app import app

print("=" * 60)
print("REGISTERED FLASK ROUTES:")
print("=" * 60)

for rule in app.url_map.iter_rules():
    methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    print(f"{rule.rule:40s} {methods:20s} -> {rule.endpoint}")

print("=" * 60)
