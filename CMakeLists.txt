cmake_minimum_required(VERSION 3.5.0)

#-----------------------------------------------------------------------------
set(EXTENSION_NAME SlicerPIRADS)
set(EXTENSION_HOMEPAGE "http://wiki.slicer.org/slicerWiki/index.php/Documentation/Nightly/Modules/QuantitativeReporting")
set(EXTENSION_CATEGORY "Informatics")
set(EXTENSION_CONTRIBUTORS "Andrey Fedorov (SPL), Christian Herz (SPL)")
set(EXTENSION_DESCRIPTION "Support of PI-RADS Reporting")
set(EXTENSION_STATUS "Work in progress")
set(EXTENSION_DEPENDS SlicerDevelopmentToolbox)

#-----------------------------------------------------------------------------

set(MODULE_NAME SlicerPIRADS)

find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

add_subdirectory(SlicerPIRADS)

#-----------------------------------------------------------------------------

if(BUILD_TESTING)
  add_subdirectory(Testing)
endif()

#-----------------------------------------------------------------------------

include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
