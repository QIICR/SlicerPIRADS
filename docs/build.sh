#!/usr/bin/env bash
sphinx-apidoc ../SlicerPIRADS/ -o source --ext-autodoc --ext-viewcode --ext-todo -f
make html
open ./build/html/index.html