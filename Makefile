LATEXMK ?= latexmk
PYTHON ?= python3
JOB ?= ml-genai-engineer
SCOPE ?= drafts
OUT_ROOT ?= build
AGENT ?= auto
CONTEXT_LIMIT ?= 2
CONTEXT_THRESHOLD ?= 25

ifeq ($(SCOPE),approved)
SRC := approved/$(JOB)/$(JOB).tex
else
SRC := drafts/$(JOB).tex
endif

LATEX_OUT := $(OUT_ROOT)/latex/$(SCOPE)/$(JOB)
PDF_OUT := $(OUT_ROOT)/pdf/$(SCOPE)
PDF := $(PDF_OUT)/$(JOB).pdf

.PHONY: pdf draft draft-pdf preview approved approved-pdf import-job check approve export learn clean-draft abort status check-all

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
