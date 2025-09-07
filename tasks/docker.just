# variables
GCLOUD_ADC_PATH := ".config/gcloud/application_default_credentials.json"

# run docker tasks
[group('docker')]
docker: docker-build docker-run

# build docker image
[group('docker')]
docker-build tag="latest": package-requirements
    docker build --tag={{REPOSITORY}}:{{tag}} .

# run docker image by tag
[group('docker')]
docker-run tag="latest" port="8080":
    docker run --env-file=.env --rm -it -p {{port}}:{{port}} \
    -v ~/{{GCLOUD_ADC_PATH}}:/home/runner/{{GCLOUD_ADC_PATH}}:ro \
    {{REPOSITORY}}:{{tag}}
