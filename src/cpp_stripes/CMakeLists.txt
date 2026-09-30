cmake_minimum_required(VERSION 3.16)

project(compas_knit_stripes)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

include(FetchContent)

# same revisions as shrink-morph, so the trajectories match the ones it produced
FetchContent_Declare(
  libigl
  GIT_REPOSITORY https://github.com/libigl/libigl.git
  GIT_TAG fd16e24391f3a85628999fe67b84a9b2201f2bc2
)
FetchContent_Declare(
  polyscope
  GIT_REPOSITORY https://github.com/nmwsharp/polyscope.git
  GIT_TAG 6bcc99ba68d832a764e60b7e74f542ada1e348bb
)
FetchContent_Declare(
  geometry-central
  GIT_REPOSITORY https://github.com/nmwsharp/geometry-central.git
  GIT_TAG ca6ca18b4f761d69f60ba33aa5f869269cf97e3f
)
FetchContent_MakeAvailable(libigl polyscope geometry-central)

add_executable(stripes src/main.cpp src/polyline.cpp src/singularities.cpp src/stitches.cpp src/neighbours.cpp src/remesh.cpp)
target_link_libraries(stripes Eigen3::Eigen geometry-central polyscope igl::core)

target_compile_options(stripes PRIVATE $<$<CONFIG:RELEASE>:
  $<$<OR:$<CXX_COMPILER_ID:Clang>,$<CXX_COMPILER_ID:AppleClang>,$<CXX_COMPILER_ID:GNU>>:-Ofast>
  $<$<CXX_COMPILER_ID:MSVC>:/Ox>>)

# remove annoying Polyscope-related compiler warning
target_compile_options(stripes PRIVATE
  $<$<OR:$<CXX_COMPILER_ID:Clang>,$<CXX_COMPILER_ID:AppleClang>,$<CXX_COMPILER_ID:GNU>>:-Wno-nonnull>)
