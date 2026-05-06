LATEXMK ?= latexmk
PYTHON ?= python3
JOB ?= ml-genai-engineer
SCOPE ?= drafts
OUT_ROOT ?= build
AGENT ?= auto
CONTEXT_LIMIT ?= 2
CONTEXT_THRESHOLD ?= 25
SEARCH ?= ai-engineer-sydney
PROFILE ?= jd_search/profiles/example.json
PROFILE_OUT ?= jd_search/profiles/generated-from-raw.json
RAW_ROOT ?= raw
QUERY ?=
LOCATION ?=
SITES ?= indeed,linkedin,google,adzuna
# Glassdoor dropped: their unauthenticated location lookup endpoint
# (`findPopularLocationAjax.htm`) returns 403 to all queries since ~2024,
# so JobSpy can't resolve any location ID and every Glassdoor call fails
# with "location not parsed". Re-add it manually if/when JobSpy ships an
# updated Glassdoor adapter.
#
# `adzuna` is implemented locally in jd_search/adzuna.py (JobSpy has no SEEK
# or Adzuna scraper). Set ADZUNA_APP_ID and ADZUNA_APP_KEY in your env
# (free tier: https://developer.adzuna.com/) — without them the adapter
# logs and skips itself silently, so the search still runs on JobSpy alone.
RESULTS_WANTED ?= 10
HOURS_OLD ?= 168
MAX_QUERIES ?= 8
RANK ?= 1
DRY_RUN ?=
TRIAGE_AGENT ?= codex
SECOND_TRIAGE_AGENT ?=
PERSONA ?= jd_search/persona.md
TOP_N ?= 25
LINKEDIN_FETCH ?= 1

ifeq ($(SCOPE),approved)
SRC := approved/$(JOB)/$(JOB).tex
else
SRC := drafts/$(JOB).tex
endif

TRIAGE_JOB_ARG :=
ifneq ($(filter command line environment,$(origin JOB)),)
TRIAGE_JOB_ARG := --job "$(JOB)"
endif

LATEX_OUT := $(OUT_ROOT)/latex/$(SCOPE)/$(JOB)
PDF_OUT := $(OUT_ROOT)/pdf/$(SCOPE)
PDF := $(PDF_OUT)/$(JOB).pdf

.PHONY: pdf draft draft-pdf preview approved approved-pdf import-job plan-jobs match-jobs search-jobs import-search-result triage scan-jobs triage-inbox inbox check approve export learn clean-draft abort status check-all raw-cache applied web-search

pdf:
	@test -f "$(SRC)" || (echo "Missing source: $(SRC)" >&2; exit 1)
	@mkdir -p "$(LATEX_OUT)" "$(PDF_OUT)"
	$(LATEXMK) -g -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir="$(LATEX_OUT)" "$(SRC)"
	@cp "$(LATEX_OUT)/$(JOB).pdf" "$(PDF)"
	@echo "PDF ready: $(PDF)"

draft:
	$(PYTHON) scripts/draft_resume.py --job "$(JOB)" --agent "$(AGENT)" --context-limit "$(CONTEXT_LIMIT)" --context-threshold "$(CONTEXT_THRESHOLD)" $(if $(FROM),--from "$(FROM)") $(if $(URL),--url "$(URL)") $(if $(MODE),--mode "$(MODE)") $(if $(FORCE),--force)

draft-pdf:
	$(MAKE) pdf SCOPE=drafts JOB="$(JOB)"

preview: draft-pdf

approved-pdf:
	$(MAKE) pdf SCOPE=approved JOB="$(JOB)"

approved: approved-pdf

import-job:
	$(PYTHON) scripts/import_job.py --job "$(JOB)" $(if $(FROM),--from "$(FROM)") $(if $(URL),--url "$(URL)") $(if $(MODE),--mode "$(MODE)") $(if $(FORCE),--force)

plan-jobs:
	$(PYTHON) jd_search/search_jobs.py --profile "$(PROFILE)" --search "$(SEARCH)" --sites "$(SITES)" --results-wanted "$(RESULTS_WANTED)" --hours-old "$(HOURS_OLD)" --max-queries "$(MAX_QUERIES)" $(if $(QUERY),--query "$(QUERY)") $(if $(LOCATION),--location "$(LOCATION)") --dry-run $(if $(FORCE),--force)

