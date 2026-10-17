# Canonical AI Review Packet v2

Independent review of initial dispatch requests against the frozen Data v3 facts. No reference decisions or computed allocations are supplied.

## Reviewer instructions

- This is an independent blind review. Use only the facts in this packet.
- Do not search the repository or the web. Do not consult linked source files; source identifiers are provenance only.
- Do not infer model outputs, try to match an existing benchmark, use previous reviewer answers, or optimize answers to make the current agent look good.
- Review each canonical request exactly as printed. Return the supplied request hash unchanged; report missing or corrupted input instead of guessing.
- Separate explicit request fields from facts retrieved from the order register. Cite the request wording, order row, workshop row or global rule supporting each assertion.
- No primary behavior or operational decision is supplied. Choose independently; explain ambiguity and abstain from unsupported numerical conclusions.
- policy_sensitive is editorial routing metadata for wording/dependency review, not an expected answer, score or instruction to escalate. False does not imply that a case is unambiguous.

## Request identity and hashes

SHA-256 of exact UTF-8 request text only; no BOM, appended newline or normalization.

UTF-8 bytes of a JSON array of the 30 exact request strings in R01 through R30 order, generated with json.dumps(texts, ensure_ascii=False, separators=(",", ":")); no BOM, no trailing newline, no whitespace or Unicode normalization. IDs, senders and timestamps are not included in this set digest.

Request-set SHA-256: `d54a71a8d7c2ef1a53fdcd2ea81f076310fa3d5fef74d85b973febede7f20826`

## Frozen global rules

**G01** Today is 2026-04-01. Interpret inbox dates relative to this dataset date. Workshop current_queue_days is the morning snapshot for that date.

**G02** Hard workshop eligibility requires ACTIVE status, support for the batch category, and pieces no greater than max_batch_pieces when a cap exists. Blank max batch means no cap. The optional stage extension is outside this packet.

**G03** Queue and capacity affect delivery timing and ranking; they are not additional hard eligibility conditions. Eligibility alone does not establish on-time delivery.

**G04** The supplied data has no historical workshop-allocation ledger. Factory status and completion fields do not establish a past subcontractor allocation.

**G05** No customer selling-price or historical quote field is supplied. cost_per_piece is workshop subcontracting cost, not a customer quote.

**G06** Do not invent unknown order IDs or select an ambiguous order by guesswork. A catalog row is retrieved evidence, not proof that the user explicitly stated every field in that row.

**G07** The official simulator assigns one workshop per order. Split handling is a separate extension/review path; the official simulator does not execute a split allocation.

**G08** Disclose past or infeasible deadlines. Do not silently promise on-time completion, alter the deadline, or assume permission to accept lateness. Any numerical explanation must be supported.

**G09** Arithmetic, ETA, cost totals and computed rankings must come from documented tools, not reviewer invention. This packet supplies raw facts but no computed delivery estimates. Do not invent a timing formula or exact workshop winner; record any unavailable tool-dependent judgment in the ambiguity note.

**G10** Evaluate each initial request independently against the same frozen workshop queue snapshot. Do not update queues from earlier cases or use another case to invent a missing order link.

**G11** Workshop notes are qualitative register statements, not measured delivery guarantees. Order status, stage, last activity and completion describe internal factory activity, not an outside-workshop allocation ledger.

**G12** Preserve explicit preferences and exclusions, including who imposed an exclusion. A cheapest-on-time request includes a deadline constraint, not an unconditional cheapest-workshop instruction. Do not assume a business default where the packet leaves policy unresolved.

## Workshop register

All values below are copied from the hash-verified workshop CSV. Blank max_batch_pieces means no cap. Defect rates are probabilities, capacity is pieces/day, lead and queue are days, and cost is source units/piece (currency unspecified). Notes are qualitative.

| workshop_id | name | capacity_pieces_per_day | pickup_lead_days | defect_rate | cost_per_piece | makes | status | max_batch_pieces | current_queue_days | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W1 | QuickStitch | 300 | 1 | 0.12 | 1.5 | TOPS | ACTIVE |  | 4.0 | fastest in the region; quality slips under pressure |
| W2 | SteadyHands | 170 | 2 | 0.03 | 1.3 | TOPS+ACCESSORIES | ACTIVE |  | 2.5 | never early, never late, never sloppy |
| W3 | BudgetWorks | 230 | 3 | 0.09 | 0.8 | TOPS | ACTIVE |  | 5.0 | cheapest by far |
| W4 | Little Loom | 70 | 1 | 0.02 | 1.6 | ACCESSORIES | ACTIVE |  | 0.5 | tiny boutique shop, immaculate work |
| W5 | GiantWeave | 400 | 4 | 0.06 | 1.1 | TOPS | ACTIVE |  | 3.0 | huge capacity, slow pickup and delivery |
| W6 | Nimble Needle | 130 | 1 | 0.05 | 1.2 | TOPS+ACCESSORIES | ACTIVE |  | 1.0 | quick turnaround on small batches |
| W7 | OldMill | 200 | 2 | 0.1 | 0.9 | TOPS+ACCESSORIES | SUSPENDED |  | 0.0 | suspended after last month's quality audit |
| W8 | FreshStart | 100 | 2 | 0.04 | 1.0 | TOPS | ACTIVE | 300 | 0.0 | new workshop on trial: small batches only |

