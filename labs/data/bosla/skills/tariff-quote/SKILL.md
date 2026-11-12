---
name: tariff-quote
description: Quote berth hire for a vessel and a number of days, with the feeder discount and the dangerous goods surcharge, citing the circulars in force.
---
# Tariff quote

1. Find the vessel's gross tonnage with `get_vessel` (never guess it).
2. Ask, or read from the request, whether the cargo includes dangerous goods.
3. Call `compute_dues(gross_tonnage, days, dangerous_goods)`. Do not do the arithmetic yourself.
4. Answer with the amount in SAR and cite TC-07 (rate and minimum) and TC-04 (discount, surcharge).
5. If the agent asks how the number was reached, read `reference.md` in this skill.
