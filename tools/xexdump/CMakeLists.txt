cmake_minimum_required(VERSION 3.20)
project(xexdump CXX C)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

# XenonRecomp checkout (reference/XenonRecomp with submodules)
set(XENONRECOMP_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../reference/XenonRecomp" CACHE PATH "XenonRecomp source tree")
add_subdirectory(${XENONRECOMP_DIR} xenonrecomp EXCLUDE_FROM_ALL)

add_executable(xexdump xexdump.cpp)
target_link_libraries(xexdump PRIVATE XenonUtils)
