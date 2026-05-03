# NVMe QoS Analysis Skill

## When Used

Use this skill when the user asks about p99 latency, saturation, IOPS, bandwidth, queue depth, NAND penalties, or design readiness.

## Input

- simulator summary
- workload-level latency and saturation results
- device configuration
- deterministic recommendations

## Output

Return:

- answer
- evidence
- next_action
- recommendation
- decision

## Rules

- Mention exact deterministic metrics.
- Prioritize workloads with highest p99 latency and highest saturation.
- Treat high p99 latency as a QoS risk.
- Clearly state whether the SSD profile is ready for customer review.