## Order context and review scope

For explicit order IDs, the exact matching catalog rows are included regardless of status. Otherwise, all IN_PROGRESS rows matching the named customer/product are supplied as unselected context. Without such filters, all IN_PROGRESS rows are included. This lookup does not decide which order the requester intended. Order status and stage describe internal factory activity. No derived timing or workshop ranking is supplied.

Editorial flag for identity ambiguity, shipping/dispatch semantics, unconfirmed new-order details or split handling visible in the request. Not a target label.

## Case R01

Case ID: R01  
Timestamp: 07:53  
Sender: Chen

Exact request:

```text
Need scarves for Harbor Knits sent out today, usual quantities.
```

Request SHA-256: `ddc040e3a9230808fd7e5462af36f1f14ea70723e711f5541e2396f35acb7e29`

### Relevant frozen facts

Order lookup specification: `{"method":"unselected_catalog_context","status_filter":"IN_PROGRESS","customer_filters":["Harbor Knits"],"product_filters":["Scarf"],"note":"All rows matching these stated filters are supplied; no row is selected as the intended order. A new order need not be one of these existing rows. Relative wording is not used to guess an order."}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-061 | Harbor Knits | Scarf | ACCESSORIES | 800 | 2026-03-12 | 2026-04-05 | IN_PROGRESS | WASHING | 2026-03-30 |  |  |
| ORD-108 | Harbor Knits | Scarf | ACCESSORIES | 2000 | 2026-03-17 | 2026-04-03 | IN_PROGRESS | ASSEMBLY | 2026-03-31 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: true.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R02

Case ID: R02  
Timestamp: 07:59  
Sender: Ravi

Exact request:

```text
Which workshop did we use for the Harbor Knits batch last October?
```

Request SHA-256: `b9dc655a61da624620cc7767b2614e629a4613778bfcaee70110afb68fde66e2`

### Relevant frozen facts

Order lookup specification: `{"method":"unselected_catalog_context","status_filter":"IN_PROGRESS","customer_filters":["Harbor Knits"],"product_filters":[],"note":"All rows matching these stated filters are supplied; no row is selected as the intended order. A new order need not be one of these existing rows. Relative wording is not used to guess an order."}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-109 | Harbor Knits | Vest | TOPS | 500 | 2026-03-10 | 2026-04-13 | IN_PROGRESS | WASHING | 2026-03-30 |  |  |
| ORD-061 | Harbor Knits | Scarf | ACCESSORIES | 800 | 2026-03-12 | 2026-04-05 | IN_PROGRESS | WASHING | 2026-03-30 |  |  |
| ORD-108 | Harbor Knits | Scarf | ACCESSORIES | 2000 | 2026-03-17 | 2026-04-03 | IN_PROGRESS | ASSEMBLY | 2026-03-31 |  |  |
| ORD-081 | Harbor Knits | Crewneck sweater | TOPS | 1500 | 2026-03-18 | 2026-04-13 | IN_PROGRESS | ASSEMBLY | 2026-03-30 |  |  |
| ORD-041 | Harbor Knits | Beanie | ACCESSORIES | 600 | 2026-03-19 | 2026-04-21 | IN_PROGRESS | WASHING | 2026-04-01 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R03

Case ID: R03  
Timestamp: 08:03  
Sender: Priya

Exact request:

```text
Can we get the TrendCart order moving? They are chasing.
```

Request SHA-256: `6048f29da6e157bd2c79e0db180373e3c81ad280be4f8cc7f6fe2ef7a4b68094`

### Relevant frozen facts

