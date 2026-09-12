#!/bin/zsh
set -euo pipefail
command -v neo4j >/dev/null || { echo "Neo4j Community is not installed. The app will use its SQLite graph system-of-record. Install with: brew install neo4j"; exit 1; }
conf_dir="${NEO4J_CONF:-/opt/homebrew/etc/neo4j}"
conf_file="$conf_dir/neo4j.conf"
if [[ ! -f "$conf_file" ]] || ! grep -q '^dbms.usage_report.enabled=false' "$conf_file" || ! grep -q '^dbms.fleet_manager.enabled=false' "$conf_file" || ! grep -q '^server.fleet_discovery.enabled=false' "$conf_file"; then
  echo "Refusing to start: $conf_file must explicitly disable usage reporting, Fleet Manager, and Fleet discovery."
  echo "Add: dbms.usage_report.enabled=false"
  echo "Add: dbms.fleet_manager.enabled=false"
  echo "Add: server.fleet_discovery.enabled=false"
  exit 1
fi
echo "Starting local Neo4j. Configure it to listen on 127.0.0.1 only."
exec neo4j console
