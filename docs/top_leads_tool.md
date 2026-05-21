# Top Reorder Leads Tool

`get_top_reorder_leads` exists so a local n8n/Ollama agent can answer higher-level sales questions such as:

```text
Tell me the top 10 leads with reasoning.
```

The local LLM should call this MCP tool for "top leads" or "best reorder opportunities" questions. The LLM should not rank customers itself. The MCP server ranks leads with a transparent demo heuristic over the existing backend/model outputs.

## Ranking Method

The tool scans a bounded set of demo clients, generates each client's next-basket prediction with the existing local backend, converts predicted tokens into readable items and timing, then scores the opportunity.

The score is heuristic:

- timing signal present
- near-term reorder timing
- predicted readable items available
- enough sample history available
- penalty when no clear item prediction is available

This is not a calibrated probability or confidence score.

## Safety

The response is recommendation-only:

- no automatic customer contact
- no automatic order placement
- human review is required before any customer action
- no chain-of-thought is exposed

## Example Input

```json
{
  "limit": 10,
  "include_evidence": true,
  "max_clients_to_scan": 30
}
```

## Example Output Summary

```json
{
  "ok": true,
  "tool": "get_top_reorder_leads",
  "requested_limit": 10,
  "scanned_clients": 31,
  "returned_leads": 10,
  "ranking_method": "demo_rule_based_over_model_outputs",
  "leads": [
    {
      "rank": 1,
      "client_id": "nexus_lab_solutions",
      "score": 100,
      "expected_timing": "next order after 1 week(s)",
      "likely_items": ["solv acetone tech", "kimwipes large", "waste carboy 10"],
      "recommended_action": "Prepare a replenishment offer...",
      "reason_codes": [
        "TIMING_SIGNAL_PRESENT",
        "NEAR_TERM_REORDER_SIGNAL",
        "PREDICTED_ITEMS_AVAILABLE",
        "SUFFICIENT_HISTORY_AVAILABLE"
      ],
      "evidence_summary": "Concise evidence summary without chain-of-thought.",
      "limitations": [
        "Ranking is based on demo heuristics over model outputs.",
        "No calibrated probability or confidence score is exposed.",
        "Recommendations require human review before customer contact.",
        "The ranking uses local sample histories available in the demo dataset."
      ]
    }
  ],
  "safety": {
    "recommendation_only": true,
    "requires_human_approval": true,
    "can_contact_customer_automatically": false,
    "can_place_order_automatically": false
  }
}
```
