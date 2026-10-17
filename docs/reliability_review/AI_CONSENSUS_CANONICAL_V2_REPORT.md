# Canonical multi-AI assertion consensus v2

"This is an AI-consensus benchmark based on independent canonical-v2 reviews. It is not human-adjudicated gold."

Independence is self-declared. The voting pool also retains exact-current legacy Gemini/DeepSeek cases; those are not retroactively described as canonical-v2 review sessions. Claude is inventoried but lacks qualifying request provenance.

## Reviewer pool and provenance quality

| ID | Model | Version | File | Canonical v2 | Set hash | Blind declaration | Prior-output risk | Usable cases |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Claude | Claude (file attribution only) | Not declared | docs/reliability_review/Part_A_Claude.docx | False | False | Yes, self-declared; independence not externally verified | No disclosed prior-output use; declaration only. File attribution/version not externally authenticated. | 0 |
| Gemini | Gemini (file attribution only) | Not declared | docs/reliability_review/Part_A_Gemini.pdf | False | False | Yes, self-declared; independence not externally verified | No disclosed prior-output use; declaration only. File attribution/version not externally authenticated. | 21 |
| DeepSeek | DeepSeek (file attribution only) | Not declared | docs/reliability_review/Part_A_DeepSeek.docx | False | False | Yes, self-declared; independence not externally verified | No disclosed prior-output use; declaration only. File attribution/version not externally authenticated. | 5 |
| Grok | Grok | 4.5 | docs/reliability_review/Reviewer_D_Grok_4.5_Canonical_V2.md | True | True | Yes, self-declared; independence not externally verified | No disclosed prior-output use; declaration only. File attribution/version not externally authenticated. | 30 |
| GPT | GPT-6 | Independent blind review v1.0 (review revision, not verified model build) | docs/reliability_review/AI_REVIEW_RESPONSE_COMPLETED_V2.md | True | True | Yes, self-declared; independence not externally verified | No disclosed prior-output use; declaration only. File attribution/version not externally authenticated. | 30 |

Non-voting files: docs/reliability_review/AI_CONSENSUS_ASSERTION_ADJUDICATION_V1.md; docs/reliability_review/AI_Consensus_Gold_v1_Review.xlsx; docs/reliability_review/AI_REVIEW_RESPONSE_TEMPLATE_V2.md; docs/reliability_review/CANONICAL_AI_REVIEW_PACKET_V2.md; docs/reliability_review/CANONICAL_REVIEW_PACKET_V2_MANIFEST.json; docs/reliability_review/Reviewer_D_Grok_4.5_QA.md

## Canonical request compatibility

| Case | Claude | Gemini | DeepSeek | Grok | GPT |
| --- | --- | --- | --- | --- | --- |
| R01 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | CORRUPTED_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R02 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | MISSING_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R03 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | MISSING_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R04 | SEMANTICALLY_DIFFERENT_REQUEST | SEMANTICALLY_DIFFERENT_REQUEST | SEMANTICALLY_DIFFERENT_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R05 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R06 | SEMANTICALLY_DIFFERENT_REQUEST | SEMANTICALLY_DIFFERENT_REQUEST | MISSING_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R07 | SEMANTICALLY_DIFFERENT_REQUEST | SEMANTICALLY_DIFFERENT_REQUEST | SEMANTICALLY_DIFFERENT_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R08 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R09 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | MISSING_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R10 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R11 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R12 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | MISSING_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R13 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | MISSING_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R14 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | MISSING_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R15 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | MISSING_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R16 | SEMANTICALLY_DIFFERENT_REQUEST | SEMANTICALLY_DIFFERENT_REQUEST | SEMANTICALLY_DIFFERENT_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R17 | SEMANTICALLY_DIFFERENT_REQUEST | SEMANTICALLY_DIFFERENT_REQUEST | SEMANTICALLY_DIFFERENT_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R18 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | MISSING_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R19 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | MISSING_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R20 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | MISSING_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R21 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | MISSING_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R22 | SEMANTICALLY_DIFFERENT_REQUEST | SEMANTICALLY_DIFFERENT_REQUEST | SEMANTICALLY_DIFFERENT_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R23 | SEMANTICALLY_DIFFERENT_REQUEST | SEMANTICALLY_DIFFERENT_REQUEST | SEMANTICALLY_DIFFERENT_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R24 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | MISSING_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R25 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | MISSING_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R26 | SEMANTICALLY_DIFFERENT_REQUEST | SEMANTICALLY_DIFFERENT_REQUEST | SEMANTICALLY_DIFFERENT_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R27 | SEMANTICALLY_DIFFERENT_REQUEST | SEMANTICALLY_DIFFERENT_REQUEST | SEMANTICALLY_DIFFERENT_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R28 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R29 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | MISSING_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |
| R30 | CANNOT_VERIFY | EXACT_CANONICAL_V2 | MISSING_REQUEST | EXACT_CANONICAL_V2 | EXACT_CANONICAL_V2 |

