# Independent reliability review packet

Preparation only, NOT gold. READY_FOR_GOLD means ready for review, not final gold. No independent reviewer decision is supplied. Read raw request/source before provisional expectations to reduce anchoring; do not infer labels from model outputs.

## Frozen source context

Snapshot 2026-04-01; independent workshop CSV queues; registered-order preview. Weights {"lateness": 1, "defects": 0, "cost": 0, "deadline_buffer_days": 0}. Explicit preferences may override effective weights. Supplied data lacks historical workshop allocations/customer quotes. Official ACTIVE/category/cap eligibility applies; no commitment/reservation.

- track2/data/dispatch_requests.txt / raw_bytes_sha256 / dd00a2db398e4acaea1becf82137b6d7526c746621c28af5534806105d50117a
- track2/data/orders.csv / raw_bytes_sha256 / 0880af9742fe7cc0923c5009e2de48a0bedb57b78cc294e35a1c9721fe0311f8
- track2/data/workshops.csv / raw_bytes_sha256 / d7e1c97d3d338a2b5aef8e35f167e3582f22c4526e9c736c5b4c8125505ec59e
- examples/chat_rubric.json / normalized_text_sha256 / 3d5a17380de57ba5f78c3e627e077213493e13e806ba073f0b8ef7202c71a5d5
- examples/dispatch_inputs.json / normalized_text_sha256 / 6c0f29f6e6f5b6e8d38f6e22b160d014dbe83445628822db4863f1238801c201
- docs/CHAT_EVALUATION_RESULTS.md / normalized_text_sha256 / 8ef353e2f8ac3b1d8b6f9f2134da0b04b1238a706b15fa7dd41d97eef2743826
- tests/test_intake.py / normalized_text_sha256 / ad7d0f6a90c977d6c29122a71d5360074ddbe391aaf54ad3ec35b190e3d2b9ea
- tests/test_dispatch.py / normalized_text_sha256 / abac3594c8bcff84e6080c24275fb2f4e7298fda6d8d2cabab4840f4a3879da7
- tests/test_chat_ui.py / normalized_text_sha256 / 7a9b887d43603db54bf561d09d833d9aa2692409d113926685720a3ec81dda02

Manifest/benchmark hashes

- before_recorder_manifest: 5be209b51537d38ec635b2cf428c06c285e484ddefbffd09fbab13363947347d
- after_recorder_manifest: 192a16bcbb47a9f894c861f65a3d5e1f84d0f0c00dec9725095d5daa29a366ba
- before_scorer_manifest: cb62ea0684a49849053f724bcac4976ecfb8d4cdab3cfbd37574eef13df85526
- after_scorer_manifest: 5c10153c1c0fb34b8ca8d4cdeba39dfe07144638cfddd54b06fdfc18ca6cd8ff
- benchmark: bb55a3462c6f8291549f1b956bf14f0c5b7c117fd9b211d4c53a09d0e14be8ee

## Workshop source facts

~~~json
[
  {
    "workshop_id": "W1",
    "name": "QuickStitch",
    "capacity_pieces_per_day": "300",
    "pickup_lead_days": "1",
    "defect_rate": "0.12",
    "cost_per_piece": "1.5",
    "makes": "TOPS",
    "status": "ACTIVE",
    "max_batch_pieces": "",
    "current_queue_days": "4.0",
    "notes": "fastest in the region; quality slips under pressure"
  },
  {
    "workshop_id": "W2",
    "name": "SteadyHands",
    "capacity_pieces_per_day": "170",
    "pickup_lead_days": "2",
    "defect_rate": "0.03",
    "cost_per_piece": "1.3",
    "makes": "TOPS+ACCESSORIES",
    "status": "ACTIVE",
    "max_batch_pieces": "",
    "current_queue_days": "2.5",
    "notes": "never early, never late, never sloppy"
  },
  {
    "workshop_id": "W3",
    "name": "BudgetWorks",
    "capacity_pieces_per_day": "230",
    "pickup_lead_days": "3",
    "defect_rate": "0.09",
    "cost_per_piece": "0.8",
    "makes": "TOPS",
    "status": "ACTIVE",
    "max_batch_pieces": "",
    "current_queue_days": "5.0",
    "notes": "cheapest by far"
  },
  {
    "workshop_id": "W4",
    "name": "Little Loom",
    "capacity_pieces_per_day": "70",
    "pickup_lead_days": "1",
    "defect_rate": "0.02",
    "cost_per_piece": "1.6",
    "makes": "ACCESSORIES",
    "status": "ACTIVE",
    "max_batch_pieces": "",
    "current_queue_days": "0.5",
    "notes": "tiny boutique shop, immaculate work"
  },
  {
    "workshop_id": "W5",
    "name": "GiantWeave",
    "capacity_pieces_per_day": "400",
    "pickup_lead_days": "4",
    "defect_rate": "0.06",
    "cost_per_piece": "1.1",
    "makes": "TOPS",
    "status": "ACTIVE",
    "max_batch_pieces": "",
    "current_queue_days": "3.0",
    "notes": "huge capacity, slow pickup and delivery"
  },
  {
    "workshop_id": "W6",
    "name": "Nimble Needle",
    "capacity_pieces_per_day": "130",
    "pickup_lead_days": "1",
    "defect_rate": "0.05",
    "cost_per_piece": "1.2",
    "makes": "TOPS+ACCESSORIES",
    "status": "ACTIVE",
    "max_batch_pieces": "",
    "current_queue_days": "1.0",
    "notes": "quick turnaround on small batches"
  },
  {
    "workshop_id": "W7",
    "name": "OldMill",
    "capacity_pieces_per_day": "200",
    "pickup_lead_days": "2",
    "defect_rate": "0.1",
    "cost_per_piece": "0.9",
    "makes": "TOPS+ACCESSORIES",
    "status": "SUSPENDED",
    "max_batch_pieces": "",
    "current_queue_days": "0.0",
    "notes": "suspended after last month's quality audit"
  },
  {
    "workshop_id": "W8",
    "name": "FreshStart",
    "capacity_pieces_per_day": "100",
    "pickup_lead_days": "2",
    "defect_rate": "0.04",
    "cost_per_piece": "1.0",
    "makes": "TOPS",
    "status": "ACTIVE",
    "max_batch_pieces": "300",
    "current_queue_days": "0.0",
    "notes": "new workshop on trial: small batches only"
  }
]
~~~

## R01

Requester: Chen

