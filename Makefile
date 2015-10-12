# target: run — run project
run:
	gunicorn -b 0.0.0.0:8080 -k aiohttp.worker.GunicornWebWorker -w 1 -t 3600 main:app --reload