## Valid reviewer coverage

| Case | Valid reviewers | Count |
| --- | --- | --- |
| R01 | Gemini, Grok, GPT | 3 |
| R02 | Gemini, Grok, GPT | 3 |
| R03 | Gemini, Grok, GPT | 3 |
| R04 | Grok, GPT | 2 |
| R05 | Gemini, DeepSeek, Grok, GPT | 4 |
| R06 | Grok, GPT | 2 |
| R07 | Grok, GPT | 2 |
| R08 | Gemini, DeepSeek, Grok, GPT | 4 |
| R09 | Gemini, Grok, GPT | 3 |
| R10 | Gemini, DeepSeek, Grok, GPT | 4 |
| R11 | Gemini, DeepSeek, Grok, GPT | 4 |
| R12 | Gemini, Grok, GPT | 3 |
| R13 | Gemini, Grok, GPT | 3 |
| R14 | Gemini, Grok, GPT | 3 |
| R15 | Gemini, Grok, GPT | 3 |
| R16 | Grok, GPT | 2 |
| R17 | Grok, GPT | 2 |
| R18 | Gemini, Grok, GPT | 3 |
| R19 | Gemini, Grok, GPT | 3 |
| R20 | Gemini, Grok, GPT | 3 |
| R21 | Gemini, Grok, GPT | 3 |
| R22 | Grok, GPT | 2 |
| R23 | Grok, GPT | 2 |
| R24 | Gemini, Grok, GPT | 3 |
| R25 | Gemini, Grok, GPT | 3 |
| R26 | Grok, GPT | 2 |
| R27 | Grok, GPT | 2 |
| R28 | Gemini, DeepSeek, Grok, GPT | 4 |
| R29 | Gemini, Grok, GPT | 3 |
| R30 | Gemini, Grok, GPT | 3 |

## Status consensus

