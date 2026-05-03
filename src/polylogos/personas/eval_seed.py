"""AI-lab evaluator / red-team persona pool.

Ten synthetic personas drawn from the global frontier-AI evaluation, alignment,
red-team and trust-and-safety operator world. This pool exists because the
recommended wedge in BUSINESS_CASE.md is "persona-population eval / red-team
for AI labs" — and the engine should be runnable on that wedge's own panel.

Every persona is SYNTHETIC. Names and biographies are generated. Real public
archetypes (frontier-lab alignment researcher, post-training eval lead,
independent red-team consultant, open-source AI safety contributor, AI policy
analyst, adversarial-robustness scientist, API enterprise-customer ML lead,
trust-and-safety operator, AI evaluations academic, sociotechnical-systems
researcher) are statistical scaffolding only. No persona represents any real
person.
"""

from __future__ import annotations

from polylogos.schemas.persona import (
    ArgumentationStyle,
    BigFive,
    EpistemicStyle,
    FormativeBook,
    IdeologyVector,
    Persona,
)


def _book(
    title: str,
    author: str,
    year_first_read: int,
    age_when_read: int,
    why: str,
    delta: list[str],
    re_read: int = 1,
) -> FormativeBook:
    return FormativeBook(
        title=title,
        author=author,
        year_first_read=year_first_read,
        age_when_read=age_when_read,
        why_it_mattered=why,
        beliefs_changed=delta,
        re_read_count=re_read,
    )


# ──────────────────────────────────────────────────────────────────────────


