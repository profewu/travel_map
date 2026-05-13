# Live booking-site spot check, 2026-05-12

Scope: one Chrome-based spot check per site, not a full refresh. The shared sample target was `2026-06-25` to `2026-06-26`, Eniwa / nearby, `3 adults + 1 child age 10`, `1 room`, using the existing non-logged-in Chrome session.

## Summary

| Site | Live result | Decision impact |
| --- | --- | --- |
| Agoda | Submitted the existing Agoda property search for Fairfield by Marriott Hokkaido Eniwa. URL retained `selectedproperty=31562792`, `checkIn=2026-06-25`, `rooms=1`, `adults=3`, `children=1`, `childages=10`, but the page showed `0個搜尋結果`. | Confirms the master report should not show Agoda as a dated price source. Keep as property/search entry only. |
| Booking.com | Folks House opened as a dated property room page: `6 月 25 日（四） — 6 月 26 日（五）`, `3 位成人 · 1 位孩童 · 1 間房`. Visible room option showed `1 晚、3 位成人、1 位孩童 TWD 3,998`. | Booking remains the strongest saved room-level evidence, but currency is live TWD while stored report used JPY-equivalent URL price evidence. |
| Hotels.com | Report row opened to Randor Hotel Sapporo Heritage, with visible dates `Tue, Jun 30 - Wed, Jul 1`, `4 travelers, 1 room`. | Confirms the row is a date mismatch for the 2026-06-25 Eniwa section. |
| Expedia | Report row opened to Randor Hotel Sapporo Heritage, with visible dates `Sun, Jun 28 - Mon, Jun 29`, `4 travelers, 1 room`; visible prices included `$59`, `$49`, `$60`, `$62`, `$223`. | Confirms the row is a date/location mismatch for the 2026-06-25 Eniwa section and should not be treated as that night's price. |
| trivago | Dated metasearch page loaded with `6月25日 - 6月26日`, `4 位旅客，1 間客房`; Minn Chitose appeared with `Hotels.com 我們的最低價 TWD 4,652`, and other Eniwa-area cards included Folks House `TWD 3,635`. | Confirms trivago can show dated metasearch prices, but it is still a metasearch reference, not a final child-age-validated booking quote. |

## Evidence Files

- `live-spotcheck-2026-05-12/agoda.png`
- `live-spotcheck-2026-05-12/agoda-after-search.png`
- `live-spotcheck-2026-05-12/hotels-com.png`
- `live-spotcheck-2026-05-12/expedia.png`
- `live-spotcheck-2026-05-12/trivago.png`
- `live-spotcheck-2026-05-12/spotcheck-results.json`