| Case | Status | Consensus | Votes | Policy sensitive |
| --- | --- | --- | --- | --- |
| R01 | CLARIFY | HIGH_CONSENSUS | Gemini=CLARIFY; Grok=CLARIFY; GPT=CLARIFY | True |
| R02 | DECLINE | HIGH_CONSENSUS | Gemini=DECLINE; Grok=DECLINE; GPT=DECLINE | False |
| R03 | CLARIFY | HIGH_CONSENSUS | Gemini=CLARIFY; Grok=CLARIFY; GPT=CLARIFY | True |
| R04 | RECOMMEND_ALLOCATE | LIMITED_CONSENSUS | Grok=RECOMMEND_ALLOCATE; GPT=RECOMMEND_ALLOCATE | False |
| R05 | CLARIFY | MAJORITY | Gemini=CLARIFY; DeepSeek=CLARIFY; Grok=CLARIFY; GPT=RECOMMEND_ALLOCATE | True |
| R06 | UNRESOLVED | UNRESOLVED | Grok=RECOMMEND_ALLOCATE; GPT=CLARIFY | True |
| R07 | RECOMMEND_ALLOCATE | LIMITED_CONSENSUS | Grok=RECOMMEND_ALLOCATE; GPT=RECOMMEND_ALLOCATE | False |
| R08 | REFUSE_SUGGESTION | HIGH_CONSENSUS | Gemini=REFUSE_SUGGESTION; DeepSeek=REFUSE_SUGGESTION; Grok=REFUSE_SUGGESTION; GPT=REFUSE_SUGGESTION | False |
| R09 | RECOMMEND_ALLOCATE | HIGH_CONSENSUS | Gemini=RECOMMEND_ALLOCATE; Grok=RECOMMEND_ALLOCATE; GPT=RECOMMEND_ALLOCATE | False |
| R10 | CLARIFY | HIGH_CONSENSUS | Gemini=CLARIFY; DeepSeek=CLARIFY; Grok=CLARIFY; GPT=CLARIFY | True |
| R11 | REFUSE_SUGGESTION | HIGH_CONSENSUS | Gemini=REFUSE_SUGGESTION; DeepSeek=REFUSE_SUGGESTION; Grok=REFUSE_SUGGESTION; GPT=REFUSE_SUGGESTION | False |
| R12 | RECOMMEND_ALLOCATE | HIGH_CONSENSUS | Gemini=RECOMMEND_ALLOCATE; Grok=RECOMMEND_ALLOCATE; GPT=RECOMMEND_ALLOCATE | False |
| R13 | DECLINE | HIGH_CONSENSUS | Gemini=DECLINE; Grok=DECLINE; GPT=DECLINE | False |
| R14 | REFUSE_SUGGESTION | HIGH_CONSENSUS | Gemini=REFUSE_SUGGESTION; Grok=REFUSE_SUGGESTION; GPT=REFUSE_SUGGESTION | False |
| R15 | CLARIFY | HIGH_CONSENSUS | Gemini=CLARIFY; Grok=CLARIFY; GPT=CLARIFY | True |
| R16 | UNRESOLVED | UNRESOLVED | Grok=RECOMMEND_ALLOCATE; GPT=CLARIFY | True |
| R17 | RECOMMEND_ALLOCATE | LIMITED_CONSENSUS | Grok=RECOMMEND_ALLOCATE; GPT=RECOMMEND_ALLOCATE | False |
| R18 | CLARIFY | MAJORITY | Gemini=DECLINE; Grok=CLARIFY; GPT=CLARIFY | True |
| R19 | CLARIFY | HIGH_CONSENSUS | Gemini=CLARIFY; Grok=CLARIFY; GPT=CLARIFY | True |
| R20 | RECOMMEND_ALLOCATE | HIGH_CONSENSUS | Gemini=RECOMMEND_ALLOCATE; Grok=RECOMMEND_ALLOCATE; GPT=RECOMMEND_ALLOCATE | True |
| R21 | RECOMMEND_ALLOCATE | HIGH_CONSENSUS | Gemini=RECOMMEND_ALLOCATE; Grok=RECOMMEND_ALLOCATE; GPT=RECOMMEND_ALLOCATE | True |
| R22 | RECOMMEND_ALLOCATE | LIMITED_CONSENSUS | Grok=RECOMMEND_ALLOCATE; GPT=RECOMMEND_ALLOCATE | False |
| R23 | NEEDS_REVIEW_ESCALATE | LIMITED_CONSENSUS | Grok=NEEDS_REVIEW_ESCALATE; GPT=NEEDS_REVIEW_ESCALATE | True |
| R24 | REFUSE_SUGGESTION | HIGH_CONSENSUS | Gemini=REFUSE_SUGGESTION; Grok=REFUSE_SUGGESTION; GPT=REFUSE_SUGGESTION | False |
| R25 | RECOMMEND_ALLOCATE | HIGH_CONSENSUS | Gemini=RECOMMEND_ALLOCATE; Grok=RECOMMEND_ALLOCATE; GPT=RECOMMEND_ALLOCATE | False |
| R26 | RECOMMEND_ALLOCATE | LIMITED_CONSENSUS | Grok=RECOMMEND_ALLOCATE; GPT=RECOMMEND_ALLOCATE | False |
| R27 | RECOMMEND_ALLOCATE | LIMITED_CONSENSUS | Grok=RECOMMEND_ALLOCATE; GPT=RECOMMEND_ALLOCATE | False |
| R28 | RECOMMEND_ALLOCATE | MAJORITY | Gemini=RECOMMEND_ALLOCATE; DeepSeek=RECOMMEND_ALLOCATE; Grok=RECOMMEND_ALLOCATE; GPT=CLARIFY | True |
| R29 | CLARIFY | HIGH_CONSENSUS | Gemini=CLARIFY; Grok=CLARIFY; GPT=CLARIFY | True |
| R30 | RECOMMEND_ALLOCATE | HIGH_CONSENSUS | Gemini=RECOMMEND_ALLOCATE; Grok=RECOMMEND_ALLOCATE; GPT=RECOMMEND_ALLOCATE | True |

