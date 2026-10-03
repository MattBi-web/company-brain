# Intermodal Rail-Sea SLA Policy (Meridian Intermodal Logistics)

Covers Meridian's internal service levels for door-to-door moves that combine an ocean leg with a rail
dray leg (port → inland rail ramp → final delivery). This is Meridian's core differentiator vs.
pure drayage brokers.

## Transit time SLAs (vessel discharge → inland ramp availability)
| Corridor | Target transit | Breach threshold |
|---|---|---|
| US West Coast port → Chicago ramp | 5 business days | 7 business days |
| US West Coast port → Dallas ramp | 4 business days | 6 business days |
| US East Coast port → Atlanta ramp | 2 business days | 4 business days |
| North Europe port → Milan ramp | 3 business days | 5 business days |
| North Europe port → Warsaw ramp | 4 business days | 6 business days |

"Breach" triggers an automatic SLA credit (see below), not a customer-initiated claim — ops should flag
breaches proactively.

## SLA credit schedule
- 1 day over breach threshold: 5% of the rail-leg charge credited.
- 2–3 days over: 10% credited.
- 4+ days over: 20% credited, plus a root-cause note logged in the lane's ops record.

## Exclusions (SLA does not apply)
- Customs holds (any authority) — outside Meridian's control.
- Declared port congestion advisories (see `port_congestion_advisory.md`) — the advisory period is
  excluded from the transit-time clock, not just extended.
- Rail carrier network-wide service disruptions (strikes, embargoes) communicated via carrier notice.
- Cargo requiring re-weighing, re-documentation, or hazmat re-certification due to customer-side errors.

## Visibility requirement
Every leg must emit a milestone event (vessel discharge, rail gate-in, rail gate-out, ramp availability)
to the tracking feed within 2 hours of occurrence. A lane missing 2+ consecutive milestones for the same
shipment should be escalated to Ops regardless of whether the SLA clock has breached yet — missing
milestones are usually a earlier warning sign than a timer running out.