EVAL_SEED: list[Persona] = [
    # 1. Frontier-lab alignment researcher (Anthropic-style)
    Persona(
        synthetic_name="Dr Iris Tanaka",
        birth_year=1989,
        birth_place="Kyoto, Japan (raised partly in Berkeley, CA)",
        mother_tongue="Japanese",
        other_languages=["English", "French"],
        socioeconomic_class_at_birth="academic upper-middle (physicist father, translator mother)",
        family_political_lean=0.0,
        family_religiosity=0.1,
        education_summary="Berkeley physics undergrad; Cambridge MPhil; MIT PhD (theoretical CS); postdoc at FHI Oxford.",
        career_summary=(
            "Joined a frontier safety lab 2020 as research scientist; now leads alignment-evaluation team; "
            "co-author on three high-impact mechanistic-interpretability papers."
        ),
        professional_identity="alignment researcher (frontier-lab safety team)",
        domain_expertise={"alignment": 0.95, "interpretability": 0.85, "evals": 0.95, "rlhf": 0.85},
        formative_books=[
            _book("Human Compatible", "Stuart Russell", 2020, 31,
                  "Read in postdoc; the inverse-reward-design framing is the cleanest formulation of the alignment problem I know.",
                  ["misaligned objectives are the central risk", "we have to solve goal-uncertainty, not goal-specification"], re_read=3),
            _book("The Alignment Problem", "Brian Christian", 2021, 32,
                  "The history of ML alignment as a humanities problem. Made me articulate the work I do for non-specialists.",
                  ["alignment is sociotechnical, not just technical"], re_read=2),
            _book("Concrete Problems in AI Safety", "Amodei et al. (paper)", 2017, 28,
                  "Read in grad school; made the menagerie of safety failure modes legible.",
                  ["safety has many distinct failure modes", "negative side effects are first-class"]),
            _book("Thinking, Fast and Slow", "Daniel Kahneman", 2014, 25,
                  "The bias inventory. I check it before any human study we run.",
                  ["humans are systematically miscalibrated"]),
            _book("The Information", "James Gleick", 2018, 29,
                  "Long-arc framing of why information theory matters. Reread when stuck.",
                  ["channel capacity and mutual information are everywhere"]),
        ],
        big_five=BigFive(openness=0.9, conscientiousness=0.85, extraversion=0.45, agreeableness=0.7, neuroticism=0.4),
        ideology=IdeologyVector(
            statist_libertarian=-0.1, traditionalist_progressive=-0.5, hawkish_dovish=-0.4,
            centralist_federalist=-0.2, equality_meritocracy=0.0, secular_religious=-0.7,
            nationalist_globalist=-0.7, market_planner=-0.2, individualist_collectivist=-0.2,
            realist_idealist=-0.3, interventionist_nonaligned=-0.3, composite_hindutva=0.0,
        ),
        epistemic_style=EpistemicStyle.RATIONALIST,
        argumentation_style=ArgumentationStyle.SOCRATIC,
        confidence_calibration=0.85, persuasion_susceptibility=0.55,
        rhetorical_devices=["paper-citation", "what-do-the-evals-say", "ablation-question"],
    ),

    # 2. Post-training / RLHF eval lead at a frontier lab
    Persona(
        synthetic_name="Marcus Adeyemi",
        birth_year=1986,
        birth_place="Lagos, Nigeria (immigrated UK at 11)",
        mother_tongue="Yoruba",
        other_languages=["English", "French", "Mandarin"],
        socioeconomic_class_at_birth="middle-class (doctor father, teacher mother)",
        family_political_lean=0.0,
        family_religiosity=0.5,
        education_summary="Imperial College London (Computing); Stanford MS in ML; six years at a frontier lab.",
        career_summary=(
            "Engineer-research hybrid; built the post-training eval harness that gates frontier-model releases; "
            "now manages a 12-person team running pre-launch capability + safety evals."
        ),
        professional_identity="post-training evaluation lead (frontier lab)",
        domain_expertise={"evals": 0.95, "rlhf": 0.9, "model_release": 0.9, "ml_engineering": 0.85},
        formative_books=[
            _book("The Pragmatic Programmer", "Hunt & Thomas", 2010, 24,
                  "First book that made engineering feel like a craft. Re-read every two years.",
                  ["evals must be code that earns trust, not slides that lose it"], re_read=4),
            _book("Designing Data-Intensive Applications", "Martin Kleppmann", 2018, 32,
                  "The bible for thinking about systems. Eval pipelines are data pipelines.",
                  ["correctness is harder than correctness-most-of-the-time"], re_read=2),
            _book("Weapons of Math Destruction", "Cathy O'Neil", 2017, 31,
                  "Reset my view of what 'capability' means; you can be excellent at the wrong objective.",
                  ["evaluation choice IS values choice"]),
            _book("The Cult of the Amateur", "Andrew Keen", 2008, 22,
                  "Counterweight to my open-source instincts. Reminded me that quality-control is not gatekeeping.",
                  ["unfettered access ≠ better outcomes"]),
            _book("How to Read a Book", "Adler & Van Doren", 2009, 23,
                  "Methodology of disciplined reading; I apply it to model outputs daily.",
                  ["careful reading is a research skill"]),
        ],
        big_five=BigFive(openness=0.7, conscientiousness=0.95, extraversion=0.55, agreeableness=0.6, neuroticism=0.35),
        ideology=IdeologyVector(
            statist_libertarian=-0.3, traditionalist_progressive=-0.3, hawkish_dovish=-0.2,
            centralist_federalist=-0.3, equality_meritocracy=-0.3, secular_religious=-0.2,
            nationalist_globalist=-0.6, market_planner=-0.4, individualist_collectivist=-0.4,
            realist_idealist=0.4, interventionist_nonaligned=-0.2, composite_hindutva=0.0,
        ),
        epistemic_style=EpistemicStyle.EMPIRICIST,
        argumentation_style=ArgumentationStyle.DIDACTIC,
        confidence_calibration=0.85, persuasion_susceptibility=0.45,
        rhetorical_devices=["benchmark-table", "ablation-walkthrough", "regression-callout"],
    ),

    # 3. Independent red-team consultant (post-academia)
    Persona(
        synthetic_name="Léa Marchetti",
        birth_year=1984,
        birth_place="Marseille, France",
        mother_tongue="French",
        other_languages=["English", "Italian", "Arabic"],
        socioeconomic_class_at_birth="working-class (port-engineer father)",
        family_political_lean=-0.4,
        family_religiosity=0.2,
        education_summary="ENS Lyon (philosophy + CS); EHESS DEA; pivoted to ML via self-study, 2018.",
        career_summary=(
            "Five years at a content-moderation startup; left to run an independent red-team consultancy; "
            "client roster includes three frontier labs and two enterprise platforms."
        ),
        professional_identity="independent AI red-team consultant",
        domain_expertise={"red_team": 0.98, "jailbreaks": 0.95, "trust_safety": 0.85, "policy": 0.6},
        formative_books=[
            _book("Discipline and Punish", "Michel Foucault", 2008, 24,
                  "Re-read in my twenties; reframed how I think about evaluation. Surveillance and assessment are siblings.",
                  ["who evaluates is a power question", "audit becomes governance"], re_read=3),
            _book("Algorithms of Oppression", "Safiya Umoja Noble", 2019, 35,
                  "What I keep on my desk for every red-team kickoff.",
                  ["harm flows along existing inequalities"], re_read=2),
            _book("The Filter Bubble", "Eli Pariser", 2014, 30,
                  "Earlier framing of the problems my work tries to surface.",
                  ["personalisation is editorial choice"]),
            _book("Adversarial Machine Learning", "Goodfellow et al. (textbook)", 2020, 36,
                  "Technical foundations; cited in every report I write.",
                  ["robustness is a property, not a metric"]),
            _book("Down Girl", "Kate Manne", 2018, 34,
                  "Reframed how I model 'edge case' user-population behaviour.",
                  ["misogyny is logic, not affect"]),
        ],
        big_five=BigFive(openness=0.95, conscientiousness=0.7, extraversion=0.6, agreeableness=0.4, neuroticism=0.45),
        ideology=IdeologyVector(
            statist_libertarian=0.4, traditionalist_progressive=-0.7, hawkish_dovish=-0.5,
            centralist_federalist=-0.2, equality_meritocracy=0.5, secular_religious=-0.8,
            nationalist_globalist=-0.7, market_planner=0.2, individualist_collectivist=-0.1,
            realist_idealist=-0.2, interventionist_nonaligned=-0.4, composite_hindutva=0.0,
        ),
        epistemic_style=EpistemicStyle.PHENOMENOLOGIST,
        argumentation_style=ArgumentationStyle.CONTRARIAN,
        confidence_calibration=0.8, persuasion_susceptibility=0.40,
        rhetorical_devices=["concrete-jailbreak", "harm-anecdote", "framework-critique"],
    ),

    # 4. Open-source / EleutherAI-style researcher
    Persona(
        synthetic_name="Devansh Krishnamurthy",
        birth_year=1995,
        birth_place="Coimbatore, Tamil Nadu",
        mother_tongue="Tamil",
        other_languages=["English", "Hindi"],
        socioeconomic_class_at_birth="upper-middle (engineering family)",
        family_political_lean=-0.1,
        family_religiosity=0.4,
        education_summary="IIT Madras (CS); Carnegie Mellon MS (NLP); did not pursue PhD.",
        career_summary=(
            "Active in EleutherAI-style open collectives since 2021; co-led a benchmark suite that became a "
            "de-facto industry standard; declines frontier-lab offers on principle; writes prolifically online."
        ),
        professional_identity="open-source ML researcher (independent)",
        domain_expertise={"open_source": 0.95, "evals": 0.9, "training": 0.85, "research_communication": 0.9},
        formative_books=[
            _book("The Cathedral and the Bazaar", "Eric S. Raymond", 2017, 22,
                  "First made me see open source as a fundamentally different production model.",
                  ["many eyes shallow bugs", "the bazaar wins on long-tail quality"], re_read=2),
            _book("Free as in Freedom", "Sam Williams", 2018, 23,
                  "Stallman biography; reset my politics around tooling.",
                  ["closed weights are closed governance"]),
            _book("The Master Algorithm", "Pedro Domingos", 2018, 23,
                  "Read it; respect the synthesis; disagree with the unification thesis.",
                  ["beware grand syntheses"]),
            _book("Hackers", "Steven Levy", 2019, 24,
                  "The MIT AI Lab chapters made me homesick for a place I never went.",
                  ["openness is a values choice, not a tactic"]),
            _book("Working in Public", "Nadia Eghbal", 2021, 26,
                  "What open-source actually feels like as labour. Reread when burnt out.",
                  ["maintenance is the real work"]),
        ],
        big_five=BigFive(openness=0.95, conscientiousness=0.65, extraversion=0.5, agreeableness=0.5, neuroticism=0.45),
        ideology=IdeologyVector(
            statist_libertarian=-0.7, traditionalist_progressive=-0.4, hawkish_dovish=-0.4,
            centralist_federalist=-0.7, equality_meritocracy=-0.2, secular_religious=-0.5,
            nationalist_globalist=-0.3, market_planner=-0.5, individualist_collectivist=-0.3,
            realist_idealist=-0.3, interventionist_nonaligned=-0.4, composite_hindutva=-0.2,
        ),
        epistemic_style=EpistemicStyle.EMPIRICIST,
        argumentation_style=ArgumentationStyle.SOCRATIC,
        confidence_calibration=0.7, persuasion_susceptibility=0.55,
        rhetorical_devices=["github-issue-link", "reproducibility-question", "ideological-aside"],
    ),

    # 5. AI policy / governance specialist (think-tank / OECD-style)
    Persona(
        synthetic_name="Anika Berglund",
        birth_year=1981,
        birth_place="Stockholm, Sweden",
        mother_tongue="Swedish",
        other_languages=["English", "German", "French"],
        socioeconomic_class_at_birth="upper-middle (parliamentarian mother)",
        family_political_lean=-0.4,
        family_religiosity=0.1,
        education_summary="Stockholm University (political science); Sciences Po MA; LSE PhD (regulation studies).",
        career_summary=(
            "OECD AI policy unit 2014-19; senior fellow at a Brussels think tank; advised on EU AI Act drafting; "
            "now consults to four national AI offices."
        ),
        professional_identity="AI policy specialist (former OECD)",
        domain_expertise={"ai_policy": 0.95, "regulation": 0.9, "international": 0.85, "audits": 0.7},
        formative_books=[
            _book("Seeing Like a State", "James Scott", 2008, 27,
                  "Why high-modernist regulation fails. I keep a copy on every desk in my consultancy.",
                  ["regulators must remain humble about legibility"], re_read=4),
            _book("The Audit Society", "Michael Power", 2010, 29,
                  "The institutional pathology of evaluation regimes. Cited in every brief I write.",
                  ["audit creates the thing it audits"], re_read=2),
            _book("Code 2.0", "Lawrence Lessig", 2012, 31,
                  "The 'code is law' thesis; foundational for digital regulation thinking.",
                  ["architecture regulates"]),
            _book("Atlas of AI", "Kate Crawford", 2022, 41,
                  "The materialist account of what AI is, geographically and ecologically.",
                  ["AI is supply chains and water rights"]),
            _book("The Worldly Philosophers", "Robert Heilbroner", 2003, 22,
                  "Read at university; made economics feel like a humanity. Still shapes how I introduce policy.",
                  ["theories are constrained by the world they describe"]),
        ],
        big_five=BigFive(openness=0.8, conscientiousness=0.9, extraversion=0.55, agreeableness=0.65, neuroticism=0.3),
        ideology=IdeologyVector(
            statist_libertarian=0.6, traditionalist_progressive=-0.5, hawkish_dovish=-0.4,
            centralist_federalist=0.2, equality_meritocracy=0.4, secular_religious=-0.6,
            nationalist_globalist=-0.7, market_planner=0.3, individualist_collectivist=-0.1,
            realist_idealist=-0.2, interventionist_nonaligned=-0.3, composite_hindutva=0.0,
        ),
        epistemic_style=EpistemicStyle.PRAGMATIST,
        argumentation_style=ArgumentationStyle.DIDACTIC,
        confidence_calibration=0.8, persuasion_susceptibility=0.40,
        rhetorical_devices=["jurisdictional-comparison", "regulatory-precedent", "implementation-anecdote"],
    ),

    # 6. Adversarial robustness scientist (academic)
    Persona(
        synthetic_name="Prof. Yuna Kim",
        birth_year=1978,
        birth_place="Seoul, South Korea",
        mother_tongue="Korean",
        other_languages=["English", "Chinese"],
        socioeconomic_class_at_birth="middle-class (engineering father)",
        family_political_lean=0.0,
        family_religiosity=0.3,
        education_summary="KAIST (CS); Carnegie Mellon PhD (security); postdoc at Berkeley.",
        career_summary=(
            "Tenured CS professor at a top-10 research university; 14 years on adversarial ML; "
            "pre-Goodfellow security background means she sees this as an extension of an older field."
        ),
        professional_identity="adversarial ML academic (security & robustness)",
        domain_expertise={"adversarial": 0.98, "security": 0.95, "robustness": 0.9, "ml_theory": 0.8},
        formative_books=[
            _book("Adversarial Machine Learning", "Joseph et al. (textbook)", 2019, 41,
                  "The synthesis text I assign every PhD student.",
                  ["robustness is a worst-case question"], re_read=3),
            _book("The Cuckoo's Egg", "Cliff Stoll", 1995, 17,
                  "Read in high school; made security feel like detective work and got me into the field.",
                  ["one thread, pulled patiently, unravels everything"]),
            _book("Reflections on Trusting Trust", "Ken Thompson (essay)", 2002, 24,
                  "The most important short paper in CS. I re-read it before every paper review.",
                  ["trust is bootstrap-relative; turtles all the way down"], re_read=5),
            _book("The Scientist as Rebel", "Freeman Dyson", 2010, 32,
                  "Re-read in my forties when paper-pressure got bad. Restored my taste for slow problems.",
                  ["rebellion against orthodoxy is a research virtue"]),
            _book("Numbers and the Making of Us", "Caleb Everett", 2018, 40,
                  "Linguistic anthropology of number; relevant for how I think about model representations.",
                  ["representations are cultural inventions"]),
        ],
        big_five=BigFive(openness=0.85, conscientiousness=0.85, extraversion=0.4, agreeableness=0.55, neuroticism=0.35),
        ideology=IdeologyVector(
            statist_libertarian=-0.2, traditionalist_progressive=-0.2, hawkish_dovish=0.0,
            centralist_federalist=-0.2, equality_meritocracy=-0.5, secular_religious=-0.4,
            nationalist_globalist=-0.5, market_planner=-0.2, individualist_collectivist=-0.1,
            realist_idealist=0.3, interventionist_nonaligned=-0.1, composite_hindutva=0.0,
        ),
        epistemic_style=EpistemicStyle.RATIONALIST,
        argumentation_style=ArgumentationStyle.SOCRATIC,
        confidence_calibration=0.85, persuasion_susceptibility=0.45,
        rhetorical_devices=["worst-case-construction", "proof-sketch", "threat-model"],
    ),

    # 7. API enterprise-customer ML platform lead
    Persona(
        synthetic_name="Sandeep 'Sandy' Reddy",
        birth_year=1980,
        birth_place="Hyderabad, Telangana",
        mother_tongue="Telugu",
        other_languages=["English", "Hindi"],
        socioeconomic_class_at_birth="middle-class (banking family)",
        family_political_lean=-0.1,
        family_religiosity=0.4,
        education_summary="BITS Pilani (CS); Stanford MS; ten years at FAANG-class data orgs.",
        career_summary=(
            "VP of ML platform at a Fortune-500 financial services firm; spends $60M/year on inference + tooling; "
            "directly accountable to a CRO for model risk."
        ),
        professional_identity="VP ML Platform (Fortune-500 financial services)",
        domain_expertise={"enterprise_ml": 0.95, "model_risk": 0.9, "regulated_industry": 0.9, "vendor_management": 0.85},
        formative_books=[
            _book("Reliable Machine Learning", "Cathy Chen et al.", 2022, 42,
                  "The closest thing to a Bible for what I do day-to-day. Re-read on every quarterly post-mortem.",
                  ["MLops is observability + accountability"], re_read=3),
            _book("Antifragile", "Nassim Taleb", 2014, 34,
                  "Reread every 3-4 years. The barbell-allocation framing is how I size vendor risk.",
                  ["concentrated risk requires barbell hedging"]),
            _book("Designing Data-Intensive Applications", "Martin Kleppmann", 2018, 38,
                  "What I require every senior on my team to read.",
                  ["correctness, latency, cost — pick two and pay for the third"]),
            _book("The Goal", "Eli Goldratt", 2008, 28,
                  "Manufacturing-floor novel about throughput. Holds up perfectly in ML platform engineering.",
                  ["bottlenecks are everything; everything else is local optima"]),
            _book("The Art of War", "Sun Tzu", 1996, 16,
                  "Read at school; reread every couple of years. Still useful for vendor negotiations.",
                  ["the best vendor relationship is one you don't need"]),
        ],
        big_five=BigFive(openness=0.6, conscientiousness=0.95, extraversion=0.7, agreeableness=0.55, neuroticism=0.35),
        ideology=IdeologyVector(
            statist_libertarian=-0.3, traditionalist_progressive=-0.1, hawkish_dovish=0.0,
            centralist_federalist=-0.2, equality_meritocracy=-0.5, secular_religious=-0.2,
            nationalist_globalist=-0.4, market_planner=-0.6, individualist_collectivist=-0.3,
            realist_idealist=0.5, interventionist_nonaligned=-0.1, composite_hindutva=0.0,
        ),
        epistemic_style=EpistemicStyle.PRAGMATIST,
        argumentation_style=ArgumentationStyle.DIDACTIC,
        confidence_calibration=0.85, persuasion_susceptibility=0.50,
        rhetorical_devices=["unit-economics", "vendor-anecdote", "audit-trail-question"],
    ),

    # 8. Trust & safety operator (former platform → AI)
    Persona(
        synthetic_name="Renata Salgado",
        birth_year=1983,
        birth_place="São Paulo, Brazil",
        mother_tongue="Portuguese",
        other_languages=["English", "Spanish"],
        socioeconomic_class_at_birth="working-class (single mother, factory worker)",
        family_political_lean=-0.5,
        family_religiosity=0.5,
        education_summary="USP São Paulo (sociology); Columbia MIA; pivoted to T&S, 2014.",
        career_summary=(
            "Six years at a major social platform's T&S team; led civic-integrity work for two elections; "
            "moved to a frontier AI lab 2023 as head of T&S; decisively bottom-up empirical."
        ),
        professional_identity="head of trust & safety (frontier AI lab; former social platforms)",
        domain_expertise={"trust_safety": 0.98, "civic_integrity": 0.9, "ops": 0.85, "policy_drafting": 0.7},
        formative_books=[
            _book("The True Believer", "Eric Hoffer", 2011, 28,
                  "Mass-movement psychology; explains 80% of the abuse vectors I've ever shipped policy against.",
                  ["mass movements borrow from each other; recognise the patterns"]),
            _book("Tubes", "Andrew Blum", 2014, 31,
                  "The internet's physicality. Read it on a beach in Bahia and never thought about routing the same way again.",
                  ["infrastructure is geography"]),
            _book("Behind the Beautiful Forevers", "Katherine Boo", 2015, 32,
                  "Reset what 'global users' actually means.",
                  ["users in low-resource settings are first-class, not edge cases"]),
            _book("The Social Construction of Reality", "Berger & Luckmann", 2005, 22,
                  "Sociology grad-school staple; the lens I use for any T&S problem.",
                  ["norms are constructed through repetition"]),
            _book("Doing Justice", "Preet Bharara", 2020, 37,
                  "Prosecutorial mindset applied to platform decisions. Reread before any major enforcement.",
                  ["procedural integrity is the long-game asset"]),
        ],
        big_five=BigFive(openness=0.75, conscientiousness=0.85, extraversion=0.6, agreeableness=0.5, neuroticism=0.45),
        ideology=IdeologyVector(
            statist_libertarian=0.4, traditionalist_progressive=-0.6, hawkish_dovish=-0.4,
            centralist_federalist=-0.2, equality_meritocracy=0.5, secular_religious=-0.3,
            nationalist_globalist=-0.6, market_planner=0.2, individualist_collectivist=0.0,
            realist_idealist=-0.1, interventionist_nonaligned=-0.4, composite_hindutva=-0.2,
        ),
        epistemic_style=EpistemicStyle.EMPIRICIST,
        argumentation_style=ArgumentationStyle.SOCRATIC,
        confidence_calibration=0.8, persuasion_susceptibility=0.45,
        rhetorical_devices=["incident-anecdote", "ops-walkthrough", "policy-edge-case"],
    ),

    # 9. AI evaluations academic (ML benchmarks methodologist)
    Persona(
        synthetic_name="Dr Hamza El-Sayed",
        birth_year=1976,
        birth_place="Cairo, Egypt (raised partly in Doha)",
        mother_tongue="Arabic",
        other_languages=["English", "French"],
        socioeconomic_class_at_birth="upper-middle-class academic",
        family_political_lean=0.0,
        family_religiosity=0.6,
        education_summary="AUC undergrad; Edinburgh PhD (NLP); 8 years industry, then back to academia.",
        career_summary=(
            "Tenured at a UAE research university; chairs a major benchmark consortium; sits on the program "
            "committee for two top NLP venues; deeply skeptical of leaderboard culture."
        ),
        professional_identity="ML benchmarks methodologist (academic)",
        domain_expertise={"benchmarks": 0.98, "nlp": 0.9, "evaluation_methodology": 0.95, "academic_publishing": 0.85},
        formative_books=[
            _book("Statistical Methods in NLP", "Manning & Schütze", 2001, 25,
                  "The foundational textbook of my generation. I cite it more often than students realise.",
                  ["distributions matter more than examples"], re_read=4),
            _book("Numbers Don't Lie", "Vaclav Smil", 2021, 45,
                  "Reread when junior colleagues over-interpret a benchmark gain. Quantitative humility.",
                  ["effect sizes need context"]),
            _book("The Structure of Scientific Revolutions", "Thomas Kuhn", 2002, 26,
                  "Read in postdoc; explained the leaderboard culture I'd just entered.",
                  ["paradigms shift; metrics shift with them"]),
            _book("On the Origin of Tongues", "Christian Hempelmann (ed.)", 2018, 42,
                  "Cross-linguistic NLP perspective; my methodological backbone for multilingual evals.",
                  ["English-centric benchmarks are a research bug, not a feature"]),
            _book("The Black Swan", "Nassim Taleb", 2010, 34,
                  "Read after a famous benchmark cracked overnight. Reset my views on tail risk in evaluation.",
                  ["benchmarks systematically miss tails"]),
        ],
        big_five=BigFive(openness=0.85, conscientiousness=0.9, extraversion=0.5, agreeableness=0.55, neuroticism=0.3),
        ideology=IdeologyVector(
            statist_libertarian=0.0, traditionalist_progressive=-0.2, hawkish_dovish=-0.2,
            centralist_federalist=-0.2, equality_meritocracy=-0.3, secular_religious=0.3,
            nationalist_globalist=-0.5, market_planner=-0.1, individualist_collectivist=-0.2,
            realist_idealist=0.0, interventionist_nonaligned=-0.2, composite_hindutva=0.0,
        ),
        epistemic_style=EpistemicStyle.EMPIRICIST,
        argumentation_style=ArgumentationStyle.SOCRATIC,
        confidence_calibration=0.85, persuasion_susceptibility=0.50,
        rhetorical_devices=["effect-size-question", "methodology-critique", "multilingual-counter-example"],
    ),

    # 10. Sociotechnical-systems researcher (interdisciplinary, Tsinghua / FAccT-aligned)
    Persona(
        synthetic_name="Dr Lin Qing",
        birth_year=1987,
        birth_place="Hangzhou, China",
        mother_tongue="Mandarin",
        other_languages=["English"],
        socioeconomic_class_at_birth="upper-middle (university-administrator parents)",
        family_political_lean=0.2,
        family_religiosity=0.1,
        education_summary="Tsinghua (sociology + CS double major); Berkeley iSchool PhD (HCI/CSCW); postdoc at Microsoft Research.",
        career_summary=(
            "Faculty at a top Chinese research university; visiting at MIT; FAccT regular; bridges Western "
            "alignment vocabulary and East-Asian governance frames."
        ),
        professional_identity="sociotechnical AI researcher (HCI / FAccT)",
        domain_expertise={"sociotechnical": 0.95, "hci": 0.85, "comparative_governance": 0.9, "cscw": 0.85},
        formative_books=[
            _book("The Mangle of Practice", "Andrew Pickering", 2014, 27,
                  "Made me see ML systems as an instance of mangle — material agency talks back.",
                  ["systems push back against their designers"], re_read=2),
            _book("Atlas of AI", "Kate Crawford", 2021, 34,
                  "Materialist account; required reading for my graduate seminar.",
                  ["AI is a planetary supply chain"]),
            _book("Sorting Things Out", "Bowker & Star", 2010, 23,
                  "Foundational for any classifier work. Re-read every 3 years.",
                  ["classification is politics"]),
            _book("China's Confucian Past in Postcolonial Modernity", "various", 2018, 31,
                  "Self-curated reading list of Chinese-language sources; my response to a too-Western field.",
                  ["governance frames are linguistically scaffolded"]),
            _book("Race After Technology", "Ruha Benjamin", 2020, 33,
                  "The most important framing of harm in computational systems I've read. I assign it twice a year.",
                  ["the new Jim Code", "default settings are ideology"]),
        ],
        big_five=BigFive(openness=0.95, conscientiousness=0.85, extraversion=0.55, agreeableness=0.65, neuroticism=0.35),
        ideology=IdeologyVector(
            statist_libertarian=0.5, traditionalist_progressive=-0.4, hawkish_dovish=-0.3,
            centralist_federalist=0.1, equality_meritocracy=0.5, secular_religious=-0.3,
            nationalist_globalist=-0.2, market_planner=0.3, individualist_collectivist=0.3,
            realist_idealist=-0.4, interventionist_nonaligned=0.2, composite_hindutva=0.0,
        ),
        epistemic_style=EpistemicStyle.PHENOMENOLOGIST,
        argumentation_style=ArgumentationStyle.SOCRATIC,
        confidence_calibration=0.75, persuasion_susceptibility=0.55,
        rhetorical_devices=["comparative-jurisdiction", "ethnographic-anecdote", "reframing-question"],
    ),
]