## Assertion consensus counts

{
  "UNRESOLVED": 552,
  "HIGH_CONSENSUS": 137,
  "LIMITED_CONSENSUS": 154,
  "MAJORITY": 5
}

Count unit: unique case/assertion keys, including explicit prose-detail assertions. These are not independent observations or model accuracy. Prose preserved with different wording remains unresolved unless enough identical values exist.

## Coverage by family

| Family | Scoreable | Case suppressed | Unsupported | Unresolved |
| --- | --- | --- | --- | --- |
| deferred_needs | 6 | 0 | 0 | 45 |
| needs | 1 | 9 | 4 | 48 |
| field_prohibitions | 0 | 0 | 0 | 43 |
| flags | 0 | 0 | 14 | 74 |
| operational_predicates | 0 | 0 | 32 | 280 |
| primary_status | 21 | 7 | 0 | 2 |
| supported_fields | 118 | 46 | 8 | 60 |
| exclusions | 21 | 9 | 0 | 0 |

## Policy-sensitive disagreements

Always-sensitive IDs: R01, R03, R06, R10, R15, R16, R19, R23, R29

Status agreement never implies needs/deferred-needs agreement. R06/R16 retain shipping-semantics disagreement. R23 primary status, simulator single-workshop rule and split extension predicate are separate. Alternative workshops are not automatically clarification needs.

## Newly identified policy-sensitive cases

- R05: Primary behavior disagreement: {"DeepSeek": "CLARIFY", "GPT": "RECOMMEND_ALLOCATE", "Gemini": "CLARIFY", "Grok": "CLARIFY"}
- R18: Primary behavior disagreement: {"GPT": "CLARIFY", "Gemini": "DECLINE", "Grok": "CLARIFY"}
- R20: Past-deadline or tool-dependent feasibility/ranking policy requires adjudication
- R21: Past-deadline or tool-dependent feasibility/ranking policy requires adjudication
- R28: Primary behavior disagreement: {"DeepSeek": "RECOMMEND_ALLOCATE", "GPT": "CLARIFY", "Gemini": "RECOMMEND_ALLOCATE", "Grok": "RECOMMEND_ALLOCATE"}
- R30: Past-deadline or tool-dependent feasibility/ranking policy requires adjudication

## Unresolved assertions

All vote values, dissent and exclusion reasons are in the provenance ledger. Exact unresolved keys:

- R01: clarification.deferred_needs_detail, clarification.deferred_needs_exact, clarification.required_needs_detail, field_prohibitions.forbidden_fields.guessed_order_identity, field_prohibitions.forbidden_fields.ungrounded_eta, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.AMBIGUOUS_DEADLINE_VS_DISPATCH, flags.required_flags.AMBIGUOUS_QUANTITY, flags.required_flags.MISSING_ORDER_ID, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.no_fabricated_eta, operational_predicates.ranking_requires_tool, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, supported_fields.date_semantics, supported_fields.preference, supported_fields.quantity

- R02: clarification.deferred_needs_detail, clarification.required_needs_detail, clarification.required_needs_exact, field_prohibitions.forbidden_fields.fabricated_history, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.NO_LEDGER_DATA, flags.required_flags.UNSUPPORTED_HISTORICAL_QUERY, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.split_handling, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, supported_fields.date_semantics

- R03: clarification.deferred_needs_detail, clarification.deferred_needs_exact, clarification.required_needs.deadline, clarification.required_needs.quantity, clarification.required_needs_detail, field_prohibitions.forbidden_fields.guessed_order_identity, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.AMBIGUOUS_CUSTOMER_MULTIPLE_ORDERS, flags.required_flags.MISSING_ORDER_ID, flags.required_flags_concept.past_deadline, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.infeasibility_disclosure, operational_predicates.named_workshop_refusal_reason, operational_predicates.past_deadline_disclosure, operational_predicates.ranking_requires_tool, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, supported_fields.date_semantics, supported_fields.due_date, supported_fields.preference

- R04: clarification.deferred_needs_detail, clarification.required_needs_detail, field_prohibitions.forbidden_fields.ungrounded_eta, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.no_fabricated_eta, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, operational_predicates.workshop_hard_eligibility_ids, supported_fields.date_semantics