Request: Need scarves for Harbor Knits sent out today, usual quantities.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-007",
    "customer": "Harbor Knits",
    "product": "Cardigan",
    "category": "TOPS",
    "pieces": "2000",
    "order_date": "2026-01-06",
    "due_date": "2026-01-30",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-13",
    "completed_date": "2026-02-13",
    "days_late": "14"
  },
  {
    "order_id": "ORD-049",
    "customer": "Harbor Knits",
    "product": "Scarf",
    "category": "ACCESSORIES",
    "pieces": "300",
    "order_date": "2026-01-08",
    "due_date": "2026-01-22",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-01-30",
    "completed_date": "2026-01-30",
    "days_late": "8"
  },
  {
    "order_id": "ORD-101",
    "customer": "Harbor Knits",
    "product": "Scarf",
    "category": "ACCESSORIES",
    "pieces": "1200",
    "order_date": "2026-01-13",
    "due_date": "2026-01-27",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-07",
    "completed_date": "2026-02-07",
    "days_late": "11"
  },
  {
    "order_id": "ORD-052",
    "customer": "Harbor Knits",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "1200",
    "order_date": "2026-01-14",
    "due_date": "2026-02-13",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-12",
    "completed_date": "2026-02-12",
    "days_late": "-1"
  },
  {
    "order_id": "ORD-067",
    "customer": "Harbor Knits",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "400",
    "order_date": "2026-01-30",
    "due_date": "2026-03-04",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-15",
    "completed_date": "2026-02-15",
    "days_late": "-17"
  },
  {
    "order_id": "ORD-085",
    "customer": "Harbor Knits",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "1500",
    "order_date": "2026-02-07",
    "due_date": "2026-03-01",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-05",
    "completed_date": "2026-03-05",
    "days_late": "4"
  },
  {
    "order_id": "ORD-034",
    "customer": "Harbor Knits",
    "product": "Cardigan",
    "category": "TOPS",
    "pieces": "1000",
    "order_date": "2026-02-17",
    "due_date": "2026-03-12",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-19",
    "completed_date": "2026-03-19",
    "days_late": "7"
  },
  {
    "order_id": "ORD-088",
    "customer": "Harbor Knits",
    "product": "Crewneck sweater",
    "category": "TOPS",
    "pieces": "300",
    "order_date": "2026-03-02",
    "due_date": "2026-03-21",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-18",
    "completed_date": "2026-03-18",
    "days_late": "-3"
  },
  {
    "order_id": "ORD-109",
    "customer": "Harbor Knits",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "500",
    "order_date": "2026-03-10",
    "due_date": "2026-04-13",
    "status": "IN_PROGRESS",
    "current_stage": "WASHING",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-069",
    "customer": "Harbor Knits",
    "product": "Cardigan",
    "category": "TOPS",
    "pieces": "400",
    "order_date": "2026-03-11",
    "due_date": "2026-04-09",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-30",
    "completed_date": "2026-03-30",
    "days_late": "-10"
  },
  {
    "order_id": "ORD-112",
    "customer": "Harbor Knits",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "300",
    "order_date": "2026-03-11",
    "due_date": "2026-03-28",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-24",
    "completed_date": "2026-03-24",
    "days_late": "-4"
  },
  {
    "order_id": "ORD-061",
    "customer": "Harbor Knits",
    "product": "Scarf",
    "category": "ACCESSORIES",
    "pieces": "800",
    "order_date": "2026-03-12",
    "due_date": "2026-04-05",
    "status": "IN_PROGRESS",
    "current_stage": "WASHING",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-108",
    "customer": "Harbor Knits",
    "product": "Scarf",
    "category": "ACCESSORIES",
    "pieces": "2000",
    "order_date": "2026-03-17",
    "due_date": "2026-04-03",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-03-31",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-081",
    "customer": "Harbor Knits",
    "product": "Crewneck sweater",
    "category": "TOPS",
    "pieces": "1500",
    "order_date": "2026-03-18",
    "due_date": "2026-04-13",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-041",
    "customer": "Harbor Knits",
    "product": "Beanie",
    "category": "ACCESSORIES",
    "pieces": "600",
    "order_date": "2026-03-19",
    "due_date": "2026-04-21",
    "status": "IN_PROGRESS",
    "current_stage": "WASHING",
    "last_activity_date": "2026-04-01",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "CLARIFY",
  "expected_fields": {
    "order_id": null,
    "customer": "Harbor Knits",
    "product": "Scarf",
    "pieces": null,
    "date_kind": "shipping"
  },
  "expected_resolved_fields": {},
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [
    "order",
    "quantity"
  ],
  "forbidden_needs": [],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "no_candidates_or_recommendation",
    "selection_predicate": null,
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null
  },
  "required_flags": [],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "targeted_clarification",
      "no_ranking_before_resolution"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: NEEDS_POLICY_DECISION; unresolved: True.
- Usual quantities is explicit uncertainty, not an omitted retrievable quantity.
- Today describes sending; no delivery deadline is inferred. Shipping interpretation and question ordering need adjudication.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.
- Does sent out today express dispatch only, or should it set date_kind=shipping and/or due_date=2026-04-01?
- Should explicit usual quantities be asked alongside order identification, and must it remain blocking after identification?
- Should an omitted delivery deadline be absent from needs or optionally deferred while order is unresolved?

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R02

Requester: Ravi

Request: Which workshop did we use for the Harbor Knits batch last October?

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-007",
    "customer": "Harbor Knits",
    "product": "Cardigan",
    "category": "TOPS",
    "pieces": "2000",
    "order_date": "2026-01-06",
    "due_date": "2026-01-30",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-13",
    "completed_date": "2026-02-13",
    "days_late": "14"
  },
  {
    "order_id": "ORD-049",
    "customer": "Harbor Knits",
    "product": "Scarf",
    "category": "ACCESSORIES",
    "pieces": "300",
    "order_date": "2026-01-08",
    "due_date": "2026-01-22",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-01-30",
    "completed_date": "2026-01-30",
    "days_late": "8"
  },
  {
    "order_id": "ORD-101",
    "customer": "Harbor Knits",
    "product": "Scarf",
    "category": "ACCESSORIES",
    "pieces": "1200",
    "order_date": "2026-01-13",
    "due_date": "2026-01-27",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-07",
    "completed_date": "2026-02-07",
    "days_late": "11"
  },
  {
    "order_id": "ORD-052",
    "customer": "Harbor Knits",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "1200",
    "order_date": "2026-01-14",
    "due_date": "2026-02-13",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-12",
    "completed_date": "2026-02-12",
    "days_late": "-1"
  },
  {
    "order_id": "ORD-067",
    "customer": "Harbor Knits",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "400",
    "order_date": "2026-01-30",
    "due_date": "2026-03-04",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-15",
    "completed_date": "2026-02-15",
    "days_late": "-17"
  },
  {
    "order_id": "ORD-085",
    "customer": "Harbor Knits",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "1500",
    "order_date": "2026-02-07",
    "due_date": "2026-03-01",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-05",
    "completed_date": "2026-03-05",
    "days_late": "4"
  },
  {
    "order_id": "ORD-034",
    "customer": "Harbor Knits",
    "product": "Cardigan",
    "category": "TOPS",
    "pieces": "1000",
    "order_date": "2026-02-17",
    "due_date": "2026-03-12",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-19",
    "completed_date": "2026-03-19",
    "days_late": "7"
  },
  {
    "order_id": "ORD-088",
    "customer": "Harbor Knits",
    "product": "Crewneck sweater",
    "category": "TOPS",
    "pieces": "300",
    "order_date": "2026-03-02",
    "due_date": "2026-03-21",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-18",
    "completed_date": "2026-03-18",
    "days_late": "-3"
  },
  {
    "order_id": "ORD-109",
    "customer": "Harbor Knits",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "500",
    "order_date": "2026-03-10",
    "due_date": "2026-04-13",
    "status": "IN_PROGRESS",
    "current_stage": "WASHING",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-069",
    "customer": "Harbor Knits",
    "product": "Cardigan",
    "category": "TOPS",
    "pieces": "400",
    "order_date": "2026-03-11",
    "due_date": "2026-04-09",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-30",
    "completed_date": "2026-03-30",
    "days_late": "-10"
  },
  {
    "order_id": "ORD-112",
    "customer": "Harbor Knits",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "300",
    "order_date": "2026-03-11",
    "due_date": "2026-03-28",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-24",
    "completed_date": "2026-03-24",
    "days_late": "-4"
  },
  {
    "order_id": "ORD-061",
    "customer": "Harbor Knits",
    "product": "Scarf",
    "category": "ACCESSORIES",
    "pieces": "800",
    "order_date": "2026-03-12",
    "due_date": "2026-04-05",
    "status": "IN_PROGRESS",
    "current_stage": "WASHING",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-108",
    "customer": "Harbor Knits",
    "product": "Scarf",
    "category": "ACCESSORIES",
    "pieces": "2000",
    "order_date": "2026-03-17",
    "due_date": "2026-04-03",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-03-31",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-081",
    "customer": "Harbor Knits",
    "product": "Crewneck sweater",
    "category": "TOPS",
    "pieces": "1500",
    "order_date": "2026-03-18",
    "due_date": "2026-04-13",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-041",
    "customer": "Harbor Knits",
    "product": "Beanie",
    "category": "ACCESSORIES",
    "pieces": "600",
    "order_date": "2026-03-19",
    "due_date": "2026-04-21",
    "status": "IN_PROGRESS",
    "current_stage": "WASHING",
    "last_activity_date": "2026-04-01",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "DECLINE",
  "expected_fields": {
    "order_id": null,
    "intent": "history",
    "customer": "Harbor Knits",
    "due_date": null,
    "date_uncertain": false
  },
  "expected_resolved_fields": {},
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days",
    "due_date"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "no_candidates_or_recommendation",
    "selection_predicate": null,
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null
  },
  "required_flags": [],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "missing_records_limitation",
      "no_invented_answer"
    ],
    "forbidden_question_topics": [
      "allocation_quantity",
      "allocation_deadline"
    ],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- Historical last October must not become a delivery deadline or irrelevant allocation questions.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R03

