"""Small hand-labeled (question -> expected source document) set used by
both `company-brain eval` and the pytest retrieval test. Not meant to be a
rigorous benchmark — it's a fast sanity check that a change to chunking,
fusion weights, or the graph boost hasn't silently broken retrieval."""

EVAL_SET: list[tuple[str, str]] = [
    ("How many free demurrage days do we get on Transpacific imports to the US West Coast?", "demurrage_detention_policy"),
    ("What's the difference between demurrage and detention?", "demurrage_detention_policy"),
    ("Which Incoterm transfers risk at the port of loading but still has the seller paying freight?", "incoterms_glossary"),
    ("What temperature range can a 20ft reefer container hold?", "container_types_reference"),
    ("What's the SLA transit time from a US West Coast port to the Chicago rail ramp?", "intermodal_sla_policy"),
    ("What's causing the current congestion at Rotterdam?", "port_congestion_advisory"),
    ("What should a support agent check before offering a customer an SLA credit?", "customer_escalation_playbook"),
    ("What combined free-time pool does Meridian's Maersk contract give on Transpacific reefer?", "carrier_contract_summary_maersk"),
    ("Roughly what does a 40HC from Shanghai to Rotterdam cost on Maersk before surcharges?", "ocean_fcl_rate_card"),
]
