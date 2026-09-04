# AI Buyer Agent

## One-line pitch
An AI-powered procurement and payment assistant that turns a natural-language shopping request into a budget-compliant, approval-aware, and auditable purchase flow.

## Real-world problem it solves
Companies and teams often lose time and money because purchase requests are handled manually:
- employees ask for products in chat or email
- managers manually compare options
- budgets are checked ad hoc
- approval rules are inconsistent
- payments and audit trails are disconnected

This creates delays, overspending risk, and poor visibility into what was approved and why.

## What the system does
The AI Buyer Agent solves this by combining product discovery, policy validation, and payment orchestration into one workflow.

### Core flow
1. User describes a product request in natural language.
2. The system infers intent, category, brand preference, and budget.
3. It searches the product catalog and ranks options by fit, rating, availability, and delivery.
4. It checks business rules like maximum spend, daily limits, and approval thresholds.
5. If the purchase exceeds policy thresholds, it triggers approval.
6. If approved, it creates a Razorpay payment order.
7. It stores transaction history and audit information for review.

## Why this matters
This is not just a shopping assistant. It is a small but practical version of an AI-powered purchasing workflow that companies need in real life.

Use cases:
- employee purchasing
- internal procurement assistants
- budget-controlled spend management
- finance/audit compliance
- guided buying for non-technical users

## Business value
- reduces buying friction
- keeps spending within policy
- increases decision transparency
- speeds up approvals
- creates a clean purchase audit trail

## Technical highlights
- FastAPI backend with REST endpoints
- AI-based intent parsing
- product ranking and filtering logic
- spending limit checks
- approval workflow
- Razorpay order integration
- transaction history and audit logging

## Why this is a strong project story
This project sits at the intersection of three important trends:
- AI for decision support
- fintech and payments
- workflow automation for business operations

It showcases a real product-thinking mindset: not just building a chatbot, but building a system that can automate a meaningful business process with safeguards.

## Demo positioning
In an interview or project review, this project can be positioned as:
> "An AI-powered procurement workflow for teams that need faster buying decisions without losing budget control or compliance." 

That is a much stronger story than simply calling it a shopping bot.
