# Nabtiq delivery system — Wave 0
.PHONY: demo check-fixed check-bad index seal
demo: ## run both demos (bad blocks, fixed passes)
	@echo "### demo-goldenish (expected BLOCKED) ###"; bash scripts/run-checks.sh projects/demo-goldenish || true
	@echo; echo "### demo-fixed (expected PASS) ###"; bash scripts/run-checks.sh projects/demo-fixed
check-bad:  ; bash scripts/run-checks.sh projects/demo-goldenish
check-fixed:; bash scripts/run-checks.sh projects/demo-fixed
index:      ; python3 probes/build_project_index.py projects/demo-fixed
first-paint: ## live first-paint probe on the demo build (needs playwright)
	bash scripts/first-paint.sh projects/demo-fixed