Requester: Priya

Request: Can we get the TrendCart order moving? They are chasing.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-076",
    "customer": "TrendCart",
    "product": "Crewneck sweater",
    "category": "TOPS",
    "pieces": "1200",
    "order_date": "2026-01-02",
    "due_date": "2026-01-27",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-08",
    "completed_date": "2026-02-08",
    "days_late": "12"
  },
  {
    "order_id": "ORD-087",
    "customer": "TrendCart",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "1000",
    "order_date": "2026-01-03",
    "due_date": "2026-01-19",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-18",
    "completed_date": "2026-02-18",
    "days_late": "30"
  },
  {
    "order_id": "ORD-091",
    "customer": "TrendCart",
    "product": "Polo shirt",
    "category": "TOPS",
    "pieces": "600",
    "order_date": "2026-01-03",
    "due_date": "2026-02-02",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-01-27",
    "completed_date": "2026-01-27",
    "days_late": "-6"
  },
  {
    "order_id": "ORD-028",
    "customer": "TrendCart",
    "product": "Beanie",
    "category": "ACCESSORIES",
    "pieces": "150",
    "order_date": "2026-01-10",
    "due_date": "2026-01-26",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-04",
    "completed_date": "2026-02-04",
    "days_late": "9"
  },
  {
    "order_id": "ORD-115",
    "customer": "TrendCart",
    "product": "Cardigan",
    "category": "TOPS",
    "pieces": "2000",
    "order_date": "2026-01-10",
    "due_date": "2026-01-28",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-28",
    "completed_date": "2026-02-28",
    "days_late": "31"
  },
  {
    "order_id": "ORD-021",
    "customer": "TrendCart",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "800",
    "order_date": "2026-01-17",
    "due_date": "2026-02-18",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-13",
    "completed_date": "2026-02-13",
    "days_late": "-5"
  },
  {
    "order_id": "ORD-059",
    "customer": "TrendCart",
    "product": "Scarf",
    "category": "ACCESSORIES",
    "pieces": "100",
    "order_date": "2026-01-22",
    "due_date": "2026-02-24",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-15",
    "completed_date": "2026-02-15",
    "days_late": "-9"
  },
  {
    "order_id": "ORD-090",
    "customer": "TrendCart",
    "product": "Polo shirt",
    "category": "TOPS",
    "pieces": "600",
    "order_date": "2026-01-22",
    "due_date": "2026-02-23",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-06",
    "completed_date": "2026-03-06",
    "days_late": "11"
  },
  {
    "order_id": "ORD-014",
    "customer": "TrendCart",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "2000",
    "order_date": "2026-01-27",
    "due_date": "2026-02-28",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-23",
    "completed_date": "2026-03-23",
    "days_late": "23"
  },
  {
    "order_id": "ORD-054",
    "customer": "TrendCart",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "600",
    "order_date": "2026-02-20",
    "due_date": "2026-03-06",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-29",
    "completed_date": "2026-03-29",
    "days_late": "23"
  },
  {
    "order_id": "ORD-120",
    "customer": "TrendCart",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "1500",
    "order_date": "2026-02-27",
    "due_date": "2026-03-17",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-030",
    "customer": "TrendCart",
    "product": "Cardigan",
    "category": "TOPS",
    "pieces": "400",
    "order_date": "2026-02-28",
    "due_date": "2026-03-27",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-28",
    "completed_date": "2026-03-28",
    "days_late": "1"
  },
  {
    "order_id": "ORD-020",
    "customer": "TrendCart",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "1200",
    "order_date": "2026-03-08",
    "due_date": "2026-03-31",
    "status": "IN_PROGRESS",
    "current_stage": "WASHING",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-096",
    "customer": "TrendCart",
    "product": "Beanie",
    "category": "ACCESSORIES",
    "pieces": "1000",
    "order_date": "2026-03-19",
    "due_date": "2026-04-17",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-04-01",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-005",
    "customer": "TrendCart",
    "product": "Scarf",
    "category": "ACCESSORIES",
    "pieces": "500",
    "order_date": "2026-03-21",
    "due_date": "2026-04-20",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-03-24",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-017",
    "customer": "TrendCart",
    "product": "Cardigan",
    "category": "TOPS",
    "pieces": "800",
    "order_date": "2026-03-23",
    "due_date": "2026-04-10",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-04-01",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-082",
    "customer": "TrendCart",
    "product": "Beanie",
    "category": "ACCESSORIES",
    "pieces": "600",
    "order_date": "2026-03-27",
    "due_date": "2026-05-01",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "CLARIFY",
  "expected_fields": {
    "order_id": null,
    "customer": "TrendCart"
  },
  "expected_resolved_fields": {},
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [
    "order"
  ],
  "forbidden_needs": [],
  "expected_deferred_needs": null,
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "no_candidates_or_recommendation",
    "selection_predicate": null,
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null
  },
  "required_flags": [],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "targeted_clarification",
      "no_ranking_before_resolution"
    ],
    "forbidden_question_topics": [
      "omitted_retrievable_quantity",
      "omitted_retrievable_deadline"
    ],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: NEEDS_WORDING/EXPECTATION_REFINEMENT; unresolved: True.
- Order question must appear once. Optional omitted quantity/deadline needs may be deferred, not asked prematurely.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.
- Is needs=[order] equivalent to order plus quantity/deadline when all omitted secondary needs are deferred?
- Which explicit predicate forbids non-deferred secondary needs while expected_deferred_needs is null?

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R04

Requester: Boss

Request: ORD-041 needs a home today. 600 beanies, back by Apr 21.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-041",
    "customer": "Harbor Knits",
    "product": "Beanie",
    "category": "ACCESSORIES",
    "pieces": "600",
    "order_date": "2026-03-19",
    "due_date": "2026-04-21",
    "status": "IN_PROGRESS",
    "current_stage": "WASHING",
    "last_activity_date": "2026-04-01",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "RECOMMEND",
  "expected_fields": {
    "order_id": "ORD-041",
    "pieces": 600,
    "product": "Beanie",
    "due_date": "2026-04-21",
    "intent": "allocate"
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-041",
    "batch.order_id": "ORD-041",
    "batch.category": "ACCESSORIES",
    "batch.pieces": 600,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-21"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_configured_score_among_permitted_candidates",
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null,
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": true
  },
  "required_flags": [],
  "forbidden_flags": [
    "NO_ON_TIME_OPTION",
    "PAST_DEADLINE",
    "SELECTED_OPTION_LATE",
    "SUGGESTION_REFUSED",
    "SPLIT_REVIEW"
  ],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "eligible_recommendation",
      "delivery_is_estimate_not_guarantee"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R05

Requester: Mei

Request: ORD-066 due date just moved up — will confirm the new date after the call, but line something up.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-066",
    "customer": "Northwind Apparel",
    "product": "Polo shirt",
    "category": "TOPS",
    "pieces": "1000",
    "order_date": "2026-03-22",
    "due_date": "2026-04-26",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "CLARIFY",
  "expected_fields": {
    "order_id": "ORD-066",
    "date_uncertain": true,
    "due_date": null
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-066"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [
    "deadline"
  ],
  "forbidden_needs": [],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "no_candidates_or_recommendation",
    "selection_predicate": null,
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null
  },
  "required_flags": [],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "targeted_clarification",
      "no_ranking_before_resolution"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- Unknown revised deadline must block ranking; do not reuse the registered due date.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R06

Requester: Chen

Request: Farm out ORD-096 please — 1000 beanies for TrendCart, ship date Apr 17.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-096",
    "customer": "TrendCart",
    "product": "Beanie",
    "category": "ACCESSORIES",
    "pieces": "1000",
    "order_date": "2026-03-19",
    "due_date": "2026-04-17",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-04-01",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "RECOMMEND",
  "expected_fields": {
    "order_id": "ORD-096",
    "pieces": 1000,
    "product": "Beanie",
    "customer": "TrendCart",
    "due_date": "2026-04-17",
    "date_kind": "shipping"
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-096",
    "batch.order_id": "ORD-096",
    "batch.category": "ACCESSORIES",
    "batch.pieces": 1000,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-17"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_configured_score_among_permitted_candidates",
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null,
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": true
  },
  "required_flags": [],
  "forbidden_flags": [
    "NO_ON_TIME_OPTION",
    "PAST_DEADLINE",
    "SELECTED_OPTION_LATE",
    "SUGGESTION_REFUSED",
    "SPLIT_REVIEW"
  ],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "eligible_recommendation",
      "delivery_is_estimate_not_guarantee",
      "ship_date_matches_recorded_due_date"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: NEEDS_POLICY_DECISION; unresolved: True.
