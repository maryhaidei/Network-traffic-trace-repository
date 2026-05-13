LOADTEST_ENV := .env.loadtest

loadtest-ui:
	@set -a; source $(LOADTEST_ENV); set +a; \
	locust -f loadtests/locustfile.py --host=$$LOADTEST_HOST

loadtest-headless:
	@mkdir -p loadtests/results
	@set -a; source $(LOADTEST_ENV); set +a; \
	locust -f loadtests/locustfile.py \
		--host=$$LOADTEST_HOST \
		--headless \
		-u $$LOCUST_USERS \
		-r $$LOCUST_SPAWN_RATE \
		--run-time $$LOCUST_RUN_TIME \
		--csv=$$LOCUST_CSV

loadtest-smoke:
	@mkdir -p loadtests/results
	@set -a; source $(LOADTEST_ENV); set +a; \
	locust -f loadtests/locustfile.py \
		--host=$$LOADTEST_HOST \
		--headless \
		-u 5 \
		-r 1 \
		--run-time 1m \
		--csv=loadtests/results/smoke