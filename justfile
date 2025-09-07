# https://just.systems/man/en/

# REQUIRES

docker := require("docker")
find := require("find")
rm := require("rm")
uv := require("uv")

# SETTINGS

set dotenv-load := true

# ENVIRONS

export UV_ENV_FILE := ".env"

# VARIABLES

REPOSITORY := "fmind-ai-assistant"
SOURCES := "app.py"
TESTS := "test_app.py"

# DEFAULTS

# display help information
default:
    @just --list

# IMPORTS

import 'tasks/app.just'
import 'tasks/check.just'
import 'tasks/clean.just'
import 'tasks/docker.just'
import 'tasks/format.just'
import 'tasks/install.just'
import 'tasks/package.just'