- Shipping date matches the recorded due date. RECOMMEND follows the current tool convention; this policy still needs independent adjudication.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.
- Does a ship date matching the registered due date authorize treating it as delivery without clarification, or should shipping semantics always be clarified?

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R07

Requester: Ravi

Request: ORD-063 — 100 cardigans. No special requirements, just make Apr 29.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-063",
    "customer": "Loom & Leaf",
    "product": "Cardigan",
    "category": "TOPS",
    "pieces": "100",
    "order_date": "2026-03-27",
    "due_date": "2026-04-29",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "RECOMMEND",
  "expected_fields": {
    "order_id": "ORD-063",
    "pieces": 100,
    "product": "Cardigan",
    "due_date": "2026-04-29"
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-063",
    "batch.order_id": "ORD-063",
    "batch.category": "TOPS",
    "batch.pieces": 100,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-29"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_configured_score_among_permitted_candidates",
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null,
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": true
  },
  "required_flags": [],
  "forbidden_flags": [
    "NO_ON_TIME_OPTION",
    "PAST_DEADLINE",
    "SELECTED_OPTION_LATE",
    "SUGGESTION_REFUSED",
    "SPLIT_REVIEW"
  ],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "eligible_recommendation",
      "delivery_is_estimate_not_guarantee"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R08

Requester: Priya

Request: Send ORD-073 (400 hoodies) to FreshStart, their quote was good.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-073",
    "customer": "Loom & Leaf",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "400",
    "order_date": "2026-03-21",
    "due_date": "2026-04-20",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-03-31",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "REFUSE_SUGGESTION",
  "expected_fields": {
    "order_id": "ORD-073",
    "pieces": 400,
    "product": "Hoodie",
    "suggested_workshop": "W8",
    "intent": "allocate"
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-073",
    "batch.order_id": "ORD-073",
    "batch.category": "TOPS",
    "batch.pieces": 400,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-20"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_configured_score_among_permitted_candidates",
    "refused_workshop_id": "W8",
    "refusal_reason": "batch_size_exceeds_300_piece_cap",
    "alternative_predicate": "eligible_permitted_candidate_selected_by_effective_policy",
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": false
  },
  "required_flags": [
    "SUGGESTION_REFUSED"
  ],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "refusal_reason",
      "eligible_alternative_if_available",
      "disclose_alternative_lateness"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- The quote comment is not a request for a customer quote or authority to invent a price.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R09

Requester: Boss

Request: ORD-045 — 150 vests for Cotton Club, due Apr 09. It's urgent. Cost doesn't matter, just the fastest turnaround.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-045",
    "customer": "Cotton Club",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "150",
    "order_date": "2026-03-21",
    "due_date": "2026-04-09",
    "status": "IN_PROGRESS",
    "current_stage": "WASHING",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "RECOMMEND",
  "expected_fields": {
    "order_id": "ORD-045",
    "pieces": 150,
    "product": "Vest",
    "customer": "Cotton Club",
    "due_date": "2026-04-09",
    "preference": "fastest"
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-045",
    "batch.order_id": "ORD-045",
    "batch.category": "TOPS",
    "batch.pieces": 150,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-09"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_expected_turnaround_among_permitted_candidates",
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null,
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": true
  },
  "required_flags": [],
  "forbidden_flags": [
    "NO_ON_TIME_OPTION",
    "PAST_DEADLINE",
    "SELECTED_OPTION_LATE",
    "SUGGESTION_REFUSED",
    "SPLIT_REVIEW"
  ],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "eligible_recommendation",
      "delivery_is_estimate_not_guarantee"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R10

Requester: Mei

Request: New rush coming in from Loom & Leaf — details to follow, but book capacity somewhere good.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-038",
    "customer": "Loom & Leaf",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "2000",
    "order_date": "2026-01-08",
    "due_date": "2026-02-08",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-09",
    "completed_date": "2026-02-09",
    "days_late": "1"
  },
  {
    "order_id": "ORD-065",
    "customer": "Loom & Leaf",
    "product": "Crewneck sweater",
    "category": "TOPS",
    "pieces": "100",
    "order_date": "2026-01-16",
    "due_date": "2026-02-12",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-01",
    "completed_date": "2026-02-01",
    "days_late": "-11"
  },
  {
    "order_id": "ORD-102",
    "customer": "Loom & Leaf",
    "product": "Beanie",
    "category": "ACCESSORIES",
    "pieces": "600",
    "order_date": "2026-01-19",
    "due_date": "2026-02-12",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-12",
    "completed_date": "2026-02-12",
    "days_late": "0"
  },
  {
    "order_id": "ORD-064",
    "customer": "Loom & Leaf",
    "product": "Beanie",
    "category": "ACCESSORIES",
    "pieces": "400",
    "order_date": "2026-01-20",
    "due_date": "2026-02-21",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-09",
    "completed_date": "2026-02-09",
    "days_late": "-12"
  },
  {
    "order_id": "ORD-071",
    "customer": "Loom & Leaf",
    "product": "Scarf",
    "category": "ACCESSORIES",
    "pieces": "1200",
    "order_date": "2026-01-30",
    "due_date": "2026-03-04",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-25",
    "completed_date": "2026-02-25",
    "days_late": "-7"
  },
  {
    "order_id": "ORD-074",
    "customer": "Loom & Leaf",
    "product": "Scarf",
    "category": "ACCESSORIES",
    "pieces": "300",
    "order_date": "2026-02-12",
    "due_date": "2026-03-12",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-10",
    "completed_date": "2026-03-10",
    "days_late": "-2"
  },
  {
    "order_id": "ORD-027",
    "customer": "Loom & Leaf",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "600",
    "order_date": "2026-02-28",
    "due_date": "2026-03-19",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-16",
    "completed_date": "2026-03-16",
    "days_late": "-3"
  },
  {
    "order_id": "ORD-073",
    "customer": "Loom & Leaf",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "400",
    "order_date": "2026-03-21",
    "due_date": "2026-04-20",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-03-31",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-008",
    "customer": "Loom & Leaf",
    "product": "Polo shirt",
    "category": "TOPS",
    "pieces": "600",
    "order_date": "2026-03-23",
    "due_date": "2026-04-09",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-03-31",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-024",
    "customer": "Loom & Leaf",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "300",
    "order_date": "2026-03-24",
    "due_date": "2026-04-15",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-04-01",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-035",
    "customer": "Loom & Leaf",
    "product": "Beanie",
    "category": "ACCESSORIES",
    "pieces": "300",
    "order_date": "2026-03-25",
    "due_date": "2026-04-29",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-04-01",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-040",
    "customer": "Loom & Leaf",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "1200",
    "order_date": "2026-03-25",
    "due_date": "2026-04-21",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-04-01",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-063",
    "customer": "Loom & Leaf",
    "product": "Cardigan",
    "category": "TOPS",
    "pieces": "100",
    "order_date": "2026-03-27",
    "due_date": "2026-04-29",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "CLARIFY",
  "expected_fields": {
    "order_id": null,
    "customer": "Loom & Leaf",
    "pieces": null,
    "due_date": null
  },
  "expected_resolved_fields": {},
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "no_candidates_or_recommendation",
    "selection_predicate": null,
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null
  },
  "required_flags": [],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "targeted_clarification",
      "no_ranking_before_resolution",
      "new_order_and_booking_scope_limitation"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: NEEDS_POLICY_DECISION; unresolved: True.
- New-order creation and capacity booking are unsupported. Keep provisional CLARIFY; exact scope/order/detail needs are not fixed pending adjudication.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.
- Should an incomplete new-order booking request CLARIFY for details, DECLINE unsupported creation/booking, or require a new scoped request?
- Which order/product/quantity/deadline/scope needs are legitimate, and should an existing-order ID question be forbidden?
- Should expected_deferred_needs=[] be replaced by unasserted or scope-specific needs once the workflow is chosen?

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R11