- R05: clarification.deferred_needs_detail, clarification.deferred_needs_exact, clarification.required_needs_detail, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.PREMATURE_ALLOCATION_RISK, flags.required_flags.UNCONFIRMED_DEADLINE_CHANGE, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.no_fabricated_eta, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, operational_predicates.workshop_hard_eligibility_ids, supported_fields.customer, supported_fields.date_semantics, supported_fields.preference, supported_fields.product, supported_fields.quantity

- R06: clarification.deferred_needs_detail, clarification.required_needs_detail, field_prohibitions.forbidden_fields.ungrounded_eta, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags_concept.date_semantics_ambiguity, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.no_fabricated_eta, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, primary_status.status, supported_fields.date_semantics, supported_fields.due_date

- R07: clarification.deferred_needs_detail, clarification.required_needs_detail, clarification.required_needs_exact, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, supported_fields.date_semantics

- R08: clarification.deferred_needs_detail, clarification.required_needs_detail, clarification.required_needs_exact, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.HARD_BATCH_CAP_EXCEEDED, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.split_handling, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, operational_predicates.workshop_hard_eligibility_ids, supported_fields.customer, supported_fields.date_semantics

- R09: clarification.deferred_needs_detail, clarification.deferred_needs_exact, clarification.required_needs_detail, clarification.required_needs_exact, field_prohibitions.forbidden_fields.ungrounded_eta, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.SPEED_PRIORITY_OVER_COST, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.no_fabricated_eta, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, supported_fields.date_semantics

- R10: clarification.deferred_needs_detail, clarification.deferred_needs_exact, clarification.required_needs_detail, field_prohibitions.forbidden_fields.guessed_order_identity, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.MISSING_ORDER_DETAILS, flags.required_flags.UNSUPPORTED_CAPACITY_BOOKING_WORKFLOW, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.ranking_requires_tool, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, supported_fields.date_semantics, supported_fields.preference

- R11: clarification.deferred_needs_detail, clarification.required_needs_detail, clarification.required_needs_exact, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.SUSPENDED_WORKSHOP_INELIGIBILITY, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.explicit_exclusion_workshop_ids, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.ranking_requires_tool, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, operational_predicates.workshop_hard_eligibility_ids, supported_fields.customer, supported_fields.date_semantics, supported_fields.due_date, supported_fields.product, supported_fields.quantity

- R12: clarification.deferred_needs_detail, clarification.deferred_needs_exact, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.USER_EXCLUSION_QUICKSTITCH, flags.required_flags_concept.explicit_exclusion, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, operational_predicates.workshop_hard_eligibility_ids, supported_fields.date_semantics, supported_fields.suggested_workshop

- R13: clarification.deferred_needs_detail, clarification.required_needs_detail, clarification.required_needs_exact, field_prohibitions.forbidden_fields.fabricated_quote, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.NO_PRICING_LEDGER, flags.required_flags.UNSUPPORTED_CUSTOMER_QUOTE_PRICE_QUERY, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.no_fabricated_quote, operational_predicates.split_handling, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, supported_fields.date_semantics, supported_fields.due_date, supported_fields.product, supported_fields.quantity, supported_fields.retrieved.customer, supported_fields.retrieved.quantity

- R14: clarification.deferred_needs_detail, clarification.required_needs_detail, clarification.required_needs_exact, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.CATEGORY_INCOMPATIBILITY, flags.required_flags_concept.category_mismatch, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.named_workshop_refusal_reason_code, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, operational_predicates.workshop_hard_eligibility_ids, supported_fields.date_semantics, supported_fields.preference

- R15: clarification.deferred_needs_detail, clarification.deferred_needs_exact, clarification.required_needs_detail, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.MISSING_ORDER_ID, flags.required_flags.MULTIPLE_ORDERS_FOR_CUSTOMER, flags.required_flags.UNPRECISE_DEADLINE, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.past_deadline_disclosure, operational_predicates.ranking_requires_tool, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, supported_fields.date_semantics, supported_fields.preference

- R16: clarification.deferred_needs_detail, clarification.required_needs_detail, field_prohibitions.forbidden_fields.ungrounded_eta, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags_concept.date_semantics_ambiguity, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.no_fabricated_eta, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, primary_status.status, supported_fields.date_semantics

