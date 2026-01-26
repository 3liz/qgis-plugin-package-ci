# QGIS Plugin Package

Contains scripts to perform automated testing and deployment for QGIS plugins.

This a rewrite of the [qgis-plugin-ci](https://opengisch.github.io/qgis-plugin-ci) initial 

## Differences from qgis-plugin-ci

* Move tests to pytest
* Move linter to ruff/mypy
* Use uv as project management tool
* Migrated transifex management to another tool
* Do not handle resource file compilation

This is actually an experimental proof of concept not ready for production (behavior may change 
without further notice).

For QGIS plugin management, please use https://opengisch.github.io/qgis-plugin-ci/.