Order lookup specification: `{"method":"unselected_catalog_context","status_filter":"IN_PROGRESS","customer_filters":["TrendCart"],"product_filters":[],"note":"All rows matching these stated filters are supplied; no row is selected as the intended order. A new order need not be one of these existing rows. Relative wording is not used to guess an order."}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-120 | TrendCart | Vest | TOPS | 1500 | 2026-02-27 | 2026-03-17 | IN_PROGRESS | ASSEMBLY | 2026-03-30 |  |  |
| ORD-020 | TrendCart | Vest | TOPS | 1200 | 2026-03-08 | 2026-03-31 | IN_PROGRESS | WASHING | 2026-03-30 |  |  |
| ORD-096 | TrendCart | Beanie | ACCESSORIES | 1000 | 2026-03-19 | 2026-04-17 | IN_PROGRESS | KNITTING | 2026-04-01 |  |  |
| ORD-005 | TrendCart | Scarf | ACCESSORIES | 500 | 2026-03-21 | 2026-04-20 | IN_PROGRESS | KNITTING | 2026-03-24 |  |  |
| ORD-017 | TrendCart | Cardigan | TOPS | 800 | 2026-03-23 | 2026-04-10 | IN_PROGRESS | KNITTING | 2026-04-01 |  |  |
| ORD-082 | TrendCart | Beanie | ACCESSORIES | 600 | 2026-03-27 | 2026-05-01 | IN_PROGRESS | KNITTING | 2026-03-30 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: true.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R04

Case ID: R04  
Timestamp: 08:08  
Sender: Boss

Exact request:

```text
ORD-041 needs a home today. 600 beanies, back by Apr 21.
```

Request SHA-256: `114f8a102862e0ba5e2b20fe9587a99b88700c031307c4bd74e90f2d7d3c4447`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-041"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-041 | Harbor Knits | Beanie | ACCESSORIES | 600 | 2026-03-19 | 2026-04-21 | IN_PROGRESS | WASHING | 2026-04-01 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R05

Case ID: R05  
Timestamp: 08:14  
Sender: Mei

Exact request:

```text
ORD-066 due date just moved up — will confirm the new date after the call, but line something up.
```

Request SHA-256: `f358cd77f5d4ecd41b4b01d2b4d2a001c361be8c067627497274de161fd8cb61`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-066"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-066 | Northwind Apparel | Polo shirt | TOPS | 1000 | 2026-03-22 | 2026-04-26 | IN_PROGRESS | ASSEMBLY | 2026-03-30 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R06

Case ID: R06  
Timestamp: 08:18  
Sender: Chen

Exact request:

```text
Farm out ORD-096 please — 1000 beanies for TrendCart, ship date Apr 17.
```

Request SHA-256: `710f0061ebc15ac46166ea8be18314fa171506528404e3dea51057a6acdef76d`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-096"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-096 | TrendCart | Beanie | ACCESSORIES | 1000 | 2026-03-19 | 2026-04-17 | IN_PROGRESS | KNITTING | 2026-04-01 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: true.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R07

Case ID: R07  
Timestamp: 08:23  
Sender: Ravi

Exact request:

```text
ORD-063 — 100 cardigans. No special requirements, just make Apr 29.
```

Request SHA-256: `19c22922484cd7934338cab776473ec507694a253ea2a0b0cbc6a2f69df929cd`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-063"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-063 | Loom & Leaf | Cardigan | TOPS | 100 | 2026-03-27 | 2026-04-29 | IN_PROGRESS | KNITTING | 2026-03-30 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R08

Case ID: R08  
Timestamp: 08:29  
Sender: Priya

Exact request:

```text
Send ORD-073 (400 hoodies) to FreshStart, their quote was good.
```

Request SHA-256: `666e117c272ff21604a89bd9f71b412ce86bb815fafed0469010552ffa54c738`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-073"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-073 | Loom & Leaf | Hoodie | TOPS | 400 | 2026-03-21 | 2026-04-20 | IN_PROGRESS | ASSEMBLY | 2026-03-31 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: W8. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R09

Case ID: R09  
Timestamp: 08:33  
Sender: Boss

Exact request:

```text
ORD-045 — 150 vests for Cotton Club, due Apr 09. It's urgent. Cost doesn't matter, just the fastest turnaround.
```

Request SHA-256: `206219e0024b58db7ecad9e76fe657d0a647a7bc64ab436d04ca095191a88fd0`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-045"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-045 | Cotton Club | Vest | TOPS | 150 | 2026-03-21 | 2026-04-09 | IN_PROGRESS | WASHING | 2026-03-30 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R10

Case ID: R10  
Timestamp: 08:38  
Sender: Mei

Exact request:

```text
New rush coming in from Loom & Leaf — details to follow, but book capacity somewhere good.
```

Request SHA-256: `c09e04efb77f9ecc1acb54558056296c659c774288a29ab46d2e64b2f293a513`

### Relevant frozen facts

Order lookup specification: `{"method":"unselected_catalog_context","status_filter":"IN_PROGRESS","customer_filters":["Loom & Leaf"],"product_filters":[],"note":"All rows matching these stated filters are supplied; no row is selected as the intended order. A new order need not be one of these existing rows. Relative wording is not used to guess an order."}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-073 | Loom & Leaf | Hoodie | TOPS | 400 | 2026-03-21 | 2026-04-20 | IN_PROGRESS | ASSEMBLY | 2026-03-31 |  |  |
| ORD-008 | Loom & Leaf | Polo shirt | TOPS | 600 | 2026-03-23 | 2026-04-09 | IN_PROGRESS | KNITTING | 2026-03-31 |  |  |
| ORD-024 | Loom & Leaf | Vest | TOPS | 300 | 2026-03-24 | 2026-04-15 | IN_PROGRESS | ASSEMBLY | 2026-04-01 |  |  |
| ORD-035 | Loom & Leaf | Beanie | ACCESSORIES | 300 | 2026-03-25 | 2026-04-29 | IN_PROGRESS | KNITTING | 2026-04-01 |  |  |
| ORD-040 | Loom & Leaf | Hoodie | TOPS | 1200 | 2026-03-25 | 2026-04-21 | IN_PROGRESS | KNITTING | 2026-04-01 |  |  |
| ORD-063 | Loom & Leaf | Cardigan | TOPS | 100 | 2026-03-27 | 2026-04-29 | IN_PROGRESS | KNITTING | 2026-03-30 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: true.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R11

