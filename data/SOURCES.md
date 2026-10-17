# Data provenance and usage

The CSV contains eight annual aggregate counts transcribed from Statistics and Census Service (DSEC) releases published on the Macao Government Information Bureau's NEWS GOV-MO website. Each record is one year and one source market. Original counts are retained without rounding; the spelling “Chinese mainland” is standardized across the two releases.

| Coverage | Official release | Publication date | Source acquisition / recheck |
|---|---|---|---|
| 2024 full year | [Visitor arrivals for December and the whole year of 2024](https://www.gcs.gov.mo/news/detail/en/N25AUB2Zwi) | 21 January 2025 | 6 October / 14 October 2026 |
| 2025 full year | [Visitor arrivals for December and the whole year of 2025](https://www.gcs.gov.mo/news/detail/en/N26AWC98hd) | 23 January 2026 | 6 October / 14 October 2026 |

## Usage permissions

The [NEWS GOV-MO Terms of Use](https://www.gcs.gov.mo/news/terms/en), checked on 14 October 2026, permit noncommercial reproduction of government content with source attribution, acquisition date and accuracy. Their statistical-data section permits calculated figures when sources and calculation methods are identified. Commercial reuse requires written permission; third-party content may have separate conditions. This educational project reproduces only the attributed aggregate numerical counts and presents its own calculated charts. It is not an official publication or a government endorsement. No blanket open-data license is claimed.

## Fields and boundaries

- `year`: full calendar year, 2024 or 2025.
- `source_market`: one of four mutually exclusive groups reported in the releases.
- `visitor_arrivals`: integer arrival visits; repeat visits count again.
- `unit`: always `arrival visits`.
- `source_url`: release supporting that row.

International visitors exclude the Chinese mainland, Hong Kong SAR and Taiwan region. The four groups sum to each published annual total. The data contain no names, contact details, individual travel histories or other personal records.

Derived columns and formulas are documented in the main README and implemented in `src/analyze.py`. Published counts are not forecasts, expenditure, unique customers or evidence of causal effects.
