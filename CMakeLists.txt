cmake_minimum_required(VERSION 3.22)
project(color_looks_mvp_v1 VERSION 1.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(COLORLOOKS_BUILD_TESTS "Build test utilities" ON)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

# Metal (and Objective-C++) exist only on Apple platforms. Elsewhere the
# tools still build, so presets and OCIO configs can be checked on any OS.
if(APPLE)
    enable_language(OBJCXX)
    find_package(Metal REQUIRED)
endif()

find_package(OpenColorIO REQUIRED)

add_subdirectory(tools)

if(COLORLOOKS_BUILD_TESTS)
    enable_testing()
    find_package(Python3 COMPONENTS Interpreter)
    if(Python3_FOUND)
        # Every shipped preset must satisfy the schema, and every pack must
        # reference looks that exist.
        add_test(NAME presets_match_schema
            COMMAND ${Python3_EXECUTABLE}
                ${CMAKE_CURRENT_SOURCE_DIR}/tools/preset_validator/validate.py
                ${CMAKE_CURRENT_SOURCE_DIR}/assets/presets)
    endif()
endif()
