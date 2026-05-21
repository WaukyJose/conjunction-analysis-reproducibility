cat > docs/audit_notes/analytical_context_mismatch_note.md <<'EOF'
# Audit Note: Analytical Context Mismatch in Intra-sentential Output Selection

During the audit of the intra-sentential conjunction results, an apparent inconsistency was identified in the comparison table. The reported values showed unusually large differences, which prompted a targeted check of the underlying files, formulas, and output provenance.

The issue was not an AI hallucination in the usual sense. The figures were not invented, nor were the files or formulas fabricated. Instead, the problem was an analytical context mismatch, specifically a file-selection error within a layered computational workflow.

The audit showed that the table had been generated from the broad intra-sentential output file:

```text
v2_intrasentential_full_text_indices.csv
