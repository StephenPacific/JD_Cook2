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
SITES ?= indeed,linkedin,glassdoor,google
RESULTS_WANTED ?= 10
HOURS_OLD ?= 168
MAX_QUERIES ?= 8
RANK ?= 1
DRY_RUN ?=

ifeq ($(SCOPE),approved)
SRC := approved/$(JOB)/$(JOB).tex
else
SRC := drafts/$(JOB).tex
endif

LATEX_OUT := $(OUT_ROOT)/latex/$(SCOPE)/$(JOB)
PDF_OUT := $(OUT_ROOT)/pdf/$(SCOPE)
PDF := $(PDF_OUT)/$(JOB).pdf

.PHONY: pdf draft draft-pdf preview approved approved-pdf import-job plan-jobs match-jobs search-jobs import-search-result check approve export learn clean-draft abort status check-all

pdf:
	@test -f "$(SRC)" || (echo "Missing source: $(SRC)" >&2; exit 1)
	@mkdir -p "$(LATEX_OUT)" "$(PDF_OUT)"
	$(LATEXMK) -g -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir="$(LATEX_OUT)" "$(SRC)"
	@cp "$(LATEX_OUT)/$(JOB).pdf" "$(PDF)"
	@echo "PDF ready: $(PDF)"

draft:
	$(PYTHON) scripts/draft_resume.py --job "$(JOB)" --agent "$(AGENT)" --context-limit "$(CONTEXT_LIMIT)" --context-threshold "$(CONTEXT_THRESHOLD)" $(if $(FORCE),--force)

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
	$(PYTHON) jd_search/search_jobs.py --profile-from-raw --raw-root "$(RAW_ROOT)" --profile-out "$(PROFILE_OUT)" --search "$(SEARCH)" --sites "$(SITES)" --results-wanted "$(RESULTS_WANTED)" --hours-old "$(HOURS_OLD)" --max-queries "$(MAX_QUERIES)" $(if $(QUERY),--query "$(QUERY)") $(if $(LOCATION),--location "$(LOCATION)") $(if $(DRY_RUN),--dry-run) $(if $(FORCE),--force)

search-jobs:
	$(PYTHON) jd_search/search_jobs.py --profile "$(PROFILE)" --search "$(SEARCH)" --sites "$(SITES)" --results-wanted "$(RESULTS_WANTED)" --hours-old "$(HOURS_OLD)" --max-queries "$(MAX_QUERIES)" $(if $(QUERY),--query "$(QUERY)") $(if $(LOCATION),--location "$(LOCATION)") $(if $(FORCE),--force)

import-search-result:
	$(PYTHON) jd_search/import_result.py --search "$(SEARCH)" --rank "$(RANK)" --job "$(JOB)" $(if $(FORCE),--force)

check: draft-pdf
	$(PYTHON) scripts/cycle.py check --job "$(JOB)"

approve: check
	$(PYTHON) scripts/cycle.py approve --job "$(JOB)"

export:
	$(PYTHON) scripts/cycle.py export --job "$(JOB)" $(if $(FORCE),--force)

learn:
	$(PYTHON) scripts/cycle.py learn --job "$(JOB)"

clean-draft:
	$(PYTHON) scripts/cycle.py clean-draft --job "$(JOB)"

abort:
	$(PYTHON) scripts/cycle.py abort --job "$(JOB)"

status:
	$(PYTHON) scripts/cycle.py status --job "$(JOB)"

check-all:
	$(PYTHON) scripts/cycle.py check-all
