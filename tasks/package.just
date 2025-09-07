# run package tasks
[group('package')]
package: package-requirements

# export package requirements
[group('package')]
package-requirements:
	uv export --no-dev --no-hashes --no-editable \
		--no-emit-project --output-file=requirements.txt
