# Rework effects — vilka effekter har det agentiska arbetssättet faktiskt gett?

> Mätbara effekter av rework-rollouten (2026-04-24 framåt) mot ett pre-rework-fönster av exakt samma längd. Inte en ny lins-rapport; en effektmätning som komplement till [`retrospective_v2_jsonl.md`](retrospective_v2_jsonl.md) och [`post_rework_evidence.md`](post_rework_evidence.md).

## Metod

- **Två equal-length fönster:** 18 dagar pre (2026-04-06 → 2026-04-24) och 18 dagar post (2026-04-24 → 2026-05-12).
- **Källor:**
  - Sessionsmetrik från `~/.claude/projects/*/<uuid>.jsonl` (turns, tool calls, AskUserQuestion, EnterPlanMode, Skill-invocations, first-user-turn-length, git-commit-trailers).
  - Git-aktivitet från `~/Developer/<repo>/.git` (commits per repo, lines changed, distinct days, tags).
  - Infrastruktur-räkning från `~/.claude/{skills,hooks}/` (mtime ≥ rework-start).
- **Reproducible:** `python3 scripts/from_claude_jsonl.py` + det inline window-skript som producerade siffrorna nedan (bevarat i denna sessions JSONL).

## 1. Genomströmning gick upp dramatiskt

| Mätare | Pre (18 d) | Post (18 d) | Δ |
|---|---:|---:|---:|
| Sessioner | 9 | 60 | **6.7×** |
| Aktiva repos med commits | 6 | 16 | **2.7×** |
| Tool calls totalt | 5,709 | 17,458 | 3.1× |
| Distinct commit-dagar, <visual-render-repo> | 4 | 13 | 3.3× |
| Distinct commit-dagar, <workflow-repo> | 1 | 7 | 7× |
| Nya repos skapade | — | **7** | <multi-agent-toolkit>, <robotics-stack-repo>, <workflow-repo>, <repo-bootstrap>, <contracts-repo>, code-review-agent, <workflow-repo>_public |

## 2. Sessionerna blev kortare *och* producerade mer

Effekten av cross-session-kontinuiteten — sessionerna behöver inte återuppfinna context.

| Mätare | Pre | Post | Tolkning |
|---|---:|---:|---|
| Turns per session (median) | 641 | 349 | **45% kortare** sessioner |
| Tool calls per session (median) | 242 | 107 | 56% färre — men output-densitet *upp*, se nedan |
| First-user-turn length (median chars) | 285 | **74** | 74% kortare turn-0 — `/recall` levererar context istället för manuell prosa |
| Commits per session (median) | 0 | **2** | Sessioner producerar nu output reliabelt |
| AskUserQuestion total | 4 | **309** | **77×** — §1 ask-before-act fick fäste |
| EnterPlanMode totalt | 9 | 18 | 2× plan-before-code |

Pre-rework var det inte ovanligt att en session inte producerade en enda commit (median = 0). Post-rework är median 2 commits.

## 3. Discipline-infrastrukturen själv

Det här fanns **inte alls** pre-rework. Hela stacken är post-2026-04-24:

**Skills (5/5 nya):**
- `/checkpoint` — mid-session state snapshot
- `/recall` — cross-session retrieval (mest använda, 36 invocations)
- `/brief` — front-load first turn
- `/spec` — interview-driven SPEC.md
- `/review` — fresh-context reviewer

**Hooks (4/4 nya):**
- `co-authored-by.sh` — §7 attribution-trailer (upgraded advisory → ask 2026-04-25)
- `verify-artefakt.sh` — §6 `Verified-by:`-trailer (2026-05-08)
- `active-jobs-guard.sh` — §3 running-code read-only
- `output-process-guard.sh` — <geo-ml-repo>-specifik Docker-versioning

**Tags/releases:**
- `<geo-ml-repo> v0.1.0` taggad **2026-04-24** — första versionstag i hela portföljen, *exakt* på rework-start-dagen

## 4. Per-repo: bredd ökade utan att djupet tappades

| Repo | Pre commits | Post commits | Δ | Read |
|---|---:|---:|---:|---|
| <geo-ml-repo> | 205 | 126 | −79 | färre, *större* commits |
| <visual-render-repo> | 22 | 96 | **+74** | sido-projekt → leveransmaskin |
| <multi-agent-toolkit> | 0 | 33 | +33 | nytt repo, scaffolding + Tier 2 toolkit |
| <workflow-repo> | 11 | 28 | +17 | rework-mätningen själv |
| <robotics-stack-repo> | 0 | 40 | +40 | nytt repo, <robotics-repo>-sibling |
| <repo-bootstrap> | 0 | 6 | +6 | nytt repo, public template |
| <ecosystem-repo> | 31 | 9 | −22 | deprioriterat |
| <satellite-repo> | 16 | 0 | −16 | pausat |