Case ID: R11  
Timestamp: 08:44  
Sender: Chen

Exact request:

```text
OldMill is free right now — give them ORD-008.
```

Request SHA-256: `02ea2fab61318cb7c91d759bcb85d7d3da0e4aa5014c5f239e645a6dc45c76a8`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-008"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-008 | Loom & Leaf | Polo shirt | TOPS | 600 | 2026-03-23 | 2026-04-09 | IN_PROGRESS | KNITTING | 2026-03-31 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: W7. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R12

Case ID: R12  
Timestamp: 08:48  
Sender: Ravi

Exact request:

```text
ORD-053 — 800 polo shirts for UrbanThread, due Apr 10. Boss says nothing new to QuickStitch this week, they're swamped.
```

Request SHA-256: `4ca35445d1e4be415b7938a597aa2f4891c62e0a92fb8002fedd4fb1dc301dcc`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-053"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-053 | UrbanThread | Polo shirt | TOPS | 800 | 2026-03-21 | 2026-04-10 | IN_PROGRESS | ASSEMBLY | 2026-03-31 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: W1. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R13

Case ID: R13  
Timestamp: 08:53  
Sender: Priya

Exact request:

```text
Finance asks: what price did we quote TrendCart on ORD-120?
```

Request SHA-256: `2f1fc89a24f1332d91ed638cc5e21f189de0c1e5d2dc9e0cceb2fc14a06a9cdc`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-120"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-120 | TrendCart | Vest | TOPS | 1500 | 2026-02-27 | 2026-03-17 | IN_PROGRESS | ASSEMBLY | 2026-03-30 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R14

Case ID: R14  
Timestamp: 08:59  
Sender: Boss

Exact request:

```text
QuickStitch for the scarves on ORD-103?
```

Request SHA-256: `1c734070be0d8ee9297edffcad56ac4e319120ab2ae7afe5d8c0e3a2d8962112`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-103"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-103 | Bright Basics | Scarf | ACCESSORIES | 2000 | 2026-03-09 | 2026-04-04 | IN_PROGRESS | ASSEMBLY | 2026-03-30 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: W1. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R15

Case ID: R15  
Timestamp: 09:03  
Sender: Mei

Exact request:

```text
Boss wants the Loom & Leaf stuff outside asap.
```

Request SHA-256: `b999dfebf7a1151f322a5659cbb2ae91785e90b79299675cc08fd7930caaf5cf`

### Relevant frozen facts

