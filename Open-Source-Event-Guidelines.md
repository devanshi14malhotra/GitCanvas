# GitCanvas Contributor Guide for for Open Source Events

This document is tailored for contributors participating in all open source events: _Nexus Spring of Code, ACM Sourcery and Apertre3.0._

[![GitCanvas - Issues](https://img.shields.io/badge/GitCanvas-Issues-9113ff?style=for-the-badge)](https://github.com/devanshi14malhotra/GitCanvas/issues)

## 1. Project Overview

### Description
GitCanvas is a Python-based project that turns GitHub contribution and profile data into beautiful visual cards and themed graphics. It includes a Streamlit app for interactive use and a FastAPI service for programmatic generation.

### Tech Stack
- Frontend/UI: Streamlit
- Backend/API: FastAPI
- Language: Python 3
- Data Source: GitHub REST APIs
- AI Integration: OpenAI and Google Gemini support for roast mode
- Image/Output: SVG-based generators with optional raster export

### Current Features
- 15+ visual themes for contribution graph rendering
- Multiple README-ready cards: stats, streak, repo, language, trophy, social, and activity
- AI roast widget with multiple tones
- Export-friendly SVG output for profile personalization
- FastAPI endpoints for card generation

### Target Users
- GitHub users who want personalized profile visuals
- Open source contributors building profile tools
- Students and developers exploring creative data visualization

---

## 2. Architecture and Key Modules

### Module Overview

| Module | Location | Purpose |
|---|---|---|
| Streamlit App | app.py | Main interactive UI for users |
| Streamlit UI Components | ui/ | Theme gallery and AI roast/compliment widgets |
| API Service | api/main.py | FastAPI entrypoint with route handlers |
| AI Services | ai/ | Roast service and model integration logic |
| Card Generators | generators/ | SVG builders for all card variants |
| Themes | themes/ and themes/json/ | Theme definitions and palettes |
| Utilities | utils/ | GitHub API wrappers, caching, validation, logging, rate limiting |

### High-Level Flow
1. User provides a GitHub username and card/theme preferences.
2. Utility layer fetches GitHub data with validation and caching.
3. Generator layer builds themed SVG output.
4. Streamlit and API layers expose downloadable and embeddable results.

---

## 3. Feature Ideas for Sourcery Contributors

### Feature 1: Theme Preview Grid in Streamlit
Problem it solves: Contributors currently switch themes one-by-one to compare outputs.

- Difficulty: Beginner
- Estimated effort: 4-6 hours
- Suggested files:
  - app.py
  - themes/styles.py

### Feature 2: Theme Metadata and Search
Problem it solves: Finding themes by vibe (retro, sci-fi, sports) is manual.

- Difficulty: Beginner to Intermediate
- Estimated effort: 6-8 hours
- Suggested files:
  - themes/__init__.py
  - themes/json/*.json
  - app.py

### Feature 3: Add Compact Card Layout Variant
Problem it solves: Existing cards can feel large for minimal README layouts.

- Difficulty: Intermediate
- Estimated effort: 8-12 hours
- Suggested files:
  - generators/svg_base.py
  - generators/stats_card.py
  - generators/repo_card.py

### Feature 4: Better GitHub API Error Messaging
Problem it solves: Users need clearer next steps when rate-limited or username is invalid.

- Difficulty: Intermediate
- Estimated effort: 6-10 hours
- Suggested files:
  - utils/github_api.py
  - utils/validators.py
  - utils/api_validators.py
  - app.py

### Feature 5: Add Basic Tests for Generators
Problem it solves: Generator changes are hard to validate quickly and safely.

- Difficulty: Intermediate
- Estimated effort: 8-14 hours
- Suggested files:
  - tests/ (new folder)
  - generators/*.py

---

## 4. Implementation Pipeline (Recommended)

Follow this checklist for any feature PR during Sourcery.

1. Understand scope
- Pick one issue and confirm expected output in the PR description.

2. Set up locally
- Install dependencies from requirements.txt.
- Run streamlit run app.py.
- Optionally run the API using uvicorn.

3. Implement small and focused changes
- Keep PRs single-purpose.
- Reuse utility modules where possible.

4. Validate with real usernames
- Test at least 2-3 public GitHub profiles.
- Check behavior when data is missing or sparse.

5. Verify outputs
- Ensure generated SVG renders correctly.
- Check readability in light/dark GitHub themes where relevant.

6. Submit polished PR
- Add before/after screenshots for visual changes.
- Mention files touched and testing done.

---

## 5. Good First Issues

### Issue 1: Improve Copy Text in UI
- Update wording for clarity and grammar.
- Files: app.py, ui/roast_widget.py, ui/compliment_widget.py

### Issue 2: Add Empty-State Message for Missing Repos
- Show user-friendly text when repo list is empty.
- Files: generators/repo_card.py, utils/github_utils.py

### Issue 3: Add One New Theme JSON
- Add one original theme and register it.
- Files: themes/json/*.json, themes/__init__.py

### Issue 4: Expose Rate Limit Info in UI
- Display remaining calls and reset time.
- Files: utils/rate_limiter.py, app.py

### Issue 5: Document One API Endpoint Better
- Improve example request/response in docs.
- Files: README.md or PROJECT_DETAILS.md

---

#### 🎨 Apart from these, you’re encouraged to come up with your own ideas as well... You can raise new issues, get them assigned, and then submit PRs. Feel free to be creative, as this application is for you, and it’s a great opportunity to make your GitHub README truly reflect your personality...
#### You can also explore existing issues and pick up any that interest you...

---

## 6. Contributor Notes

### Prerequisites
- Python 3.9+
- Git

### Local Setup
```bash
### Fork-First Workflow (Required for External Contributors)
1. Fork this repository to your own GitHub account.
2. Clone your fork locally, not the upstream repository.
3. Create a feature branch, push to your fork, then open a PR from your fork to upstream.

```bash
git clone https://github.com/<your-username>/GitCanvas.git
cd GitCanvas
git remote add upstream https://github.com/devanshi14malhotra/GitCanvas.git
git checkout -b feature/your-change
pip install -r requirements.txt
streamlit run app.py
```

### Optional Environment Variables
- GITHUB_TOKEN: Raises API limit significantly for GitHub requests
- OPENAI_API_KEY: Enables OpenAI-based roast generation
- GEMINI_API_KEY: Enables Gemini-based roast generation

### Contribution Rules
- Use real GitHub data only.
- Keep functions modular and readable.
- Do not break existing themes or card contracts.
- Add concise docs for any new user-facing behavior.

### PR Checklist
- Repository was forked and branch was pushed to your fork.
- Pull request target is `devanshi14malhotra/GitCanvas`.
- Code runs locally.
- Visual output verified for the changed card/theme.
- README or inline docs updated if behavior changed.
- PR includes clear summary and screenshots when UI is affected.

---

## 7. Open Source Event Context

Currently, this repository is a part of the _**Nexus Spring of Code** Open Source Event_. This repository has participated in _**Sourcery** by ACM IGDTUW_ and _**Apertre3.0** by Resourcio Community_. Contributors are encouraged to start with beginner-friendly issues, then move into recommendation logic, mood flows, and UI refinements.


If you are new to the project, start with one of the Good First Issues above and open a draft PR early for feedback.

Happy building and all the best!!!

``` bash
 If you like this project, please consider giving the repository a ⭐ STAR ⭐.
```
