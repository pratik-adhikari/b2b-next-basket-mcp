# Account Identity Notes

The demo dataset stores account identifiers in the `client_name` field. Local inspection is intentionally limited to counts and bounded identifier samples; it does not print full histories or raw dataset records.

Current dataset characteristics:

- Total records: 169.
- Numeric-only `client_name` values: 165.
- Non-numeric `client_name` values: 4.
- The non-numeric demo identifiers are `hardware_store`, `nexus_lab_solutions`, `retail_hardware_store`, and `retail_supermarket`.
- The dataset does not provide a full CRM-style account display-name table.

Because the dataset does not contain reliable real account display names, the MCP layer generates safe demo labels from local signals:

- `Nexus Lab Solutions` for the known `nexus_lab_solutions` demo account.
- `Grocery Account 292` for numeric accounts whose predicted item patterns look grocery-related.
- `Lab Account 123` for numeric accounts whose predicted item patterns look lab-supply-related.
- `Account 123` when no more specific safe segment label is available.

These labels are safe inferred demo labels, not real company names. They are designed to make the live demo readable without inventing proprietary customer identities.

In production, this should be replaced by a CRM/ERP metadata mapping that joins model client IDs to approved account display names, territories, owners, segments, and contact rules. Any customer contact should verify the generated demo label against CRM before outreach.