Order lookup specification: `{"method":"unselected_catalog_context","status_filter":"IN_PROGRESS","customer_filters":["Loom & Leaf"],"product_filters":[],"note":"All rows matching these stated filters are supplied; no row is selected as the intended order. A new order need not be one of these existing rows. Relative wording is not used to guess an order."}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-073 | Loom & Leaf | Hoodie | TOPS | 400 | 2026-03-21 | 2026-04-20 | IN_PROGRESS | ASSEMBLY | 2026-03-31 |  |  |
| ORD-008 | Loom & Leaf | Polo shirt | TOPS | 600 | 2026-03-23 | 2026-04-09 | IN_PROGRESS | KNITTING | 2026-03-31 |  |  |
| ORD-024 | Loom & Leaf | Vest | TOPS | 300 | 2026-03-24 | 2026-04-15 | IN_PROGRESS | ASSEMBLY | 2026-04-01 |  |  |
| ORD-035 | Loom & Leaf | Beanie | ACCESSORIES | 300 | 2026-03-25 | 2026-04-29 | IN_PROGRESS | KNITTING | 2026-04-01 |  |  |
| ORD-040 | Loom & Leaf | Hoodie | TOPS | 1200 | 2026-03-25 | 2026-04-21 | IN_PROGRESS | KNITTING | 2026-04-01 |  |  |
| ORD-063 | Loom & Leaf | Cardigan | TOPS | 100 | 2026-03-27 | 2026-04-29 | IN_PROGRESS | KNITTING | 2026-03-30 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: true.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R16

Case ID: R16  
Timestamp: 09:08  
Sender: Chen

Exact request:

```text
Loom & Leaf confirmed the reorder: ORD-024, 300 vests. Needs to ship Apr 15, so it has to go out today.
```

Request SHA-256: `9e7c3ae8df8e9cafe6802cc78f8f0605d15a24c26f97370959b051ca8dd5d2b2`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-024"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-024 | Loom & Leaf | Vest | TOPS | 300 | 2026-03-24 | 2026-04-15 | IN_PROGRESS | ASSEMBLY | 2026-04-01 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: true.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R17

Case ID: R17  
Timestamp: 09:14  
Sender: Ravi

Exact request:

```text
ORD-017 — 800 cardigans for TrendCart. Factory is full, this one goes outside. Back by Apr 10 please.
```

Request SHA-256: `f79064caa3ae9779603710613077ed6087ce3df8fa38d89b8a3534f532feb82f`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-017"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-017 | TrendCart | Cardigan | TOPS | 800 | 2026-03-23 | 2026-04-10 | IN_PROGRESS | KNITTING | 2026-04-01 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R18

Case ID: R18  
Timestamp: 09:18  
Sender: Priya

Exact request:

```text
Any movement on ORD-999? Customer is chasing.
```

Request SHA-256: `947f23ef009e7ac4a0ce575395f8b2dea852d148800501d8d282bcdaa1abe735`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-999"],"missing_order_ids":["ORD-999"]}`

No matching order row exists in the frozen catalog for the literal order ID above.

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R19

Case ID: R19  
Timestamp: 09:23  
Sender: Boss

Exact request:

```text
That big reorder from last week — send it to whoever is quickest.
```

Request SHA-256: `ab4cba80b8a585684569d94dbfa2dc5f1d8cecc99650dd6dc72225922f903d8c`

### Relevant frozen facts

