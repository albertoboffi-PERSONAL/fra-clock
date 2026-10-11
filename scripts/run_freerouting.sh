#!/bin/zsh
# usage: scripts/run_freerouting.sh <in.dsn> <out.ses> <log> [max_passes]
cd "$(dirname "$0")/.."
J=/opt/homebrew/opt/openjdk/bin/java
nohup $J -jar tools/freerouting/freerouting-2.5.0.jar -de "$1" -do "$2" \
  --router.autorouter.max_passes=${4:-100} --router.autorouter.ignore_net_classes=fixed \
  --router.fanout.enabled=false --gui.enabled=false \
  --profile.allow_telemetry=false --usage_and_diagnostic_data.disable_analytics=true > "$3" 2>&1 &
echo "started $!"
