.PHONY: alpha alpha-check alpha-gates alpha-first-paint studio-check media-image-plan media-video-plan demo check-fixed check-bad index release-check

alpha:
	python3 scripts/build_site.py projects/alpha-corporate

alpha-check:
	bash scripts/alpha-check.sh projects/alpha-corporate

alpha-gates:
	bash scripts/run-checks.sh projects/alpha-corporate build

alpha-first-paint:
	bash scripts/first-paint.sh projects/alpha-corporate

studio-check:
	python3 probes/studio_contract_check.py projects/alpha-corporate
	python3 probes/video_asset_check.py projects/alpha-corporate

media-image-plan:
	python3 scripts/media_pipeline.py image projects/alpha-corporate home.hero

media-video-plan:
	python3 scripts/media_pipeline.py video projects/alpha-corporate home.hero.motion

demo:
	@echo "### demo-goldenish (expected BLOCKED) ###"; bash scripts/run-checks.sh projects/demo-goldenish build || true
	@echo; echo "### demo-fixed (expected PASS) ###"; bash scripts/run-checks.sh projects/demo-fixed build

check-bad:
	bash scripts/run-checks.sh projects/demo-goldenish build

check-fixed:
	bash scripts/run-checks.sh projects/demo-fixed build

index:
	python3 probes/build_project_index.py projects/alpha-corporate

release-check:
	bash scripts/run-checks.sh projects/alpha-corporate release