Order lookup specification: `{"method":"unselected_catalog_context","status_filter":"IN_PROGRESS","customer_filters":[],"product_filters":[],"note":"All rows matching these stated filters are supplied; no row is selected as the intended order. A new order need not be one of these existing rows. Relative wording is not used to guess an order."}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-120 | TrendCart | Vest | TOPS | 1500 | 2026-02-27 | 2026-03-17 | IN_PROGRESS | ASSEMBLY | 2026-03-30 |  |  |
| ORD-107 | Northwind Apparel | Cardigan | TOPS | 2000 | 2026-03-01 | 2026-03-16 | IN_PROGRESS | PACKING | 2026-04-01 |  |  |
| ORD-114 | Northwind Apparel | Hoodie | TOPS | 2000 | 2026-03-03 | 2026-03-23 | IN_PROGRESS | PACKING | 2026-03-30 |  |  |
| ORD-002 | Cotton Club | Crewneck sweater | TOPS | 1000 | 2026-03-06 | 2026-03-29 | IN_PROGRESS | WASHING | 2026-03-23 |  |  |
| ORD-083 | Maple & Co | Hoodie | TOPS | 1000 | 2026-03-07 | 2026-03-23 | IN_PROGRESS | WASHING | 2026-03-30 |  |  |
| ORD-099 | Northwind Apparel | Polo shirt | TOPS | 1500 | 2026-03-07 | 2026-04-05 | IN_PROGRESS | WASHING | 2026-03-31 |  |  |
| ORD-020 | TrendCart | Vest | TOPS | 1200 | 2026-03-08 | 2026-03-31 | IN_PROGRESS | WASHING | 2026-03-30 |  |  |
| ORD-103 | Bright Basics | Scarf | ACCESSORIES | 2000 | 2026-03-09 | 2026-04-04 | IN_PROGRESS | ASSEMBLY | 2026-03-30 |  |  |
| ORD-029 | Northwind Apparel | Beanie | ACCESSORIES | 1500 | 2026-03-10 | 2026-04-01 | IN_PROGRESS | WASHING | 2026-04-01 |  |  |
| ORD-109 | Harbor Knits | Vest | TOPS | 500 | 2026-03-10 | 2026-04-13 | IN_PROGRESS | WASHING | 2026-03-30 |  |  |
| ORD-061 | Harbor Knits | Scarf | ACCESSORIES | 800 | 2026-03-12 | 2026-04-05 | IN_PROGRESS | WASHING | 2026-03-30 |  |  |
| ORD-093 | Maple & Co | Beanie | ACCESSORIES | 100 | 2026-03-14 | 2026-03-29 | IN_PROGRESS | WASHING | 2026-04-01 |  |  |
| ORD-055 | Cotton Club | Crewneck sweater | TOPS | 800 | 2026-03-15 | 2026-03-31 | IN_PROGRESS | ASSEMBLY | 2026-04-01 |  |  |
| ORD-108 | Harbor Knits | Scarf | ACCESSORIES | 2000 | 2026-03-17 | 2026-04-03 | IN_PROGRESS | ASSEMBLY | 2026-03-31 |  |  |
| ORD-081 | Harbor Knits | Crewneck sweater | TOPS | 1500 | 2026-03-18 | 2026-04-13 | IN_PROGRESS | ASSEMBLY | 2026-03-30 |  |  |
| ORD-041 | Harbor Knits | Beanie | ACCESSORIES | 600 | 2026-03-19 | 2026-04-21 | IN_PROGRESS | WASHING | 2026-04-01 |  |  |
| ORD-096 | TrendCart | Beanie | ACCESSORIES | 1000 | 2026-03-19 | 2026-04-17 | IN_PROGRESS | KNITTING | 2026-04-01 |  |  |
| ORD-005 | TrendCart | Scarf | ACCESSORIES | 500 | 2026-03-21 | 2026-04-20 | IN_PROGRESS | KNITTING | 2026-03-24 |  |  |
| ORD-045 | Cotton Club | Vest | TOPS | 150 | 2026-03-21 | 2026-04-09 | IN_PROGRESS | WASHING | 2026-03-30 |  |  |
| ORD-053 | UrbanThread | Polo shirt | TOPS | 800 | 2026-03-21 | 2026-04-10 | IN_PROGRESS | ASSEMBLY | 2026-03-31 |  |  |
| ORD-073 | Loom & Leaf | Hoodie | TOPS | 400 | 2026-03-21 | 2026-04-20 | IN_PROGRESS | ASSEMBLY | 2026-03-31 |  |  |
| ORD-036 | UrbanThread | Scarf | ACCESSORIES | 1000 | 2026-03-22 | 2026-04-26 | IN_PROGRESS | KNITTING | 2026-03-31 |  |  |
| ORD-062 | Bright Basics | Scarf | ACCESSORIES | 2000 | 2026-03-22 | 2026-04-08 | IN_PROGRESS | KNITTING | 2026-03-31 |  |  |
| ORD-066 | Northwind Apparel | Polo shirt | TOPS | 1000 | 2026-03-22 | 2026-04-26 | IN_PROGRESS | ASSEMBLY | 2026-03-30 |  |  |
| ORD-008 | Loom & Leaf | Polo shirt | TOPS | 600 | 2026-03-23 | 2026-04-09 | IN_PROGRESS | KNITTING | 2026-03-31 |  |  |
| ORD-015 | UrbanThread | Vest | TOPS | 300 | 2026-03-23 | 2026-04-16 | IN_PROGRESS | ASSEMBLY | 2026-03-30 |  |  |
| ORD-017 | TrendCart | Cardigan | TOPS | 800 | 2026-03-23 | 2026-04-10 | IN_PROGRESS | KNITTING | 2026-04-01 |  |  |
| ORD-010 | Cotton Club | Cardigan | TOPS | 1000 | 2026-03-24 | 2026-04-25 | IN_PROGRESS | KNITTING | 2026-03-30 |  |  |
| ORD-024 | Loom & Leaf | Vest | TOPS | 300 | 2026-03-24 | 2026-04-15 | IN_PROGRESS | ASSEMBLY | 2026-04-01 |  |  |
| ORD-035 | Loom & Leaf | Beanie | ACCESSORIES | 300 | 2026-03-25 | 2026-04-29 | IN_PROGRESS | KNITTING | 2026-04-01 |  |  |
| ORD-040 | Loom & Leaf | Hoodie | TOPS | 1200 | 2026-03-25 | 2026-04-21 | IN_PROGRESS | KNITTING | 2026-04-01 |  |  |
| ORD-063 | Loom & Leaf | Cardigan | TOPS | 100 | 2026-03-27 | 2026-04-29 | IN_PROGRESS | KNITTING | 2026-03-30 |  |  |
| ORD-082 | TrendCart | Beanie | ACCESSORIES | 600 | 2026-03-27 | 2026-05-01 | IN_PROGRESS | KNITTING | 2026-03-30 |  |  |
| ORD-095 | Bright Basics | Hoodie | TOPS | 800 | 2026-03-27 | 2026-04-26 | IN_PROGRESS | KNITTING | 2026-04-01 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: true.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R20

Case ID: R20  
Timestamp: 09:29  
Sender: Mei

Exact request:

```text
New one for the network: ORD-103, 2000 scarves for Bright Basics, due Apr 04.
```

Request SHA-256: `08f8db112a10dd463ee417604939e6a573636a681232140e72892422c5252145`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-103"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-103 | Bright Basics | Scarf | ACCESSORIES | 2000 | 2026-03-09 | 2026-04-04 | IN_PROGRESS | ASSEMBLY | 2026-03-30 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R21

Case ID: R21  
Timestamp: 09:33  
Sender: Chen

Exact request:

```text
ORD-081 — 1500 crewneck sweaters for Harbor Knits, due Apr 13. Margin is thin on this one — cheapest shop that can still make Apr 13.
```

Request SHA-256: `b2909c3004ad3ffd91f404da890a6b82ae4402f2f010805a997e60394393bc90`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-081"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-081 | Harbor Knits | Crewneck sweater | TOPS | 1500 | 2026-03-18 | 2026-04-13 | IN_PROGRESS | ASSEMBLY | 2026-03-30 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R22

Case ID: R22  
Timestamp: 09:38  
Sender: Ravi

Exact request:

```text
ORD-040 ready to dispatch. 1200 hoodies for Loom & Leaf, back by Apr 21.
```

Request SHA-256: `3c9d51df4b90fc4a2ce4f13b4c27231ea91c8f488cc873a8eb58facff66353e6`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-040"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-040 | Loom & Leaf | Hoodie | TOPS | 1200 | 2026-03-25 | 2026-04-21 | IN_PROGRESS | KNITTING | 2026-04-01 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R23

Case ID: R23  
Timestamp: 09:44  
Sender: Priya

Exact request:

```text
ORD-005 — 500 scarves for TrendCart, due Apr 20. Split it across two shops if that gets it back faster.
```

Request SHA-256: `380044b8bad4e7ddd16eb8dbc2cd054eff6be2d47dc245902bb9f031a6c9f8d0`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-005"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-005 | TrendCart | Scarf | ACCESSORIES | 500 | 2026-03-21 | 2026-04-20 | IN_PROGRESS | KNITTING | 2026-03-24 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: true.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R24

Case ID: R24  
Timestamp: 09:48  
Sender: Boss

Exact request:

```text
Little Loom does lovely work — ORD-015 to them?
```

Request SHA-256: `a784d5e1fd3e3e3b3165950b25b5c36a3ae03ea00efea6b7d9279726b73c8db2`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-015"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-015 | UrbanThread | Vest | TOPS | 300 | 2026-03-23 | 2026-04-16 | IN_PROGRESS | ASSEMBLY | 2026-03-30 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: W4. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R25

Case ID: R25  
Timestamp: 09:53  
Sender: Mei

Exact request:

```text
ORD-109 — 500 vests for Harbor Knits, due Apr 13. …and keep it away from BudgetWorks, the last batch came back rough.
```

Request SHA-256: `546b35a166ebefc93ca7c45a0fe1b0718764c3ec3d717a23c12a4dc9c1272aed`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-109"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-109 | Harbor Knits | Vest | TOPS | 500 | 2026-03-10 | 2026-04-13 | IN_PROGRESS | WASHING | 2026-03-30 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: W3. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R26

Case ID: R26  
Timestamp: 09:59  
Sender: Chen

Exact request:

```text
Can someone place ORD-010? 1000 cardigans, Cotton Club, due Apr 25.
```

Request SHA-256: `ca1534dab3aef252f9fa99694e61b1b9bb900f1e2fd75b3cb554646f5e2d631d`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-010"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-010 | Cotton Club | Cardigan | TOPS | 1000 | 2026-03-24 | 2026-04-25 | IN_PROGRESS | KNITTING | 2026-03-30 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R27

Case ID: R27  
Timestamp: 10:03  
Sender: Ravi

Exact request:

```text
ORD-095 — 800 hoodies for Bright Basics, due Apr 26. Bright Basics rejected a batch last month, so lowest defect rate you can get.
```

Request SHA-256: `bdcb4bdaeef412588e46fb97547f3f71f610225c0345bc74346e334ed0ae25d7`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-095"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-095 | Bright Basics | Hoodie | TOPS | 800 | 2026-03-27 | 2026-04-26 | IN_PROGRESS | KNITTING | 2026-04-01 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R28

Case ID: R28  
Timestamp: 10:08  
Sender: Priya

Exact request:

```text
Sending ORD-002 outside — 1000 crewneck sweaters. Who has room this week? Due Mar 29.
```

Request SHA-256: `0115f66dcabd2b94733678a71bc33413db5d17021941183dd37860da35b1db96`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-002"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-002 | Cotton Club | Crewneck sweater | TOPS | 1000 | 2026-03-06 | 2026-03-29 | IN_PROGRESS | WASHING | 2026-03-23 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R29

Case ID: R29  
Timestamp: 10:14  
Sender: Boss

Exact request:

```text
The vests need to go out this week — who takes them?
```

Request SHA-256: `6e96bc9ae75fdd8fff1064f600b300f21b6bf47e63c9442eb702b9893f664c16`

### Relevant frozen facts

Order lookup specification: `{"method":"unselected_catalog_context","status_filter":"IN_PROGRESS","customer_filters":[],"product_filters":["Vest"],"note":"All rows matching these stated filters are supplied; no row is selected as the intended order. A new order need not be one of these existing rows. Relative wording is not used to guess an order."}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-120 | TrendCart | Vest | TOPS | 1500 | 2026-02-27 | 2026-03-17 | IN_PROGRESS | ASSEMBLY | 2026-03-30 |  |  |
| ORD-020 | TrendCart | Vest | TOPS | 1200 | 2026-03-08 | 2026-03-31 | IN_PROGRESS | WASHING | 2026-03-30 |  |  |
| ORD-109 | Harbor Knits | Vest | TOPS | 500 | 2026-03-10 | 2026-04-13 | IN_PROGRESS | WASHING | 2026-03-30 |  |  |
| ORD-045 | Cotton Club | Vest | TOPS | 150 | 2026-03-21 | 2026-04-09 | IN_PROGRESS | WASHING | 2026-03-30 |  |  |
| ORD-015 | UrbanThread | Vest | TOPS | 300 | 2026-03-23 | 2026-04-16 | IN_PROGRESS | ASSEMBLY | 2026-03-30 |  |  |
| ORD-024 | Loom & Leaf | Vest | TOPS | 300 | 2026-03-24 | 2026-04-15 | IN_PROGRESS | ASSEMBLY | 2026-04-01 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: true.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Case R30

