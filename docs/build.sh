#!/usr/bin/env bash
sphinx-apidoc ../SlicerPIRADS/ -o . --ext-autodoc --ext-viewcode --ext-todo -f
make clean
make html
open ./build/html/index.html