Requester: Chen

Request: OldMill is free right now — give them ORD-008.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-008",
    "customer": "Loom & Leaf",
    "product": "Polo shirt",
    "category": "TOPS",
    "pieces": "600",
    "order_date": "2026-03-23",
    "due_date": "2026-04-09",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-03-31",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "REFUSE_SUGGESTION",
  "expected_fields": {
    "order_id": "ORD-008",
    "suggested_workshop": "W7",
    "pieces": null,
    "due_date": null
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-008",
    "batch.order_id": "ORD-008",
    "batch.category": "TOPS",
    "batch.pieces": 600,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-09"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_configured_score_among_permitted_candidates",
    "refused_workshop_id": "W7",
    "refusal_reason": "workshop_suspended",
    "alternative_predicate": "eligible_permitted_candidate_selected_by_effective_policy",
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": false
  },
  "required_flags": [
    "SUGGESTION_REFUSED"
  ],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "refusal_reason",
      "eligible_alternative_if_available",
      "disclose_alternative_lateness"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R12

Requester: Ravi

Request: ORD-053 — 800 polo shirts for UrbanThread, due Apr 10. Boss says nothing new to QuickStitch this week, they're swamped.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-053",
    "customer": "UrbanThread",
    "product": "Polo shirt",
    "category": "TOPS",
    "pieces": "800",
    "order_date": "2026-03-21",
    "due_date": "2026-04-10",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-03-31",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "RECOMMEND",
  "expected_fields": {
    "order_id": "ORD-053",
    "pieces": 800,
    "product": "Polo shirt",
    "customer": "UrbanThread",
    "due_date": "2026-04-10"
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-053",
    "batch.order_id": "ORD-053",
    "batch.category": "TOPS",
    "batch.pieces": 800,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-10"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [
      {
        "workshop_id": "W1",
        "imposed_by": "Boss",
        "reported_by": "Ravi",
        "evidence": "Boss says nothing new to QuickStitch this week"
      }
    ],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_configured_score_among_permitted_candidates",
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null,
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": true
  },
  "required_flags": [],
  "forbidden_flags": [
    "NO_ON_TIME_OPTION",
    "PAST_DEADLINE",
    "SELECTED_OPTION_LATE",
    "SUGGESTION_REFUSED",
    "SPLIT_REVIEW"
  ],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "eligible_recommendation",
      "delivery_is_estimate_not_guarantee"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- Boss is the imposer; Ravi is the reporting speaker. Fixture wording Boss (reported by Ravi) is normalized to separate attribution fields.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R13

Requester: Priya

Request: Finance asks: what price did we quote TrendCart on ORD-120?

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-120",
    "customer": "TrendCart",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "1500",
    "order_date": "2026-02-27",
    "due_date": "2026-03-17",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "DECLINE",
  "expected_fields": {
    "order_id": "ORD-120",
    "customer": "TrendCart",
    "intent": "quote"
  },
  "expected_resolved_fields": {},
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "no_candidates_or_recommendation",
    "selection_predicate": null,
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null
  },
  "required_flags": [],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "missing_records_limitation",
      "no_invented_answer"
    ],
    "forbidden_question_topics": [
      "allocation_quantity",
      "allocation_deadline"
    ],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R14

Requester: Boss

Request: QuickStitch for the scarves on ORD-103?

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-103",
    "customer": "Bright Basics",
    "product": "Scarf",
    "category": "ACCESSORIES",
    "pieces": "2000",
    "order_date": "2026-03-09",
    "due_date": "2026-04-04",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "REFUSE_SUGGESTION",
  "expected_fields": {
    "order_id": "ORD-103",
    "product": "Scarf",
    "suggested_workshop": "W1",
    "pieces": null,
    "due_date": null
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-103",
    "batch.order_id": "ORD-103",
    "batch.category": "ACCESSORIES",
    "batch.pieces": 2000,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-04"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_configured_score_among_permitted_candidates",
    "refused_workshop_id": "W1",
    "refusal_reason": "unsupported_ACCESSORIES_category",
    "alternative_predicate": "eligible_permitted_candidate_selected_by_effective_policy",
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": false
  },
  "required_flags": [
    "SUGGESTION_REFUSED",
    "NO_ON_TIME_OPTION"
  ],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "refusal_reason",
      "eligible_alternative_if_available",
      "disclose_alternative_lateness"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- Registered quantity is 2000. Omitted request quantity stays null; redundant quantity clarification must not prevent refusal. Alternative may be late.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R15

Requester: Mei

Request: Boss wants the Loom & Leaf stuff outside asap.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-038",
    "customer": "Loom & Leaf",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "2000",
    "order_date": "2026-01-08",
    "due_date": "2026-02-08",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-09",
    "completed_date": "2026-02-09",
    "days_late": "1"
  },
  {
    "order_id": "ORD-065",
    "customer": "Loom & Leaf",
    "product": "Crewneck sweater",
    "category": "TOPS",
    "pieces": "100",
    "order_date": "2026-01-16",
    "due_date": "2026-02-12",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-01",
    "completed_date": "2026-02-01",
    "days_late": "-11"
  },
  {
    "order_id": "ORD-102",
    "customer": "Loom & Leaf",
    "product": "Beanie",
    "category": "ACCESSORIES",
    "pieces": "600",
    "order_date": "2026-01-19",
    "due_date": "2026-02-12",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-12",
    "completed_date": "2026-02-12",
    "days_late": "0"
  },
  {
    "order_id": "ORD-064",
    "customer": "Loom & Leaf",
    "product": "Beanie",
    "category": "ACCESSORIES",
    "pieces": "400",
    "order_date": "2026-01-20",
    "due_date": "2026-02-21",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-09",
    "completed_date": "2026-02-09",
    "days_late": "-12"
  },
  {
    "order_id": "ORD-071",
    "customer": "Loom & Leaf",
    "product": "Scarf",
    "category": "ACCESSORIES",
    "pieces": "1200",
    "order_date": "2026-01-30",
    "due_date": "2026-03-04",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-25",
    "completed_date": "2026-02-25",
    "days_late": "-7"
  },
  {
    "order_id": "ORD-074",
    "customer": "Loom & Leaf",
    "product": "Scarf",
    "category": "ACCESSORIES",
    "pieces": "300",
    "order_date": "2026-02-12",
    "due_date": "2026-03-12",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-10",
    "completed_date": "2026-03-10",
    "days_late": "-2"
  },
  {
    "order_id": "ORD-027",
    "customer": "Loom & Leaf",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "600",
    "order_date": "2026-02-28",
    "due_date": "2026-03-19",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-16",
    "completed_date": "2026-03-16",
    "days_late": "-3"
  },
  {
    "order_id": "ORD-073",
    "customer": "Loom & Leaf",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "400",
    "order_date": "2026-03-21",
    "due_date": "2026-04-20",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-03-31",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-008",
    "customer": "Loom & Leaf",
    "product": "Polo shirt",
    "category": "TOPS",
    "pieces": "600",
    "order_date": "2026-03-23",
    "due_date": "2026-04-09",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-03-31",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-024",
    "customer": "Loom & Leaf",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "300",
    "order_date": "2026-03-24",
    "due_date": "2026-04-15",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-04-01",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-035",
    "customer": "Loom & Leaf",
    "product": "Beanie",
    "category": "ACCESSORIES",
    "pieces": "300",
    "order_date": "2026-03-25",
    "due_date": "2026-04-29",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-04-01",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-040",
    "customer": "Loom & Leaf",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "1200",
    "order_date": "2026-03-25",
    "due_date": "2026-04-21",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-04-01",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-063",
    "customer": "Loom & Leaf",
    "product": "Cardigan",
    "category": "TOPS",
    "pieces": "100",
    "order_date": "2026-03-27",
    "due_date": "2026-04-29",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "CLARIFY",
  "expected_fields": {
    "order_id": null,
    "customer": "Loom & Leaf",
    "due_date": null,
    "date_uncertain": false
  },
  "expected_resolved_fields": {},
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days",
    "due_date"
  ],
  "required_needs": [
    "order"
  ],
  "forbidden_needs": [],
  "expected_deferred_needs": null,
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "no_candidates_or_recommendation",
    "selection_predicate": null,
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null
  },
  "required_flags": [],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "targeted_clarification",
      "no_ranking_before_resolution"
    ],
    "forbidden_question_topics": [
      "omitted_retrievable_quantity",
      "omitted_retrievable_deadline"
    ],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: NEEDS_WORDING/EXPECTATION_REFINEMENT; unresolved: True.
