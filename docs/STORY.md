# Sauda: The Autonomous B2B Deal-Maker
Razorpay Buildathon 2026 Submission - Track 01: AI Growth and Agentic Commerce

## 1. The Authentic Problem (The Founder Story)
My mother runs a B2B Medical Supplies Distribution business. She supplies surgical equipment to hospitals and clinics on a commission basis. In the Indian B2B market, the golden rule is "Speed to Lead" -- the first distributor to reply with an accurate quote wins the hospital's order.

However, her daily reality is an operational bottleneck. She spends half her day at the godown, physically dispatching consignments, or on her phone booking Rapido and Porter trucks based on the consignment size. Because she is consumed by logistics, hospital procurement officers who send unstructured WhatsApp messages (e.g., "Need 500 surgical staplers to Pune, best rate?") are left waiting.

If she takes four hours to manually check stock, calculate her margins, and draft a quote, the hospital has already sourced it elsewhere. She loses her commission, and Razorpay loses the transaction volume. The market needs a way to go from one WhatsApp message to a final closed deal, in minutes, without manual intervention.

## 2. The Solution: Sauda
Sauda is an autonomous AI sales agent that acts as a 24/7 B2B deal closer. It intercepts inbound WhatsApp queries when my mother is busy. It checks her live inventory, reads product specificities, negotiates based on strict margin rules, and instantly closes the deal by generating a Razorpay Payment Link. Once paid, it auto-generates and sends a GST invoice directly in the chat.

For the merchant (my mom), it means zero missed revenue. For Razorpay, it brings conversational, unstructured B2B commerce onto their gateway.

## 3. Track 01 Alignment
This project directly addresses the core mandates of Track 01:
*   Grow Merchant Revenue: Automates the sales funnel, preventing lead drop-off due to human delay.
*   Make them Sellable to AI Buyers: Implements a machine-readable API endpoint so hospital procurement AI agents can fetch quotes and pay without human conversational overhead.
*   Explainable, Bounded, and Gated: AI reasoning is strictly decoupled from financial execution using deterministic Python guardrails, backed by enterprise-grade observability.

## 4. Architecture and Tech Stack
The system is built for low latency, high traceability, and zero cognitive load for the merchant.

### Backend (The Engine and Observability)
*   Framework: FastAPI (Python) for asynchronous webhook handling.
*   Agentic Orchestration: LangGraph. Manages the state machine (Extract Intent -> Check Inventory -> Negotiate -> Await Payment -> Issue Invoice -> Dispatch).
*   LLM: Groq (qwen/qwen3.8-27b) for natural language understanding and generation.
*   Guardrails: Pydantic models to strictly enforce data types and margin boundaries.
*   Observability: Arize Phoenix. Implements OpenTelemetry tracing across all LangGraph nodes to provide an immutable, cryptographic-style audit trail of every LLM span, context retrieval, and guardrail execution.

### Database (The Inventory)
A local mock_inventory.csv acting as the godown's source of truth.
Columns: product_id, item_name, stock_qty, base_price, notes.
The "notes" column provides the LLM with grounded context (e.g., "Nitrile, Powder-free, Latex-free") so it can answer hospital queries accurately without hallucinating specifications.

### Frontend (The Gamified UI)
*   Framework: React (Next.js or Vite) with Tailwind CSS.
*   Animation: Framer Motion for sprite routing.
*   Design System: Retro 8-bit / Pixel art style (inspired by Stardew Valley).

## 5. The Conversational Flow and LLM Template
To ensure traceability without annoying the buyer, the LLM is instructed to follow a lightweight, conversational template. It must gather basic logistical data before locking in the quote.

### The System Prompt
You are Sauda, an elite B2B sales agent representing a medical supplies distributor. Your goal is to negotiate bulk orders with hospital procurement staff over WhatsApp.

CONSTRAINTS AND GUARDRAILS (CRITICAL):
1. NO SLA PROMISES: You MUST NOT promise delivery times (e.g., "delivery in 10 mins"). State only: "We will dispatch via our logistics partner post-payment."
2. NO WARRANTY PROMISES: You MUST NOT offer warranties or guarantees.
3. INVENTORY AWARENESS: You will be provided with the current stock. If the request exceeds stock, apologize and offer only what is available. Do not invent stock.
4. THE TEMPLATE: You must subtly collect traceability data. Do not interrogate. Weave these into the conversation naturally:
   - Step 1: Confirm the item and available quantity based on the database.
   - Step 2: Ask for the Hospital Name and Delivery PIN Code (state it is needed to verify logistics).
   - Step 3: Negotiate the price based on the approved parameters.
   - Step 4: Confirm the deal, state that a Razorpay link is being generated, and assure them a GST invoice will be auto-generated and sent here upon payment.
5. PRICING: Do not do math. Propose a final price based ONLY on the approved variables passed to you in the system state.

## 6. Razorpay Ecosystem Integration
The system relies on three core Razorpay products to close the loop end-to-end:

1. Razorpay Payment Links API (/v1/payment_links): Once the LLM and buyer agree on a price, the deterministic Python backend calculates the final payload and POSTs to Razorpay to generate a unique link.
2. Razorpay Webhooks (payment.link.paid): The FastAPI server listens for this event. Upon success, it updates the LangGraph state to "Paid" and triggers the frontend UI to dispatch logistics.
3. Razorpay Invoices API (/v1/invoices): The ultimate B2B closer. When the payment webhook fires, the FastAPI server autonomously calls this API to generate a formal, GST-compliant PDF invoice. The system then uses the WhatsApp Cloud API to instantly push the invoice PDF link back to the hospital buyer in the same chat thread, completing the procurement loop with zero manual paperwork for my mother.

## 7. The Frontend UX (Zero Cognitive Load)
Standard SaaS dashboards are overwhelming. My mother needs to manage her business at a glance. The frontend is a 2D, isometric pixelated map, while the backend relies on Phoenix for the deep engineering audit trail.

*   The Layout: A pixelated "Hospital" on the left, a "Godown" on the right, connected by a road.
*   Visualizing Inbound Leads: When a WhatsApp message arrives, an animated exclamation mark appears over the Hospital.
*   The Merchant Audit Trail: Clicking the Hospital opens a retro RPG-style dialogue box displaying the high-level LangGraph state (e.g., "Checking inventory... Stock found. Negotiating...").
*   Visualizing Payments: When the Razorpay link is sent, a floating dollar sign appears. When the Razorpay webhook confirms payment, the icon turns green.
*   Logistics and Invoice Simulation: Post-payment, a pixelated "Receipt" icon briefly flashes over the Godown (confirming the Razorpay Invoice was sent to the buyer's WhatsApp). Immediately after, a pixelated Rapido driver sprite animates moving from the Godown to the Hospital along the road, visually confirming to my mom that the order is paid, invoiced, and fulfilled.

## 8. Future Scope
*   Dynamic Freight: Integrating the Porter/Borzo API to dynamically calculate shipping costs based on the collected PIN code and injecting it as a line item in the Razorpay link