# Customer Escalation Playbook — Shipment Delays & Charge Disputes (Meridian Intermodal Logistics)

For customer-ops agents handling an inbound delay complaint or a demurrage/detention charge dispute.
Follow in order — do not skip to a credit offer before step 3.

## Step 1 — Establish what actually happened
Pull the shipment's full milestone feed (vessel discharge, rail gate-in/out, empty-return) before
replying to the customer. Most "the carrier is lying to me" complaints are resolved once the agent has
the actual gate timestamps in hand, not by negotiating.

## Step 2 — Check for an active exclusion
Before offering any SLA credit or fee waiver, check whether an active port congestion advisory or a
carrier network disruption notice covers the shipment's port and date window (see
`port_congestion_advisory.md`, `intermodal_sla_policy.md` exclusions section). If an exclusion applies,
say so plainly to the customer — it is not a "no", it is "here's why the clock didn't run, and here's
what we're still doing for you."

## Step 3 — Apply the right policy, don't improvise
- Transit-time complaint → `intermodal_sla_policy.md` SLA credit schedule.
- Demurrage/detention invoice dispute → `demurrage_detention_policy.md`.
- Confusion about who is responsible for insurance/risk at a given leg → `incoterms_glossary.md`.
Agents should never offer a discretionary credit outside these schedules without supervisor sign-off —
ad hoc credits are the top driver of inconsistent customer treatment across the book.

## Step 4 — Set expectations for what happens next
Give the customer a concrete next milestone and a time window, not a vague "we're on it." If the
shipment is inside an active congestion advisory, say when the advisory is next reviewed (every 48
hours) rather than promising a fixed resolution date you cannot control.

## Step 5 — Log the root cause
Every escalation gets a one-line root-cause tag (carrier delay / congestion / documentation error /
customer-side error / Meridian ops error) in the lane's ops record. This is what lets Ops spot a lane
that is breaching SLA repeatedly rather than treating each case as isolated.

## Tone guidance
Lead with the facts (milestones, policy, exclusion status) before the apology. A customer who has been
shipping for years will trust a precise answer more than a sympathetic one — reserve the warmth for
step 4's expectation-setting, not for burying the actual answer.