- R17: clarification.deferred_needs_detail, clarification.required_needs_detail, clarification.required_needs_exact, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.no_fabricated_history, operational_predicates.past_deadline_disclosure, operational_predicates.ranking_requires_tool, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, operational_predicates.workshop_hard_eligibility_ids, supported_fields.date_semantics

- R18: clarification.deferred_needs_detail, clarification.deferred_needs_exact, clarification.required_needs.order, clarification.required_needs_detail, clarification.required_needs_exact, field_prohibitions.forbidden_fields.guessed_order_identity, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.NON_EXISTENT_ORDER_ID, flags.required_flags.UNSUPPORTED_SYNTHESIS, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.split_handling, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, supported_fields.date_semantics

- R19: clarification.deferred_needs_detail, clarification.deferred_needs_exact, clarification.required_needs_detail, field_prohibitions.forbidden_fields.ungrounded_eta, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.MISSING_ORDER_ID, flags.required_flags.VAGUE_ORDER_REFERENCE, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.no_fabricated_eta, operational_predicates.past_deadline_disclosure, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, supported_fields.date_semantics, supported_fields.due_date, supported_fields.quantity

- R20: clarification.deferred_needs_detail, clarification.deferred_needs_exact, clarification.required_needs_detail, clarification.required_needs_exact, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.STANDARD_ALLOCATION_CHECK_FEASIBILITY, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, supported_fields.date_semantics

- R21: clarification.deferred_needs_detail, clarification.deferred_needs_exact, clarification.required_needs_detail, clarification.required_needs_exact, field_prohibitions.forbidden_fields.ungrounded_eta, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.COST_MINIMIZATION_WITH_DEADLINE_CONSTRAINT, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.no_fabricated_eta, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, operational_predicates.workshop_hard_eligibility_ids, supported_fields.date_semantics

- R22: clarification.deferred_needs_detail, clarification.required_needs_detail, clarification.required_needs_exact, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.KNITTING, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.ranking_requires_tool, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, operational_predicates.workshop_hard_eligibility_ids, supported_fields.date_semantics, supported_fields.preference

- R23: clarification.deferred_needs_detail, clarification.required_needs_detail, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags_concept.split_review, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.ranking_requires_tool, operational_predicates.split_handling, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, supported_fields.date_semantics

- R24: clarification.deferred_needs_detail, clarification.required_needs_detail, clarification.required_needs_exact, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.CATEGORY_INCOMPATIBILITY, flags.required_flags_concept.category_mismatch, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.named_workshop_refusal_reason_code, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, operational_predicates.workshop_hard_eligibility_ids, supported_fields.date_semantics

- R25: clarification.deferred_needs_detail, clarification.deferred_needs_exact, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.USER_EXCLUSION_BUDGETWORKS, flags.required_flags_concept.explicit_exclusion, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, operational_predicates.workshop_hard_eligibility_ids, supported_fields.date_semantics, supported_fields.suggested_workshop

- R26: clarification.deferred_needs_detail, clarification.required_needs_detail, clarification.required_needs_exact, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, supported_fields.date_semantics, supported_fields.preference

- R27: clarification.deferred_needs_detail, clarification.required_needs_detail, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.no_fabricated_eta, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.static_lowest_defect_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, operational_predicates.workshop_hard_eligibility_ids, supported_fields.date_semantics

- R28: clarification.deferred_needs_detail, clarification.deferred_needs_exact, clarification.required_needs_detail, clarification.required_needs_exact, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.PAST_DEADLINE, flags.required_flags.QUEUE_CAPACITY_RANKING, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.ranking_requires_tool, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, supported_fields.customer, supported_fields.date_semantics

- R29: clarification.deferred_needs_detail, clarification.deferred_needs_exact, clarification.required_needs.quantity, clarification.required_needs_detail, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.MISSING_ORDER_ID, flags.required_flags.MULTIPLE_VEST_ORDERS_EXISTS, flags.required_flags.VAGUE_DEADLINE, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.past_deadline_disclosure, operational_predicates.ranking_requires_tool, operational_predicates.split_handling, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, supported_fields.date_semantics

