# Task 06 — Razorpay Invoicing

Parent: [../PRD.md](../PRD.md) · Depends on: [05_razorpay_payment_links](./05_razorpay_payment_links.md), [04_whatsapp_webhook](./04_whatsapp_webhook.md)

## Goal

Close the loop with zero manual paperwork: on payment, autonomously generate a GST-compliant invoice and push it back to the buyer on WhatsApp.

## Scope

- Extend `backend/app/services/razorpay_client.py` with `create_invoice(deal: DealState) -> Invoice` (calls `/v1/invoices`), including GST-relevant line items (item, qty, unit price).
- Wire the `issue_invoice` node (Task 03 stub) to call `create_invoice` once `status == Paid`, store the resulting invoice PDF URL on `DealState`.
- After invoice creation, call `WhatsAppService.send_message` (Task 04) with the invoice PDF link, then transition `status` to `Dispatched` (dispatch itself stays simulated per STORY.md §7/§8).
- Trigger this flow from the `payment_link.paid` webhook handler added in Task 05 (i.e., webhook → `Paid` → `issue_invoice` → `Dispatched`, run synchronously or via a background task).

## Out of Scope

- Real logistics/freight integration (STORY.md §8 Future Scope).
- Invoice PDF rendering/customization beyond what Razorpay's API returns.

## Acceptance Criteria

- [x] A `payment_link.paid` webhook event results in exactly one invoice created via Razorpay's test-mode API with correct line items and amount.
- [x] The buyer receives one WhatsApp message containing the invoice PDF link.
- [x] `DealState.status` ends at `Dispatched` after this flow, with no manual steps.

## Tests

- Unit test `create_invoice` payload construction against mocked HTTP layer (correct line items, GST fields, amount).
- Integration test: mocked `payment_link.paid` webhook → invoice created → WhatsApp message sent → state == `Dispatched`, all with mocked external services.
- Failure-path test: invoice API failure should not silently mark the deal `Dispatched` (state should reflect the failure for retry/inspection).