match-jobs:
	$(PYTHON) jd_search/search_jobs.py --profile-from-raw --raw-root "$(RAW_ROOT)" --profile-out "$(PROFILE_OUT)" --search "$(SEARCH)" --sites "$(SITES)" --results-wanted "$(RESULTS_WANTED)" --hours-old "$(HOURS_OLD)" --max-queries "$(MAX_QUERIES)" $(if $(filter-out 0 false no off,$(LINKEDIN_FETCH)),--linkedin-fetch-description) $(if $(QUERY),--query "$(QUERY)") $(if $(LOCATION),--location "$(LOCATION)") $(if $(DRY_RUN),--dry-run) $(if $(FORCE),--force)

search-jobs:
	$(PYTHON) jd_search/search_jobs.py --profile "$(PROFILE)" --search "$(SEARCH)" --sites "$(SITES)" --results-wanted "$(RESULTS_WANTED)" --hours-old "$(HOURS_OLD)" --max-queries "$(MAX_QUERIES)" $(if $(QUERY),--query "$(QUERY)") $(if $(LOCATION),--location "$(LOCATION)") $(if $(FORCE),--force)

import-search-result:
	$(PYTHON) jd_search/import_result.py --search "$(SEARCH)" --rank "$(RANK)" --job "$(JOB)" $(if $(FORCE),--force)

triage:
	$(PYTHON) jd_search/triage.py --agent "$(TRIAGE_AGENT)" --persona "$(PERSONA)" $(if $(SECOND_TRIAGE_AGENT),--second-agent "$(SECOND_TRIAGE_AGENT)") $(if $(URL),--url "$(URL)") $(if $(FILE),--file "$(FILE)") $(if $(FROM),--from "$(FROM)") $(TRIAGE_JOB_ARG) $(if $(FORCE),--refresh) $(if $(NO_CACHE),--no-cache)

scan-jobs:
	$(MAKE) match-jobs SEARCH="$(SEARCH)" $(if $(QUERY),QUERY="$(QUERY)") $(if $(LOCATION),LOCATION="$(LOCATION)") $(if $(SITES),SITES="$(SITES)") $(if $(RESULTS_WANTED),RESULTS_WANTED="$(RESULTS_WANTED)") $(if $(HOURS_OLD),HOURS_OLD="$(HOURS_OLD)") $(if $(FORCE),FORCE=1)
	$(MAKE) triage-inbox SEARCH="$(SEARCH)" $(if $(TOP_N),TOP_N="$(TOP_N)") $(if $(TRIAGE_AGENT),TRIAGE_AGENT="$(TRIAGE_AGENT)") $(if $(REJUDGE),REJUDGE=1)

triage-inbox:
	@test -f "jd_search/searches/$(SEARCH)/ranked_jobs.json" || (echo "No ranked_jobs.json for SEARCH=$(SEARCH); run \`make match-jobs SEARCH=$(SEARCH)\` first." >&2; exit 1)
	$(PYTHON) scripts/scan_to_inbox.py --search "$(SEARCH)" --top-n "$(TOP_N)" --agent "$(TRIAGE_AGENT)" --persona "$(PERSONA)" $(if $(REJUDGE),--rejudge)

inbox:
	@if [ -f jd_search/inbox.md ]; then cat jd_search/inbox.md; else echo "No inbox yet. Run \`make scan-jobs SEARCH=<slug>\` first."; fi

check: draft-pdf
	$(PYTHON) scripts/cycle.py check --job "$(JOB)"

approve: check
	$(PYTHON) scripts/cycle.py approve --job "$(JOB)"

export:
	$(PYTHON) scripts/cycle.py export --job "$(JOB)" $(if $(FORCE),--force)

learn:
	$(PYTHON) scripts/cycle.py learn --job "$(JOB)"

applied:
	$(PYTHON) scripts/cycle.py applied --job "$(JOB)" $(if $(FORCE),--force)

web-search:
	@test -n "$(QUERY)" || (echo "Usage: make web-search QUERY=\"<free-form search intent>\"" >&2; exit 1)
	$(PYTHON) scripts/web_search.py --query "$(QUERY)"

clean-draft:
	$(PYTHON) scripts/cycle.py clean-draft --job "$(JOB)"

abort:
	$(PYTHON) scripts/cycle.py abort --job "$(JOB)"

status:
	$(PYTHON) scripts/cycle.py status --job "$(JOB)"

check-all:
	$(PYTHON) scripts/cycle.py check-all

raw-cache:
	$(PYTHON) scripts/raw_cache.py $(if $(FORCE),--force)