- R30: clarification.deferred_needs_detail, clarification.deferred_needs_exact, clarification.required_needs_detail, clarification.required_needs_exact, field_prohibitions.forbidden_needs_fields_flags_detail, flags.required_flags.STANDARD_ALLOCATION_COMPLETE, flags.required_flags_detail, operational_predicates.deadline_behavior_detail, operational_predicates.explicit_exclusion_application, operational_predicates.historical_query_behavior_detail, operational_predicates.named_workshop_refusal_reason, operational_predicates.no_fabricated_eta, operational_predicates.split_handling, operational_predicates.split_simulator_single_workshop, operational_predicates.unknown_order_behavior_detail, operational_predicates.workshop_hard_eligibility, supported_fields.date_semantics, supported_fields.due_date

## Cases with low reviewer coverage

R04, R06, R07, R16, R17, R22, R23, R26, R27

Two agreeing explicit votes yield LIMITED_CONSENSUS only. Individual assertions can have lower coverage than their case.

## Tool-dependent assertions

ETA, fastest and cheapest-on-time choices are not gold-labelled. Explicit ranking/tool requirements are retained in the ledger; they cannot be executed by the current semantic scorer. R27's explicitly supported W2 static defect preference is preserved separately from delivery ranking and is metadata-only. No numerical formula or winner is invented.

## Scorer compatibility

validate_benchmark passed. No score_case, score_run, replay or CLI scoring was invoked.

{
  "suppressed_unresolved": 552,
  "case_suppressed": 71,
  "unsupported_by_current_scorer": 58,
  "scoreable": 167
}

Current limitations: src/dss5105/reliability_score.py:515 hardcodes nine unresolved IDs and suppresses all semantic checks in those cases; :723 requires an exact exclusion set even when no exclusion assertion is approved. expected_status=None and empty field/list expectations can omit other checks. Generic operational predicates and natural-language flags are not evaluated. Forbidden-needs checks also inspect deferred needs, so a current-question prohibition cannot be mapped without stronger evidence. The approved consensus_assertions extension is metadata, not executable scorer coverage.

Cases requiring the case gate: R01, R03, R06, R10, R15, R16, R19, R23, R29

Smallest proposed change, not implemented: an optional per-assertion approval/skip map, including a nullable exact exclusion expectation; retain existing behavior for benchmarks without that map. Replace the hardcoded case suppression only for explicitly approved v2 assertions. Generic operational predicates need separately specified evaluators; do not silently map them to current symbolic flags.

## Original provisional versus canonical v2

{
  "retained_unchanged": 175,
  "removed_or_suppressed": 486,
  "newly_declared": 59,
  "changed": 4
}

Comparison covers executable declaration keys, not all prose or implicit aggregate checks. Newly declared does not mean executable: each comparison row has canonical_v2_scoreable. Full retained/changed/removed/new keys and old/new values are in provenance.provisional_comparison. Original assertions are not used as votes.

## Limitations

Conservative normalization deliberately leaves distinct prose and conditional dependency statements unresolved. Some potentially equivalent statements need human mapping; no silence is treated as a negative vote. Self-declared AI identity and blindness are not independently authenticated. Legacy reviews have weaker fact coverage than the new packet. No benchmark is true gold. Schema-valid does not mean all consensus predicates are scoreable.

## Validation and protection

All canonical case identities and hashes retained; 90 protected files unchanged. No live calls, full scoring, staging, commits or scorer changes. Generated files are new v2 artifacts only.

## Additional extraction checks

Retrieved catalog attributes are kept separate as supported_fields.retrieved.* and mapped only to expected_resolved_fields.order.*. Reference-clock dates such as 'last week relative to 2026-04-01' are never mapped to due_date. R12 and R27 retain the Grok/GPT disagreement over W8 eligibility; these are factual reviewer disagreements, not a new business policy. R27 W2 has only one explicit winner vote and therefore remains unresolved, despite being a permitted static comparison.

Newly declared executable-key assertions: 59; of these, 38 are scoreable under current case gates. The remainder are case-suppressed.

## Safe to offline rescore?

Yes only as a partial, explicitly scoped AI-consensus diagnostic using the enabled native assertions. No full canonical assertion-coverage or gold claim is supported. For full assertion-level evaluation, implement and validate the proposed compatibility change only after separate authorization. No rescoring was performed.
