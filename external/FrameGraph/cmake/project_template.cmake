cmake_minimum_required( VERSION 3.10 FATAL_ERROR )

add_library( "ProjectTemplate" INTERFACE )
set_property( TARGET "ProjectTemplate" PROPERTY FOLDER "Utils" )

target_compile_definitions( "ProjectTemplate" INTERFACE ${FG_COMPILER_DEFINITIONS} )
target_link_libraries( "ProjectTemplate" INTERFACE "${FG_LINK_LIBRARIES}" )
	
# Debug
if (PROJECTS_SHARED_CXX_FLAGS_DEBUG)
	target_compile_options( "ProjectTemplate" INTERFACE $<$<CONFIG:Debug>: ${PROJECTS_SHARED_CXX_FLAGS_DEBUG}> )
endif()
if (PROJECTS_SHARED_DEFINES_DEBUG)
	target_compile_definitions( "ProjectTemplate" INTERFACE $<$<CONFIG:Debug>: ${PROJECTS_SHARED_DEFINES_DEBUG}> )
endif()
if (PROJECTS_SHARED_LINKER_FLAGS_DEBUG)
	set_target_properties( "ProjectTemplate" PROPERTIES LINK_FLAGS_DEBUG ${PROJECTS_SHARED_LINKER_FLAGS_DEBUG} )
endif()

# Release
if (PROJECTS_SHARED_CXX_FLAGS_RELEASE)
	target_compile_options( "ProjectTemplate" INTERFACE $<$<CONFIG:Release>: ${PROJECTS_SHARED_CXX_FLAGS_RELEASE}> )
endif()
if (PROJECTS_SHARED_DEFINES_RELEASE)
	target_compile_definitions( "ProjectTemplate" INTERFACE $<$<CONFIG:Release>: ${PROJECTS_SHARED_DEFINES_RELEASE}> )
endif()
if (PROJECTS_SHARED_LINKER_FLAGS_RELEASE)
	set_target_properties( "ProjectTemplate" PROPERTIES LINK_FLAGS_RELEASE ${PROJECTS_SHARED_LINKER_FLAGS_RELEASE} )
endif()

# Profile
if (PROJECTS_SHARED_DEFINES_PROFILE)
	target_compile_definitions( "ProjectTemplate" INTERFACE $<$<CONFIG:Profile>: ${PROJECTS_SHARED_DEFINES_PROFILE}> )
endif()
if (PROJECTS_SHARED_LINKER_FLAGS_PROFILE)
	set_target_properties( "ProjectTemplate" PROPERTIES LINK_FLAGS_PROFILE ${PROJECTS_SHARED_LINKER_FLAGS_PROFILE} )
endif()
if (PROJECTS_SHARED_CXX_FLAGS_PROFILE)
	target_compile_options( "ProjectTemplate" INTERFACE $<$<CONFIG:Profile>: ${PROJECTS_SHARED_CXX_FLAGS_PROFILE}> )
endif()

set_target_properties( "ProjectTemplate" PROPERTIES CXX_STANDARD 17 CXX_STANDARD_REQUIRED YES )
target_compile_features( "ProjectTemplate" INTERFACE cxx_std_17 )

if (FG_CI_BUILD)
	target_compile_definitions( "ProjectTemplate" INTERFACE "FG_CI_BUILD" )
endif()

