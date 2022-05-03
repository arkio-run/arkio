#!/usr/bin/env bash
python setup.py sdist \
&& pip install dist/arkio-0.0.3.tar.gz -U \
&& rm -rf *.egg-info build dist
