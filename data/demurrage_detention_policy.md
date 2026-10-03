# Demurrage & Detention Policy (Meridian Intermodal Logistics)

Demurrage and detention are two different charges and are frequently confused by customers — this
document is the canonical internal reference for support agents and the Company Brain's grounding.

## Definitions
- **Demurrage**: charged by the carrier/terminal for the container sitting *inside the port/terminal*
  past the free time, whether full or empty.
- **Detention**: charged by the carrier for the container sitting *outside the port* (at the customer's
  warehouse or yard) past the free time, whether full or empty, until it is returned.

## Standard free time by lane group (calendar days, import, dry containers)
| Lane group | Demurrage free time | Detention free time |
|---|---|---|
| Transpacific (Asia → US West Coast) | 4 days | 5 days |
| Transpacific (Asia → US East Coast, all-water) | 5 days | 5 days |
| Asia → North Europe | 7 days | 7 days |
| Intra-Mediterranean | 5 days | 5 days |
| Asia → South America | 10 days | 7 days |

Reefer containers get **2 fewer free days** than dry on every lane group above, due to terminal plug
availability constraints.

## Combined free time
Select carriers (confirm per contract — see `carrier_contract_summary_*` docs) offer a **combined/merged
free time pool** instead of split demurrage+detention, e.g. "10 days combined" instead of "5+5". Combined
pools are more forgiving for customers whose warehouse appointment slips, since days not used on
demurrage roll into detention.

## Port congestion extensions
During a declared **port congestion advisory** (see `port_congestion_advisory.md`), Meridian automatically
requests a free-time extension from the carrier on affected lanes. This is a request, not a guarantee —
customers should still be advised to pull containers as early as possible.

## Escalation
If a customer disputes a demurrage/detention invoice, the support agent should pull the container's
full event history (gate-in, gate-out, empty-return) before escalating — most disputes are resolved by
showing the actual gate timestamps rather than negotiating the charge itself.