- Asap does not establish a precise delivery date. Identify the order before asking for retrievable details.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.
- Should absent and correctly deferred omitted secondary needs be accepted as equivalent?
- Does asap imply preference=fastest, or is it non-specific urgency that remains unasserted?
- How will the final expectation prohibit converting asap into a delivery date while targeting order identification?

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R16

Requester: Chen

Request: Loom & Leaf confirmed the reorder: ORD-024, 300 vests. Needs to ship Apr 15, so it has to go out today.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-024",
    "customer": "Loom & Leaf",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "300",
    "order_date": "2026-03-24",
    "due_date": "2026-04-15",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-04-01",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "RECOMMEND",
  "expected_fields": {
    "order_id": "ORD-024",
    "pieces": 300,
    "product": "Vest",
    "customer": "Loom & Leaf",
    "due_date": "2026-04-15",
    "date_kind": "shipping"
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-024",
    "batch.order_id": "ORD-024",
    "batch.category": "TOPS",
    "batch.pieces": 300,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-15"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_configured_score_among_permitted_candidates",
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null,
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": true
  },
  "required_flags": [],
  "forbidden_flags": [
    "NO_ON_TIME_OPTION",
    "PAST_DEADLINE",
    "SELECTED_OPTION_LATE",
    "SUGGESTION_REFUSED",
    "SPLIT_REVIEW"
  ],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "eligible_recommendation",
      "delivery_is_estimate_not_guarantee",
      "ship_date_matches_recorded_due_date"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: NEEDS_POLICY_DECISION; unresolved: True.
- Shipping date matches the recorded due date; today describes dispatch. Current policy differs from historical shipping clarification.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.
- Ratify the same matching-record ship-date convention as R06.
- Does go out today describe dispatch context only, leaving Apr 15 as the sole deadline under that convention?

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R17

Requester: Ravi

Request: ORD-017 — 800 cardigans for TrendCart. Factory is full, this one goes outside. Back by Apr 10 please.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-017",
    "customer": "TrendCart",
    "product": "Cardigan",
    "category": "TOPS",
    "pieces": "800",
    "order_date": "2026-03-23",
    "due_date": "2026-04-10",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-04-01",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "RECOMMEND",
  "expected_fields": {
    "order_id": "ORD-017",
    "pieces": 800,
    "product": "Cardigan",
    "customer": "TrendCart",
    "due_date": "2026-04-10"
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-017",
    "batch.order_id": "ORD-017",
    "batch.category": "TOPS",
    "batch.pieces": 800,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-10"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_configured_score_among_permitted_candidates",
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null,
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": true
  },
  "required_flags": [],
  "forbidden_flags": [
    "NO_ON_TIME_OPTION",
    "PAST_DEADLINE",
    "SELECTED_OPTION_LATE",
    "SUGGESTION_REFUSED",
    "SPLIT_REVIEW"
  ],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "eligible_recommendation",
      "delivery_is_estimate_not_guarantee"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R18

Requester: Priya

Request: Any movement on ORD-999? Customer is chasing.

### Relevant frozen source facts

~~~json
[]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "DECLINE",
  "expected_fields": {
    "order_id": "ORD-999",
    "intent": "status"
  },
  "expected_resolved_fields": {},
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "no_candidates_or_recommendation",
    "selection_predicate": null,
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null
  },
  "required_flags": [],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "missing_records_limitation",
      "no_invented_answer"
    ],
    "forbidden_question_topics": [
      "allocation_quantity",
      "allocation_deadline"
    ],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- Unknown-order status declines; an allocation request for the same unknown ID would clarify.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R19

Requester: Boss

Request: That big reorder from last week — send it to whoever is quickest.

### Relevant frozen source facts

~~~json
[]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "CLARIFY",
  "expected_fields": {
    "order_id": null,
    "preference": "fastest",
    "due_date": null,
    "date_uncertain": false
  },
  "expected_resolved_fields": {},
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days",
    "due_date"
  ],
  "required_needs": [
    "order"
  ],
  "forbidden_needs": [],
  "expected_deferred_needs": null,
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "no_candidates_or_recommendation",
    "selection_predicate": null,
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null
  },
  "required_flags": [],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "targeted_clarification",
      "no_ranking_before_resolution"
    ],
    "forbidden_question_topics": [
      "omitted_retrievable_quantity",
      "omitted_retrievable_deadline"
    ],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: NEEDS_WORDING/EXPECTATION_REFINEMENT; unresolved: True.
- Last week describes the reorder, not the due date. Fixture asks premature secondary details; dependency-aware regression behavior supersedes that question wording.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.
- Should absent and correctly deferred omitted secondary needs be accepted as equivalent?
- How should the final allowed-state expectation reject blocking secondary needs despite expected_deferred_needs=null?
- Should last week be recorded only as reference context rather than deadline uncertainty?

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R20

Requester: Mei

Request: New one for the network: ORD-103, 2000 scarves for Bright Basics, due Apr 04.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-103",
    "customer": "Bright Basics",
    "product": "Scarf",
    "category": "ACCESSORIES",
    "pieces": "2000",
    "order_date": "2026-03-09",
    "due_date": "2026-04-04",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "NEEDS_REVIEW",
  "expected_fields": {
    "order_id": "ORD-103",
    "pieces": 2000,
    "product": "Scarf",
    "customer": "Bright Basics",
    "due_date": "2026-04-04"
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-103",
    "batch.order_id": "ORD-103",
    "batch.category": "ACCESSORIES",
    "batch.pieces": 2000,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-04"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_configured_score_among_permitted_candidates",
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null,
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": false
  },
  "required_flags": [
    "NO_ON_TIME_OPTION",
    "SELECTED_OPTION_LATE"
  ],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "review_required",
      "tool_supported_options",
      "no_guaranteed_on_time_promise"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R21

Requester: Chen

Request: ORD-081 — 1500 crewneck sweaters for Harbor Knits, due Apr 13. Margin is thin on this one — cheapest shop that can still make Apr 13.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-081",
    "customer": "Harbor Knits",
    "product": "Crewneck sweater",
    "category": "TOPS",
    "pieces": "1500",
    "order_date": "2026-03-18",
    "due_date": "2026-04-13",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "RECOMMEND",
  "expected_fields": {
    "order_id": "ORD-081",
    "pieces": 1500,
    "product": "Crewneck sweater",
    "customer": "Harbor Knits",
    "due_date": "2026-04-13",
    "preference": "cheapest_on_time"
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-081",
    "batch.order_id": "ORD-081",
    "batch.category": "TOPS",
    "batch.pieces": 1500,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-13"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_cost_among_permitted_on_time_candidates",
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null,
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": true
  },
  "required_flags": [],
  "forbidden_flags": [
    "NO_ON_TIME_OPTION",
    "PAST_DEADLINE",
    "SELECTED_OPTION_LATE",
    "SUGGESTION_REFUSED",
    "SPLIT_REVIEW"
  ],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "eligible_recommendation",
      "delivery_is_estimate_not_guarantee"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R22

Requester: Ravi

Request: ORD-040 ready to dispatch. 1200 hoodies for Loom & Leaf, back by Apr 21.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-040",
    "customer": "Loom & Leaf",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "1200",
    "order_date": "2026-03-25",
    "due_date": "2026-04-21",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-04-01",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "RECOMMEND",
  "expected_fields": {
    "order_id": "ORD-040",
    "pieces": 1200,
    "product": "Hoodie",
    "customer": "Loom & Leaf",
    "due_date": "2026-04-21"
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-040",
    "batch.order_id": "ORD-040",
    "batch.category": "TOPS",
    "batch.pieces": 1200,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-21"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_configured_score_among_permitted_candidates",
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null,
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": true
  },
  "required_flags": [],
  "forbidden_flags": [
    "NO_ON_TIME_OPTION",
    "PAST_DEADLINE",
    "SELECTED_OPTION_LATE",
    "SUGGESTION_REFUSED",
    "SPLIT_REVIEW"
  ],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "eligible_recommendation",
      "delivery_is_estimate_not_guarantee"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R23

