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

find_package(SlicerDevelopmentToolbox REQUIRED)

set(DEPENDENCY_BUILD_DIRS "")
if(CMAKE_CONFIGURATION_TYPES)
  foreach(config ${CMAKE_CONFIGURATION_TYPES})
    list(APPEND DEPENDENCY_BUILD_DIRS "${SlicerDevelopmentToolbox_DIR}/${Slicer_QTLOADABLEMODULES_LIB_DIR}/${config}")
    list(APPEND DEPENDENCY_BUILD_DIRS "${SlicerDevelopmentToolbox_DIR}/${Slicer_CLIMODULES_LIB_DIR}/${config}")
  endforeach()
else()
  set(DEPENDENCY_BUILD_DIRS "${SlicerDevelopmentToolbox_DIR}/${Slicer_QTLOADABLEMODULES_LIB_DIR}")
  set(DEPENDENCY_BUILD_DIRS "${SlicerDevelopmentToolbox_DIR}/${Slicer_CLIMODULES_LIB_DIR}")
endif()

# message("DEPENDENCY_BUILD_DIRS: ${DEPENDENCY_BUILD_DIRS}")
set(DEPENDENCIES_ADDITIONAL_MODULE_PATHS
  ${DEPENDENCY_BUILD_DIRS}
  ${SlicerDevelopmentToolbox_DIR}/${Slicer_QTSCRIPTEDMODULES_LIB_DIR}
)

#-----------------------------------------------------------------------------

add_subdirectory(DICOMPlugins)
add_subdirectory(SlicerPIRADS)

#-----------------------------------------------------------------------------

if(BUILD_TESTING)
  add_subdirectory(Testing)
endif()

#-----------------------------------------------------------------------------

include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
