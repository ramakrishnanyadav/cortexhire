import io

with io.open('final_run_metrics.log', 'r', encoding='utf-16le', errors='ignore') as f:
    lines = f.readlines()

metrics_start = -1
for i, line in enumerate(lines):
    if "FINAL EVALUATION METRICS" in line:
        metrics_start = i - 1
        break

if metrics_start != -1:
    with open('metrics_summary.txt', 'w', encoding='utf-8') as f:
        for line in lines[metrics_start:]:
            f.write(line)
