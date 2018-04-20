#!/usr/bin/env bash
SLICER="/Applications/Slicer.app/Contents/MacOS/Slicer"

$SLICER --python-code "from SlicerPIRADS import SlicerPIRADSSlicelet; slicelet=SlicerPIRADSSlicelet();" --no-splash --no-main-window