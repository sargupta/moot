# Moot
## Stress-test high-stakes decisions against a panel of synthetic experts.

> **One line.** Moot puts your hardest question to ten distinct AI personas — each with a generated 60-year life, five formative books, a 12-axis ideology — and produces a synthesis, an executive brief, and a Register of Dissent surfacing the strongest case the majority brushed off. 50 seconds. ~₹6.50 per debate.

---

## The problem

The most consequential decisions in policy, frontier AI, and Big Law are made with *insufficient adversarial vetting*. Not because the decision-makers are careless — because the deliberation that should be happening is bottlenecked on the cost and slowness of recruiting humans with the right combination of expertise, ideology, demographic background, and willingness to argue in good faith.

| Decision class | What's being paid for today | What's missed |
|---|---|---|
| **Frontier-model release** | Internal red-team reviews, eval benchmarks (MMLU, HELM), 6-12 person external red-teams | Failure modes outside the lab's own cultural / linguistic / ideological distribution |
| **Pre-trial litigation** | $200K–$2M jury consultants, 6-person mock juries | Statistical sample of size O(10); narrow demographic coverage |
| **Public-policy schemes** | Ministry technical teams, Standing Committees, McKinsey-class engagements | Pragmatist field perspective; minority stakeholder voices |
| **Board-level corporate** | $1–10M consulting engagements, board sessions | Diverse-stakeholder simulation; load-bearing dissent |

The structural failure is the same across all four: deliberation gets compressed to a small number of voices that share enough background to fail in correlated ways.

## What we built

**Moot** runs ten distinct synthetic personas through a four-round structured debate (opening · cross-examination · rebuttal · closing). Belief positions evolve under Friedkin-Johnsen dynamics with bounded confidence — a model that *prevents* mode collapse to consensus while still allowing genuine persuasion. Claims get extracted into a Toulmin argument graph, ranked by personalised PageRank. The strongest minority view is surfaced by a *surprisal × centrality* dissent score.

Three artefacts come out:

1. **Synthesis article** (~1,200 words) — extractively assembled from PageRank-ranked claims; every sentence stays attributed.
2. **Executive remark** (~200 words) — central claims, stance distribution, the brief a CEO/minister actually reads.
3. **Register of Dissent** — the load-bearing minority case, with a *Steelman* generator that writes the strongest defensible version of it.

**Wall-clock**: 40–60 seconds per debate. **Cost**: ~₹6.50 (Gemini 2.5 Flash) to ~₹25 (Anthropic Sonnet 4.6).

Four chambers ship today: **Citizens & Stakeholders** (default — Indian civic archetypes for ministry / public-policy / enterprise debates), **Investors & Mentors**, **AI-Lab Evaluators**, **Defense**. Each is a hand-curated panel of ten archetypes with full life narratives + 5 formative books each.

**Every persona is synthetic.** No persona represents any real person.

---

## What's distinctive

| | Multi-agent frameworks (CrewAI, AutoGen, LangGraph) | Eval vendors (Scale, Patronus, Surge) | Civic-tech (Polis, vTaiwan) | **Moot** |
|---|---|---|---|---|
| Curated stakeholder chambers | — | — | — | **✓** |
| Structured 4-round debate format | — | — | — | **✓** |
| Dissent as first-class output | — | — | — | **✓** |
| Synthetic agents (not human voting) | ✓ | ✓ | — | **✓** |
| Productised, not framework | — | ✓ | ✓ | **✓** |

Three things competitors do not ship:

1. **Curated chambers, not generic personas.** Each panel is hand-built around a decision class. The Indian schoolteacher persona has read Bama and Ambedkar. The IAS officer has read Scott and Ahluwalia. The auto-rickshaw driver has read Tukaram and Sane Guruji. When the chamber debates a Ministry of Education scheme, those reading-list anchors *show* in the arguments. The chambers feel like real rooms.

2. **Dissent as a first-class output.** Most multi-agent systems collapse to consensus. Moot's design *prevents* it (Friedkin-Johnsen stubbornness floor; bounded confidence; cluster-entropy floor at 0.42 nats, monitored every round). The Register of Dissent is the value-prop, not the synthesis article.

3. **Extractive synthesis, not generative.** Claims are sequenced and framed but never re-written. Attribution stays clean. The output cannot be retroactively edited to manufacture a position the agents never took.