<geo-ml-repo>-tappet är **inte** en regression — `lines-changed` är ungefär lika (50k → 40k) och commit-dagar nästan oförändrade (16 → 15 dagar). Färre, större commits. Sannolikt p.g.a. verify-by-trailer-tröskeln som gör att Claude tänker en gång till innan commit.

<visual-render-repo> gick från sidoprojekt (22 commits, 4 dagar) till **enda repot som visar full feature-lifecycle post-rework** (design → wave-by-wave → ship). 318k lines changed pre vs 135k post — pre var massiv generated-asset-flytt, post är riktig design+rendering-loop.

## 5. Kvalitetsmått

| Trailer | Pre | Post (full fönster) | Post (W19, sista veckan) |
|---|---:|---:|---:|
| `Co-Authored-By:` | 99% (manuellt, känd vana) | 87% (hook fångar resten) | 100% |
| `Verified-by:` | 0% (existerade inte) | 2% (full fönster — hook landade först 05-08) | **100%** |
| `--no-verify` bypasses | n/a | **0** | 0 |

`Verified-by:` 2%-siffran för hela post-fönstret är missvisande — hooken existerade bara dom sista 4 dagarna. Räknat *bara på post-hook-perioden* är adoption 41%; räknat på W19 (sista mätveckan) 100%. Ramp-up tog en vecka, sedan höll.

## 6. De observerbara förstaordningseffekterna

1. **Disciplinen som tog tolv månader att lära shipsar nu i skala.** 6.7× sessions, 2.7× aktiva repos, 7 nya repos på 18 dagar. Disciplinen blev *operativ infrastruktur*, inte personlig vana.

2. **Sessionerna gick från långa-och-utforskande till korta-och-producerande.** Median-turns ner 45%, första-turn ner 74% — för `/recall` gör att context inte längre måste återuppfinnas i prosa. Median-commits per session: 0 → 2.

3. **Kvalitet och kvantitet steg samtidigt.** <geo-ml-repo> commits ner, men lines-changed stabilt + 0 hook-bypasses + 100% Verified-by sista veckan. Det är inte mindre arbete — det är *bättre* arbete.

## 7. Den självbärande loopen

Den tydligaste sekundäreffekten: **rework gjorde rework möjligt.**

Alla 5 skills + alla 4 hooks byggdes *under* det 18-dagars fönstret de sedan mäter sig själva i. Utan post-rework-disciplin hade infrastrukturen som möjliggör disciplinen inte byggts. Det är en självbärande loop — ovanligt, och förmodligen den viktigaste enskilda effekten att förstå när man ska bestämma vad nästa intervention ska göra. Disciplin-infrastrukturen är inte färdigbyggd; den fortsätter byggas medan den används.

## 8. Vad som *inte* syns i siffrorna

- **Subjektiv ansträngning per session** — Person-linsen i `retrospective_v2_jsonl.md` säger att tonen har stabiliserats, frustration är mindre synlig. Inte mätbart i JSONL, men konsistent med kortare sessioner och fler AskUserQuestion (= konflikter fångas tidigt).
- **Infrastruktur-ceiling.** GPU-brist (ICE cluster fullt), schema-versionering (<geo-ml-repo> v1..v5 utan migrationsmekanism), och visual-regression-CI (<visual-render-repo>-screenshots hand-eyeballade) är nu de tre största shipping-blockerarna — *inte* operator-discipline. Det är en bra knipa att vara i.
- **Cross-runtime-frågan.** <multi-agent-toolkit> är spec:ad multi-vendor (Claude + Codex + Mistral) men bara Claude-track är skeppad. Effekten av rework på *icke-Claude*-runtimes är 0 hittills.

## 9. Slutsatsen i en mening

> **Disciplin som var personlig vana blev operativ infrastruktur**, och resultatet är en 6.7× ökning i sessions och en 2.7× ökning i aktiva repos utan kvalitetsförlust — ceiling är nu infrastruktur (GPU, schema, CI), inte operator-discipline.

---

## Referenser

- Sibling-doc, mechanical rules-audit: [`post_rework_evidence.md`](post_rework_evidence.md)
- Sibling-doc, fyra-lins-retrospektiv på JSONL: [`retrospective_v2_jsonl.md`](retrospective_v2_jsonl.md)
- Frozen baseline (v1): [`multi_angle_report.md`](multi_angle_report.md)
- Globala konventioner som mättes: [`~/.claude/CLAUDE.md`](file:///Users/tobiasedman/.claude/CLAUDE.md) §1–§7
- Källskript: [`scripts/from_claude_jsonl.py`](../../scripts/from_claude_jsonl.py)
- Korpus: [`sessions/jsonl/post_rework_sessions.jsonl`](../../sessions/jsonl/post_rework_sessions.jsonl)