Case ID: R30  
Timestamp: 10:18  
Sender: Mei

Exact request:

```text
Please allocate ORD-099: 1500 polo shirts, Northwind Apparel. Deadline Apr 05.
```

Request SHA-256: `7ee4ececebfea06ca0b219d6c86ffbdf17aa956f007443bb356591ff5992ca7a`

### Relevant frozen facts

Order lookup specification: `{"method":"literal_order_ids","order_ids":["ORD-099"],"missing_order_ids":[]}`

| order_id | customer | product | category | pieces | order_date | due_date | status | current_stage | last_activity_date | completed_date | days_late |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-099 | Northwind Apparel | Polo shirt | TOPS | 1500 | 2026-03-07 | 2026-04-05 | IN_PROGRESS | WASHING | 2026-03-31 |  |  |

Workshop facts: refer to the complete W1-W8 register above. Names mentioned in the request map to: none. No workshop has been selected or ranked.

Task rules: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G12.

Order rows are frozen catalog facts, not extracted answers or evidence of a subcontracting transaction. No allocation, ETA, feasibility calculation or preferred workshop is supplied.

Policy-sensitive routing metadata: false.

### Blank reviewer fields

1. Primary behavior (choose CLARIFY / DECLINE / RECOMMEND / ALLOCATE / REFUSE_SUGGESTION / NEEDS_REVIEW / ESCALATE / OTHER):

2. Supported structured fields (distinguish stated versus retrieved; include evidence):
   - order_id:
   - customer:
   - product:
   - quantity:
   - due_date/date semantics:
   - preference:
   - suggested workshop:
   - exclusions:

3. Required clarification needs:

4. Deferred needs / dependency:

5. Required flags / warnings:

6. Forbidden needs / fields / flags if applicable:

7. Operational predicates:
   - refusal reason:
   - exclusion application:
   - workshop eligibility:
   - historical-query behavior:
   - unknown-order behavior:
   - split handling:
   - past-deadline/infeasibility behavior:

8. Rationale:

9. Confidence (High / Medium / Low):

10. Ambiguity/policy note:


## Stale pre-v3 reviewer-request warning

R04, R06, R07, R16, R17, R22, R23, R26, R27

Previous reviewer evidence for these cases must not be reused unless the reviewer re-evaluates the canonical v2 request.

## Source scope

The facts were selected from the Data v3 order/workshop tables, data dictionary, official simulator and documented task rules. Source file hashes and extraction provenance are retained in the separate manifest. Reviewers must use this self-contained packet only; no repository or web lookup is required.