---

## Who buys

Three Wedges, ranked by validation difficulty:

### Wedge A — Frontier AI labs and large LLM-API enterprise customers
**Buyer**: alignment / post-training / safety teams at Anthropic, OpenAI, DeepMind, Cohere, Mistral, Meta FAIR, plus enterprise eval teams at top-tier banks, insurers, healthcare systems.

**Pain today**: $5–25M annual internal eval spend per lab; persona / red-team coverage that systematically over-samples the lab's own cultural distribution.

**Pricing**: $50K–$300K ARR per seat. Procurement: technical buyer, <90 days.

### Wedge B — Big Law pre-trial simulation
**Buyer**: AmLaw 100, Magic Circle, top-tier Indian litigation firms.

**Pain today**: $200K–$2M jury-consultant engagements per major case; 6–12 person mock juries; demographic coverage limited by who walks in for $200/day.

**Pricing**: $50K–$500K per case, or $250K–$1M ARR per firm. Procurement: 4–9 months, partner-level buyer.

### Wedge C — Public-policy / civic-tech (India focus)
**Buyer**: think tanks (ORF, IDSA, Takshashila), civic-tech foundations, ministry consulting cells (longer sales cycle).

**Pain today**: small staff, limited consultative bandwidth; ministry policy gets stress-tested by 5-person committees instead of stakeholder-diverse panels.

**Pricing**: ₹15–50 lakh / year per think tank. Lower margin, longer sales.

**Recommended go-to-market**: A + B in parallel. C as a strategic pilot relationship, not commercial primary.

---

## Economics

### Per-debate unit economics

| Provider | Cost / debate | Wall-clock |
|---|---|---|
| Mock (offline) | ₹0 | <1 s |
| Gemini 2.5 Flash | ~₹6.50 | ~50 s |
| Anthropic Sonnet 4.6 | ~₹25 | ~30 s |

### Pricing intent

| Tier | Price | Includes |
|---|---|---|
| Researcher / individual | ₹50K / month | 50 debates, public chambers, hosted |
| Enterprise standard | ₹3–5 lakh / month | 500 debates, custom chambers, SLA |
| Enterprise air-gapped | ₹50L–5cr / year | On-prem, custom chambers, SOC 2 / DPDP / ISO 27001 |

**Gross margin** at scale: >85% on hosted SaaS, >90% on multi-year prepaid sovereign contracts.

**Pricing anchor**: a single avoided 1% calibration error on a Rafale-class procurement (₹3.25 lakh crore lifetime) is ₹3,250 crore in value. A frontier-lab pre-release safety failure costs $10M+ in brand and regulatory standing. Annual contracts of $50K–$500K are rounding error against either anchor.

---

## Market

| Wedge | TAM (2026) | Year-3 capturable | Growth |
|---|---|---|---|
| AI-lab eval / red-teaming | $2.5–4.0 B | $5–15 M ARR | 40–60% / yr |
| Pre-trial litigation simulation | $0.8–1.5 B | $3–8 M ARR | 8–12% / yr |
| India public policy / civic-tech | ₹50–80 cr | ₹4–8 cr ARR | 15–20% / yr |
| **Composite** | **~$3.3–5.5 B** | **$8–25 M ARR** | — |

