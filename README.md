# SQLAlchemy 1.4 Quick Start
This is the code from the [*SQLAlchemy Quick Start*](https://docs.sqlalchemy.org/en/14/orm/quickstart.html) guide, posted here for personal notes usage.

# Docker
To get this up and running using *Docker*
1. `$ docker run -d -v /src:/path/to/this/git/repo -t python:bullseye`
2. `$ docker exec -it <container_name> /bin/bash`
3. `# apt-get update && apt-get -y upgrade`
4. `# pip install pip`
5. `# pip install SQLAlchemy`
6. `# python3 /src/quick_start.py`

# Credits
All the code is the original work of the *SQLAlchemy* team.  No `LICENSE` is included in this repository for that reason.