Requester: Priya

Request: ORD-005 — 500 scarves for TrendCart, due Apr 20. Split it across two shops if that gets it back faster.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-005",
    "customer": "TrendCart",
    "product": "Scarf",
    "category": "ACCESSORIES",
    "pieces": "500",
    "order_date": "2026-03-21",
    "due_date": "2026-04-20",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-03-24",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "NEEDS_REVIEW",
  "expected_fields": {
    "order_id": "ORD-005",
    "pieces": 500,
    "product": "Scarf",
    "customer": "TrendCart",
    "due_date": "2026-04-20",
    "split_requested": true
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-005",
    "batch.order_id": "ORD-005",
    "batch.category": "ACCESSORIES",
    "batch.pieces": 500,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-20"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": true
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_configured_score_among_permitted_candidates",
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null,
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": false
  },
  "required_flags": [
    "SPLIT_REVIEW"
  ],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "review_required",
      "tool_supported_options",
      "no_guaranteed_on_time_promise",
      "conditional_split_benefit_comparison",
      "split_cannot_be_saved"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: NEEDS_POLICY_DECISION; unresolved: True.
- If faster is conditional: split_requested records intent but does not authorize a split. Split estimates exist now; split plans cannot be saved.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.
- Does if faster require NEEDS_REVIEW for every split inquiry, or permit RECOMMEND when the split offers no improvement?
- What defines faster: continuous whole-batch expected turnaround, display-rounded ETA, or another criterion?
- Which whole-batch recommendation predicate and split-assessment predicate should be labeled separately?
- Does split_requested record interest only, with saving/commit disallowed until a separate split contract exists?

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R24

Requester: Boss

Request: Little Loom does lovely work — ORD-015 to them?

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-015",
    "customer": "UrbanThread",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "300",
    "order_date": "2026-03-23",
    "due_date": "2026-04-16",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "REFUSE_SUGGESTION",
  "expected_fields": {
    "order_id": "ORD-015",
    "suggested_workshop": "W4",
    "pieces": null,
    "due_date": null
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-015",
    "batch.order_id": "ORD-015",
    "batch.category": "TOPS",
    "batch.pieces": 300,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-16"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_configured_score_among_permitted_candidates",
    "refused_workshop_id": "W4",
    "refusal_reason": "unsupported_TOPS_category",
    "alternative_predicate": "eligible_permitted_candidate_selected_by_effective_policy",
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": false
  },
  "required_flags": [
    "SUGGESTION_REFUSED"
  ],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "refusal_reason",
      "eligible_alternative_if_available",
      "disclose_alternative_lateness"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R25

Requester: Mei

Request: ORD-109 — 500 vests for Harbor Knits, due Apr 13. …and keep it away from BudgetWorks, the last batch came back rough.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-109",
    "customer": "Harbor Knits",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "500",
    "order_date": "2026-03-10",
    "due_date": "2026-04-13",
    "status": "IN_PROGRESS",
    "current_stage": "WASHING",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "RECOMMEND",
  "expected_fields": {
    "order_id": "ORD-109",
    "pieces": 500,
    "product": "Vest",
    "customer": "Harbor Knits",
    "due_date": "2026-04-13",
    "preference": "configured"
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-109",
    "batch.order_id": "ORD-109",
    "batch.category": "TOPS",
    "batch.pieces": 500,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-13"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [
      {
        "workshop_id": "W3",
        "imposed_by": "Mei",
        "reported_by": "Mei",
        "evidence": "keep it away from BudgetWorks"
      }
    ],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_configured_score_among_permitted_candidates",
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null,
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": true
  },
  "required_flags": [],
  "forbidden_flags": [
    "NO_ON_TIME_OPTION",
    "PAST_DEADLINE",
    "SELECTED_OPTION_LATE",
    "SUGGESTION_REFUSED",
    "SPLIT_REVIEW"
  ],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "eligible_recommendation",
      "delivery_is_estimate_not_guarantee"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- Complaint supports an exclusion, not an explicit lowest_defects preference.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R26

Requester: Chen

Request: Can someone place ORD-010? 1000 cardigans, Cotton Club, due Apr 25.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-010",
    "customer": "Cotton Club",
    "product": "Cardigan",
    "category": "TOPS",
    "pieces": "1000",
    "order_date": "2026-03-24",
    "due_date": "2026-04-25",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "RECOMMEND",
  "expected_fields": {
    "order_id": "ORD-010",
    "pieces": 1000,
    "product": "Cardigan",
    "customer": "Cotton Club",
    "due_date": "2026-04-25"
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-010",
    "batch.order_id": "ORD-010",
    "batch.category": "TOPS",
    "batch.pieces": 1000,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-25"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_configured_score_among_permitted_candidates",
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null,
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": true
  },
  "required_flags": [],
  "forbidden_flags": [
    "NO_ON_TIME_OPTION",
    "PAST_DEADLINE",
    "SELECTED_OPTION_LATE",
    "SUGGESTION_REFUSED",
    "SPLIT_REVIEW"
  ],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "eligible_recommendation",
      "delivery_is_estimate_not_guarantee"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R27

Requester: Ravi

Request: ORD-095 — 800 hoodies for Bright Basics, due Apr 26. Bright Basics rejected a batch last month, so lowest defect rate you can get.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-095",
    "customer": "Bright Basics",
    "product": "Hoodie",
    "category": "TOPS",
    "pieces": "800",
    "order_date": "2026-03-27",
    "due_date": "2026-04-26",
    "status": "IN_PROGRESS",
    "current_stage": "KNITTING",
    "last_activity_date": "2026-04-01",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "RECOMMEND",
  "expected_fields": {
    "order_id": "ORD-095",
    "pieces": 800,
    "product": "Hoodie",
    "customer": "Bright Basics",
    "due_date": "2026-04-26",
    "preference": "lowest_defects"
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-095",
    "batch.order_id": "ORD-095",
    "batch.category": "TOPS",
    "batch.pieces": 800,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-26"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_defect_risk_among_permitted_candidates",
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null,
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": true
  },
  "required_flags": [],
  "forbidden_flags": [
    "NO_ON_TIME_OPTION",
    "PAST_DEADLINE",
    "SELECTED_OPTION_LATE",
    "SUGGESTION_REFUSED",
    "SPLIT_REVIEW"
  ],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "eligible_recommendation",
      "delivery_is_estimate_not_guarantee"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- Last month is historical context, not a deadline. The v3 provisional recommendation differs from the historical late result.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R28

Requester: Priya

Request: Sending ORD-002 outside — 1000 crewneck sweaters. Who has room this week? Due Mar 29.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-002",
    "customer": "Cotton Club",
    "product": "Crewneck sweater",
    "category": "TOPS",
    "pieces": "1000",
    "order_date": "2026-03-06",
    "due_date": "2026-03-29",
    "status": "IN_PROGRESS",
    "current_stage": "WASHING",
    "last_activity_date": "2026-03-23",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "NEEDS_REVIEW",
  "expected_fields": {
    "order_id": "ORD-002",
    "pieces": 1000,
    "product": "Crewneck sweater",
    "due_date": "2026-03-29"
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-002",
    "batch.order_id": "ORD-002",
    "batch.category": "TOPS",
    "batch.pieces": 1000,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-03-29"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_configured_score_among_permitted_candidates",
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null,
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": false
  },
  "required_flags": [
    "PAST_DEADLINE",
    "NO_ON_TIME_OPTION",
    "SELECTED_OPTION_LATE"
  ],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "review_required",
      "tool_supported_options",
      "no_guaranteed_on_time_promise"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R29

Requester: Boss

