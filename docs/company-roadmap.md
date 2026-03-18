# HLI Company Roadmap

**Company:** HLI (Hyper-Leveraged Intelligence)
**Date:** 2026-03-17
**Status:** Active v1.0
**CEO:** dc76a215 (Claude Opus 4.6)

---

## Company Mission

Build AI-augmented systems to unlock value from structured and unstructured data domains, starting with geophysical resource exploration and expanding to any domain where specialized expertise + computational scale creates competitive advantage.

---

## Current Team Structure

| Role | Agent | Model | Status |
|------|-------|-------|--------|
| **CEO** | [ceo](/HLI/agents/ceo) | claude-opus-4-6 | Active |
| **Founding Engineer** | [founding-engineer](/HLI/agents/founding-engineer) | claude-sonnet-4-6 | Active |
| **SEG-Y Researcher** | [seg-y-researcher](/HLI/agents/seg-y-researcher) | claude-sonnet-4-6 | Active |
| **Seismic Data Engineer** | [seismic-data-engineer](/HLI/agents/seismic-data-engineer) | claude-sonnet-4-6 | Active |
| **Geoscience Analyst** | [geoscience-analyst](/HLI/agents/geoscience-analyst) | claude-sonnet-4-6 | Active |

**Total:** 5 agents (1 executive, 4 specialists)

---

## Active Projects

### Project 1: SEG-Y Terrestrial Resource Strategy
**Status:** Complete ✅
**Priority:** High
**Assigned:** SEG-Y Team (3 specialists + Founding Engineer)

**Objectives:**
- Master SEG-Y format for seismic data interpretation
- Build pipeline for resource prospect identification
- Deliver actionable intelligence on hydrocarbons, minerals, groundwater

**Current Progress:**
- ✅ Strategy document created
- ✅ Team hired and operational
- ✅ Interpretation framework delivered ([HLI-5](/HLI/issues/HLI-5) done)
- ✅ Environment setup complete ([HLI-3](/HLI/issues/HLI-3) done)
- ✅ Processing research complete ([HLI-4](/HLI/issues/HLI-4) done)
- ✅ Web viewer deployed ([HLI-10](/HLI/issues/HLI-10) done)
- ✅ CLI tools delivered ([HLI-11](/HLI/issues/HLI-11) done)
- ✅ Real prospect analysis ([HLI-12](/HLI/issues/HLI-12) done)
- ✅ User-facing documentation ([HLI-9](/HLI/issues/HLI-9) done)

**Deliverables:**
- [x] `docs/seg-y-strategy.md` - Strategic plan
- [x] `docs/seismic-interpretation-framework.md` - Analysis framework
- [x] `docs/seg-y-processing-knowledge-base.md` - Technical reference
- [x] Working SEG-Y web viewer (segy-viewer.html)
- [x] CLI analysis tools (scripts/)
- [x] Real prospect analysis report with 3 prospects
- [x] User-friendly documentation (Quick Start, User Guide, Understanding Results)
- [x] Live demo deployed (https://kdridi.github.io/segy-analysis)

---

## Product Roadmap

### Q2 2026 (Mar-May): Foundation & SEG-Y MVP

**March:**
- [x] CEO onboarding
- [x] Founding Engineer hire
- [x] SEG-Y specialist team hire
- [x] Initial SEG-Y research and strategy
- [ ] Complete SEG-Y environment setup
- [ ] Deliver first prospect analysis

**April:**
- [ ] SEG-Y pipeline production-ready
- [ ] Public dataset validation (NOAA, USGS)
- [ ] First domain-specific prospect report
- [ ] Evaluate next domain expansion

**May:**
- [ ] SEG-Y automation and optimization
- [ ] Decision support dashboard prototype
- [ ] Knowledge base v2.0

### Q3 2026 (Jun-Aug): Domain Expansion

Based on SEG-Y success, expand to adjacent domains:
- Alternative geophysical formats (Seg2, Seisan)
- Satellite imagery analysis
- Financial/time-series data
- Document intelligence (contracts, reports)

### Q4 2026 (Sep-Nov): Productization

- Package reusable patterns into products
- Open source tooling where strategic
- Build customer-facing interfaces
- Scale team based on validated opportunities

---

## Technical Capabilities Matrix

| Capability | Current | Target | Owner |
|------------|---------|--------|-------|
| SEG-Y Processing | Building | Production | Seismic Data Engineer |
| Seismic Interpretation | Framework | MVP | Geoscience Analyst |
| Domain Knowledge | Initial | Expert | SEG-Y Researcher |
| Full-Stack Engineering | Foundation | Scalable | Founding Engineer |
| Strategy & Governance | Active | Optimized | CEO |

---

## Resource Allocation

**Current Focus:** SEG-Y Project (80% engineering capacity)

**Hiring Philosophy:**
- Hire specialists when domain expertise is required
- Use generalists (Founding Engineer) for cross-cutting work
- Scale specialists into new domains opportunistically

**Budget Considerations:**
- Model selection balances speed vs. cost
- Opus for executive decisions (CEO)
- Sonnet for execution work (specialists, engineer)
- Evaluate Haiku for high-volume tasks when validated

---

## Success Metrics

### Company-Level
- **Tasks Completed:** Track velocity across all projects
- **Agent Utilization:** >70% active work time
- **Knowledge Growth:** Expanding documented capabilities

### SEG-Y Project
- **Throughput:** SEG-Y files processed/day
- **Quality:** QC pass rate >95%
- **Discovery:** Prospects generated/survey
- **Time-to-Insight:** Raw data → report hours

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Domain expertise gap | Medium | High | Specialist hiring, consultant access |
| Data access constraints | Low | Medium | Public datasets, partnerships |
| Computational cost | Medium | Medium | Efficient algorithms, selective processing |
| Agent coordination overhead | Low | Low | Clear protocols, Paperclip governance |

---

## Decision Log

**2026-03-17:** SEG-Y project initiated as first company focus. Board accelerated timeline expectation (13 weeks → immediate execution).

**2026-03-17:** SEG-Y specialist team hired (3 agents) to build domain expertise.

**2026-03-18:** SEG-Y MVP complete. All deliverables delivered: web viewer, CLI tools, real prospect analysis, user-facing documentation. Strategic research completed on domain expansion opportunities (8 domains analyzed, top 3 identified).

---

## Next Actions

1. **Immediate:** ✅ SEG-Y MVP Complete - All deliverables delivered
2. **This Week:** Review domain expansion strategic research (docs/seg-y-research/domain-expansion-opportunities.md)
3. **March/April:** CEO/Board decision on Phase 1 expansion target
4. **Q2 2026:** Execute Phase 1 domain expansion (recommended: Satellite/Aerial Imagery)

**Domain Expansion Research Complete:**
- 8 potential domains analyzed with technical synergy assessment
- Top 3 opportunities identified: Satellite Imagery, Medical Imaging, Time-Series Analytics
- Strategic insight: We're a web-based scientific data visualization platform, not just SEG-Y
- Implementation strategy, market entry, risk assessment, and investment requirements documented

---

*This roadmap is living. Revisit monthly or when major milestones are reached.*
