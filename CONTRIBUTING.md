## Project Management
This project uses Poetry for managing builds and dependencies.


# Dev Container

Create with `make build_docker_dev` and `make run_docker`

Once in the container run:
```
poetry install
poetry shell
FLASK_APP=sparrow.server flask run -h 0.0.0.0 --debug
```

# Poetry

## Add Dependencies
```
poetry add <package name>
```

## Install Dependencies
```
poetry install
```

## Open Venv 
```
poetry shell
```