Request: The vests need to go out this week — who takes them?

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-094",
    "customer": "Maple & Co",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "800",
    "order_date": "2026-01-09",
    "due_date": "2026-02-03",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-01-31",
    "completed_date": "2026-01-31",
    "days_late": "-3"
  },
  {
    "order_id": "ORD-021",
    "customer": "TrendCart",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "800",
    "order_date": "2026-01-17",
    "due_date": "2026-02-18",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-13",
    "completed_date": "2026-02-13",
    "days_late": "-5"
  },
  {
    "order_id": "ORD-006",
    "customer": "Northwind Apparel",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "150",
    "order_date": "2026-01-20",
    "due_date": "2026-02-20",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-04",
    "completed_date": "2026-02-04",
    "days_late": "-16"
  },
  {
    "order_id": "ORD-014",
    "customer": "TrendCart",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "2000",
    "order_date": "2026-01-27",
    "due_date": "2026-02-28",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-23",
    "completed_date": "2026-03-23",
    "days_late": "23"
  },
  {
    "order_id": "ORD-047",
    "customer": "Cotton Club",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "150",
    "order_date": "2026-02-03",
    "due_date": "2026-02-23",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-22",
    "completed_date": "2026-02-22",
    "days_late": "-1"
  },
  {
    "order_id": "ORD-085",
    "customer": "Harbor Knits",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "1500",
    "order_date": "2026-02-07",
    "due_date": "2026-03-01",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-05",
    "completed_date": "2026-03-05",
    "days_late": "4"
  },
  {
    "order_id": "ORD-050",
    "customer": "Northwind Apparel",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "500",
    "order_date": "2026-02-13",
    "due_date": "2026-03-05",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-02-28",
    "completed_date": "2026-02-28",
    "days_late": "-5"
  },
  {
    "order_id": "ORD-012",
    "customer": "Cotton Club",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "1200",
    "order_date": "2026-02-14",
    "due_date": "2026-03-09",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-08",
    "completed_date": "2026-03-08",
    "days_late": "-1"
  },
  {
    "order_id": "ORD-054",
    "customer": "TrendCart",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "600",
    "order_date": "2026-02-20",
    "due_date": "2026-03-06",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-29",
    "completed_date": "2026-03-29",
    "days_late": "23"
  },
  {
    "order_id": "ORD-037",
    "customer": "Cotton Club",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "200",
    "order_date": "2026-02-23",
    "due_date": "2026-03-18",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-20",
    "completed_date": "2026-03-20",
    "days_late": "2"
  },
  {
    "order_id": "ORD-104",
    "customer": "UrbanThread",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "200",
    "order_date": "2026-02-24",
    "due_date": "2026-03-28",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-11",
    "completed_date": "2026-03-11",
    "days_late": "-17"
  },
  {
    "order_id": "ORD-120",
    "customer": "TrendCart",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "1500",
    "order_date": "2026-02-27",
    "due_date": "2026-03-17",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-019",
    "customer": "Northwind Apparel",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "600",
    "order_date": "2026-03-02",
    "due_date": "2026-03-29",
    "status": "COMPLETE",
    "current_stage": "COMPLETE",
    "last_activity_date": "2026-03-29",
    "completed_date": "2026-03-29",
    "days_late": "0"
  },
  {
    "order_id": "ORD-020",
    "customer": "TrendCart",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "1200",
    "order_date": "2026-03-08",
    "due_date": "2026-03-31",
    "status": "IN_PROGRESS",
    "current_stage": "WASHING",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-109",
    "customer": "Harbor Knits",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "500",
    "order_date": "2026-03-10",
    "due_date": "2026-04-13",
    "status": "IN_PROGRESS",
    "current_stage": "WASHING",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-045",
    "customer": "Cotton Club",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "150",
    "order_date": "2026-03-21",
    "due_date": "2026-04-09",
    "status": "IN_PROGRESS",
    "current_stage": "WASHING",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-015",
    "customer": "UrbanThread",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "300",
    "order_date": "2026-03-23",
    "due_date": "2026-04-16",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-03-30",
    "completed_date": "",
    "days_late": ""
  },
  {
    "order_id": "ORD-024",
    "customer": "Loom & Leaf",
    "product": "Vest",
    "category": "TOPS",
    "pieces": "300",
    "order_date": "2026-03-24",
    "due_date": "2026-04-15",
    "status": "IN_PROGRESS",
    "current_stage": "ASSEMBLY",
    "last_activity_date": "2026-04-01",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "CLARIFY",
  "expected_fields": {
    "order_id": null,
    "product": "Vest",
    "due_date": null,
    "date_uncertain": false
  },
  "expected_resolved_fields": {},
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days",
    "due_date"
  ],
  "required_needs": [
    "order"
  ],
  "forbidden_needs": [],
  "expected_deferred_needs": null,
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "no_candidates_or_recommendation",
    "selection_predicate": null,
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null
  },
  "required_flags": [],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "targeted_clarification",
      "no_ranking_before_resolution"
    ],
    "forbidden_question_topics": [
      "omitted_retrievable_quantity",
      "omitted_retrievable_deadline"
    ],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: NEEDS_WORDING/EXPECTATION_REFINEMENT; unresolved: True.
- This week describes sending and does not establish an exact delivery deadline.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.
- Should absent and correctly deferred omitted secondary needs be accepted as equivalent?
- Does go out this week describe dispatch context only, or require later date-kind clarification after identifying the order?
- Should date_kind remain unspecified while due_date=null, and how is non-deferred deadline blocking rejected?

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________

## R30

Requester: Mei

Request: Please allocate ORD-099: 1500 polo shirts, Northwind Apparel. Deadline Apr 05.

### Relevant frozen source facts

~~~json
[
  {
    "order_id": "ORD-099",
    "customer": "Northwind Apparel",
    "product": "Polo shirt",
    "category": "TOPS",
    "pieces": "1500",
    "order_date": "2026-03-07",
    "due_date": "2026-04-05",
    "status": "IN_PROGRESS",
    "current_stage": "WASHING",
    "last_activity_date": "2026-03-31",
    "completed_date": "",
    "days_late": ""
  }
]
~~~

Index uses provisional order ID, else customer, else product: navigation aid, not approved resolution. Empty index is not proof of absence; consult full frozen orders.csv and workshop facts above.

### Provisional expectations (not gold)

~~~json
{
  "expected_status": "NEEDS_REVIEW",
  "expected_fields": {
    "order_id": "ORD-099",
    "pieces": 1500,
    "product": "Polo shirt",
    "customer": "Northwind Apparel",
    "due_date": "2026-04-05"
  },
  "expected_resolved_fields": {
    "order.order_id": "ORD-099",
    "batch.order_id": "ORD-099",
    "batch.category": "TOPS",
    "batch.pieces": 1500,
    "batch.sent_date": "2026-04-01",
    "batch.due_date": "2026-04-05"
  },
  "forbidden_fields": [
    "cost",
    "eta",
    "score",
    "turnaround_days"
  ],
  "required_needs": [],
  "forbidden_needs": [
    "order",
    "quantity",
    "deadline",
    "scope",
    "constraint_change"
  ],
  "expected_deferred_needs": [],
  "expected_constraints": {
    "exclusions": [],
    "split_requested": false
  },
  "expected_workshop_behavior": {
    "candidate_policy": "eligible_for_resolved_batch_and_not_excluded",
    "selection_predicate": "minimum_configured_score_among_permitted_candidates",
    "refused_workshop_id": null,
    "refusal_reason": null,
    "alternative_predicate": null,
    "tie_break": [
      "expected_turnaround_days",
      "workshop_id"
    ],
    "recommendation_must_be_on_time": false
  },
  "required_flags": [
    "NO_ON_TIME_OPTION",
    "SELECTED_OPTION_LATE"
  ],
  "forbidden_flags": [],
  "expected_response_behavior": {
    "commit_allowed": false,
    "reserve_capacity": false,
    "invent_order_or_estimate": false,
    "numerical_claims": "bound_to_matching_tool_field_workshop_and_snapshot",
    "required_concepts": [
      "review_required",
      "tool_supported_options",
      "no_guaranteed_on_time_promise"
    ],
    "forbidden_question_topics": [],
    "max_questions_per_topic": 1
  }
}
~~~

Review state: READY_FOR_GOLD; unresolved: False.
- All expectations are provisional development annotations, not independent gold. Historical output is not the expected answer.

### Independent reviewer entry

Reviewer decision: ____________________
Confidence: ____________________
Rationale: ____________________
Approved / rejected / modified: ____________________
Reviewer name: ____________________
Review date: ____________________
Proposed modifications / source evidence: ____________________
