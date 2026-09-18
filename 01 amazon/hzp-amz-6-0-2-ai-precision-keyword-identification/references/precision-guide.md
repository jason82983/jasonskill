# 6-0-2 Precision Guide

This reference fixes the business judgment standard. It does not prescribe an execution state machine.

## Runtime Product Profile

Read the complete Current Product text. Build one profile for the full run with these concepts where evidence exists:

- ProductType and PhysicalProductForm
- CoreFunctions and CorePurchaseMission
- PrimaryPurchaseDriver and SecondaryPurchaseDrivers
- TargetAudience, Recipient and RelationshipIntent
- GiftMission and PurchaseOccasions
- Material, Theme, Style and UseCases
- CriticalAttributes, Compatibility and InstallationMethod
- ExplicitExclusions

Use `DATA_NOT_AVAILABLE` for missing evidence and `NOT_APPLICABLE` when a concept does not apply. Product facts come from the source text, not from typical category assumptions.

## Judgment kernel

For each canonical keyword:

1. State the dominant Searcher Purchase Mission.
2. Run the Hard Conflict Gate before grading strength. A clear product type, relationship, recipient, brand, personalization, material/feature, compatibility or theme conflict is a veto and normally returns `不精准`.
3. Assign the Current Product Answer Role: `NATURAL_CORE_ANSWER`, `REASONABLE_ANSWER`, `ONE_OF_MANY_POSSIBLE_ANSWERS` or `NOT_A_VALID_ANSWER`.
4. Compare the mission with the Current Product Core Purchase Mission and assess Purchase Mission Convergence.
5. Set Initial Precision.
6. Interpret Benchmark Organic Rank only as evidence that the Benchmark has ranking reality for this query.
7. Run the Decision Challenge and the counterfactual test.
8. Return FinalPrecision and a short, keyword-specific reason.

## Four levels

- `高度精准`: the dominant purchase mission is highly aligned, the product is a `NATURAL_CORE_ANSWER`, requirements are concentrated, and no key conflict exists. If many ordinary products in the broad category would satisfy the query just as naturally, do not use `高度精准`.
- `精准`: the dominant mission clearly matches and the product is a reasonable answer, but the search space is broader.
- `弱精准`: a real relationship exists, but intent is broad, adjacent or underspecified; the product is only one of many possible answers. “The product can be used as a gift” is insufficient for Selected admission.
- `不精准`: the dominant mission seeks another product or solution, or a key requirement conflicts.

Do not calculate a hidden numerical score and map it to these levels.

## PrimaryPurchaseDriver

The PrimaryPurchaseDriver changes which facts matter most. For `GIFT_EMOTIONAL`, reason mainly from:

- gift mission,
- recipient,
- relationship,
- occasion,
- emotional message.

A strong emotional-gift query does not need to contain `figurine`, `statue` or `decor`. Conversely, the presence of those product-form tokens does not make a query precise when its purchase mission conflicts.

## Hard conflicts

At minimum consider:

- `PRODUCT_TYPE_CONFLICT`
- `RELATIONSHIP_CONFLICT`
- `RECIPIENT_CONFLICT`
- `BRAND_CONFLICT`
- `PERSONALIZATION_CONFLICT`
- `MATERIAL_FEATURE_CONFLICT`
- `COMPATIBILITY_CONFLICT`

Describe the actual conflict. A hard conflict is checked before intensity grading and cannot be cancelled by a related word, gift wording, product-form token, high search volume or good Benchmark rank.

## Answer-role and counterfactual challenge

- `NATURAL_CORE_ANSWER`: only then consider `高度精准`.
- `REASONABLE_ANSWER`: may support `精准` when the mission is sufficiently converged.
- `ONE_OF_MANY_POSSIBLE_ANSWERS`: normally `弱精准`, even when the product could satisfy the request.
- `NOT_A_VALID_ANSWER`: `不精准`.

Before assigning `高度精准`, ask whether many ordinary products in the broad category would satisfy the search mission just as naturally. If yes, the query is too broad for `高度精准`. This is a general semantic decision test, not a keyword list or deterministic special case.

## Benchmark Reality

Organic rank is supporting reality evidence. Semantic judgment comes first. Never use `good rank = high precision`, and never treat Benchmark rank as Current Product rank.

Before finalizing, ask:

- Did token overlap replace purchase-mission reasoning?
- Did broad tokens such as `sister`, `gift` or `women` inflate the level?
- Did product-form tokens such as `figurine`, `statue` or `decor` inflate it?
- Did the judgment wrongly penalize a high-fit gift mission because the product form was omitted?
- Is there an unresolved hard conflict?
- Did a clear hard conflict reach Selected despite the veto gate?
- Is the product a natural core answer, merely reasonable, one of many possible answers, or not a valid answer?
- Would the result survive the counterfactual “many ordinary products also satisfy it” challenge?
- Would the semantic result still stand if Benchmark rank were removed?

## Accepted calibration scale

These are reasoning anchors for the Agent, not code rules:

| Keyword | Accepted level |
|---|---|
| sister birthday gifts | 高度精准 |
| friendship gifts for women | 高度精准 |
| big sister gift | 高度精准 |
| best friend gifts for women | 高度精准 |
| birthday gifts for women | 精准 |
| gifts for women | 弱精准 |
| birthday gifts | 弱精准 |
| gift | 弱精准 |
| sister | 弱精准 |
| jim shore angels figurines | 不精准 |
| sister candles from sister funny | 不精准 |
| sister blankets from sister | 不精准 |
| mother and daughter statue | 不精准 |
| small angel figurines | 不精准 |

Apply the principles to new keywords. Do not hard-code these strings in deterministic code.

## AI judgment handoff schema

Each unique canonical keyword judgment supplied to deterministic validation contains:

- `KeywordId`
- `CanonicalKeyword`
- `SearcherPurchaseMission`
- `MissionFit`
- `HardConflict`
- `InitialPrecision`
- `BenchmarkReality`
- `DecisionChallenge`
- `FinalPrecision`
- `ShortReason`

`FinalPrecision` must use one of the four official levels. `ShortReason` must name the decisive purchase mission or conflict and must not be copied mechanically across unrelated keywords.
