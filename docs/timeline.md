# EU AI Act timeline used by `aiact`

Checked on 22 November 2026 against Regulation (EU) 2024/1689 (the AI Act) and Regulation (EU) 2026/1744
(the Digital Omnibus on AI). The Omnibus was published in the Official Journal on 24 July 2026 and entered
into force on 27 July 2026.

| Constant in `rules.py` | Date | Applies to | Basis |
|---|---|---|---|
| `PROHIBITIONS` | 2 Feb 2025 | Art. 5 prohibited practices; Art. 4 AI literacy | Art. 113(a) |
| `GPAI` | 2 Aug 2025 | Chapter V obligations for general-purpose AI models; governance; penalties | Art. 113(b) |
| `TRANSPARENCY` | 2 Aug 2026 | Art. 50 transparency obligations | Art. 113 (unchanged by the Omnibus) |
| `MARKING_LEGACY` | 2 Dec 2026 | Art. 50(2) marking and detection for generative systems placed on the market before 2 Aug 2026 | Omnibus transitional period |
| `NEW_PROHIBITIONS` | 2 Dec 2026 | Prohibition of AI systems generating non-consensual intimate imagery or child sexual abuse material | Omnibus |
| `GPAI_LEGACY` | 2 Aug 2027 | GPAI models placed on the market before 2 Aug 2025 | Art. 111(3) |
| `ANNEX_III` | 2 Dec 2027 | High-risk systems listed in Annex III (was 2 Aug 2026) | Omnibus |
| `ANNEX_I` | 2 Aug 2028 | High-risk AI in products under Annex I Union harmonisation law (was 2 Aug 2027) | Omnibus |

## Other Omnibus changes reflected here

- **AI literacy (Art. 4)** now requires providers and deployers to *take measures to support* the AI
  literacy of staff operating AI systems, instead of *ensuring a sufficient level*. The kit keeps it as an
  obligation that applies to both roles and asks for a training plan as evidence.
- The Omnibus fixed the high-risk dates. It dropped the Commission's proposed mechanism linking them to
  the readiness of standards.

## Not modelled

- Simplified documentation and penalty caps for SMEs and small mid-caps. The kit lists the obligations;
  how much documentation is proportionate is for the team to decide.
- Processing special categories of personal data for bias detection, which the Omnibus extended to all AI
  systems under a strict-necessity test. This is a permission, not a duty.
- Member-state implementation (competent authorities, sandboxes) and sector rules that apply alongside
  the AI Act.

## Sources

- Regulation (EU) 2024/1689: https://eur-lex.europa.eu/eli/reg/2024/1689/oj
- Regulation (EU) 2026/1744 (Digital Omnibus on AI): https://eur-lex.europa.eu/eli/reg/2026/1744/oj
- European Commission, Code of Practice on Transparency of AI-Generated Content and the Article 50 guidelines: https://digital-strategy.ec.europa.eu/en/faqs/code-practice-transparency-ai-generated-content
