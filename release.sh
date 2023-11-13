#!/usr/bin/env bash
python setup.py sdist \
&& twine upload dist/* \
&& rm -rf *.egg-info build dist