Sources: Scale AI public reporting (~$870M annual revenue, ~30% gov't/eval); jury-consulting industry estimates ($500M US market); Indian think-tank aggregate budget reports (PRS / IDSA annual statements); IndiaAI Mission allocation (₹10,371 crore 2024–29).

---

## Defensibility

What is a moat:

1. **The continuously-evolving curation methodology.** Persona-pool generation procedures that update faster than competitors can reverse-engineer the population from observed outputs. Latin-Hypercube-Sampled trait synthesis with orthogonality + diversity-volume gates (already implemented). 90-day refresh cycle vs 6-12 month competitor reverse-engineering cycle = 2–3 year defensible window per chamber.
2. **Customer-data feedback loops.** Every customer's eval informs persona pool refresh. Compounding asset; first 10 customers > next 100.
3. **Sociotechnical operationalisation.** The workflow embedding evaluators in customer-team rituals — what the field calls "evaluation as a power question". Not codable; consultative; institutional.
4. **Brand among researchers.** Quarterly *Moot Research Letter*, NeurIPS / FAccT publications, open-source engine + closed curation.

What is **not** a moat: the orchestration code (open, MIT); static persona seeds (replicable in 6–12 weeks); the 4-round debate format (public methodology); the underlying math (1990s political-science literature).

The architectural decision is **open-core** (LangChain / Weaviate playbook): orchestration code MIT, curation methodology + customer-data feedback + hosted infra closed.

---

## Roadmap

| Phase | Timeline | Milestones |
|---|---|---|
| **0 — Discovery** | Weeks 1–4 | 30 outbound × Wedge A, 30 × Wedge B; 10+10 calls; 3 LOIs at ≥$50K each |
| **1 — Build** | Months 2–6 | Dynamic persona generation; customer-feedback closed loop; multi-tenant SaaS; SOC 2 Type 1 prep; 1–3 paid pilots |
| **2 — Commercial scale** | Months 7–12 | 5–10 paid Wedge-A; 2–4 paid Wedge-B; ARR $1.5–3M; Series A window |
| **3 — Sovereign / on-prem** | Months 13–18 | Air-gapped Helm chart; DPDP Act compliance; ISO 27001; MeitY empanelment kickoff |
| **4 — Horizontal expansion** | Months 19–24 | 4th chamber (financial-compliance / healthcare-protocol); first non-India market |

Research credibility runs in parallel: NeurIPS / FAccT submission by month 12; peer-reviewed publication by month 18; quarterly research letter from month 6.

---

## Team & ask

**Founder** (operator-builder) — current. Building the engine, leading commercial discovery, raising this round.

**Engineer #2** — to hire post-LOI gate. ML + ops, ideally with frontier-lab eval experience.

**Research advisor** — engagement basis. Alignment / eval methodology.

**Legal-domain advisor** — engagement basis if Wedge B clears the gate.

### Ask

**$1.5M pre-seed**, 18-month runway, **15–18% dilution** at **$8–10M post-money cap**.

If both Wedges A and B clear the LOI gate, alternative: **$2.5M seed** at **$15M post-money** with 18% dilution and a 2-engineer hire.

### Use of funds

| Line | % |
|---|---|
| Engineering (founder + 2 hires) | 60 |
| Sales / customer-success | 15 |
| Infra (Yotta H100 reservation, Vertex committed-use, Anthropic credits) | 10 |
| Compliance (SOC 2 Type 1 + DPDP audit) | 10 |
| Reserves | 5 |

### Pre-seed gate

**Three signed LOIs at ≥$50K each across Wedges A + B by week 6.** No round without this. Founder operates on personal runway through the gate.

---

## Risks

| Risk | Mitigation |
|---|---|
| Frontier labs build internally, never buy | Curation craft + customer-data flywheel make buy-vs-build economics favour buy when our cycle outruns theirs. Testable in Phase 1. |
| EU AI Act commoditises pre-release red-teaming | Move up-market to post-deployment eval — different category, different buyer. |
| Scale AI bundles persona-pop eval into existing contracts | Differentiation on curation craft + cultural / linguistic diversity (Scale's persona populations are US-centric). |
| Customer-data feedback creates IP / privacy complications | Clear contractual terms from customer #1; specialised privacy counsel before first signed contract. |
| Long sales cycle exhausts runway | Wedge B (litigation) has clear ROI math and faster procurement than Wedge A; running both in parallel hedges sales-cycle risk. |
| Open-source the wrong layer | Architectural decision is locked: orchestration code open, curation + feedback + hosting closed (LangChain/Weaviate playbook). |

---

## Decision sought

A 30-minute conversation to walk through:

- Live demonstration of a Gemini-backed debate on a question of your choosing
- Per-chamber persona deep-dive (the 5-formative-books anchoring is the moat-relevant detail)
- The Phase-0 discovery plan and how we'd validate fit for your team / portfolio / market
- Terms

---

## Trying it

The product is running today. To request a demo or a 30-minute call:

→ **founder@moot.ai** *(placeholder)*
→ Live engine + UI: **http://localhost:8765/** (during demos)
→ Source: this repository (open-core, MIT)

---

*Moot · A Chamber of Synthetic Opinion*
