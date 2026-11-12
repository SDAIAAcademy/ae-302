---
name: booking-change
description: Amend or cancel a booking for the agent who owns it, with the fee that applies and the cases that need the duty harbour master's approval.
---
# Booking change

1. Read the booking with `get_booking(booking_id, agent_code)`. If it fails, ask the agent to check both.
2. Say the fee before you write: amendment SAR 500 if less than 2 days before arrival, otherwise free;
   cancellation free 3 or more days before arrival, otherwise 25% of berth hire (TC-06).
3. A change that involves dangerous goods, leaves under-keel clearance below 1.0 m, or moves dues by more
   than SAR 10,000 needs the duty harbour master's approval (TC-06). Say so; do not write it yourself.
4. Write only after the agent has asked for that exact change: `amend_booking` or `cancel_booking`.
