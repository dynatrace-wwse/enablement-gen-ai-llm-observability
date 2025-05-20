build:
	docker build -t shinojosa/ai-travel-advisor:v0.1.1 .

push:
	docker push shinojosa/ai-travel-advisor:v0.1.1

login:
	docker logout && docker login

test: 
	docker run -p 8080:80 -v /Users/sergio.hinojosa/repos/enablement/enablement-gen-ai-llm-observability/app/public:/usr/share/nginx/html nginx
