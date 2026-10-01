cmake_minimum_required(VERSION 3.14)
project(compas_knit_sim CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()
# fabsim and optim declare cmake_minimum_required 3.1, which newer CMake refuses without this
set(CMAKE_POLICY_VERSION_MINIMUM 3.5)

include(FetchContent)
FetchContent_Declare(
  fabsim
  GIT_REPOSITORY https://github.com/duchaoyu/fabsim
  GIT_TAG 15585aa  # the orthotropic StVK membrane, rods
  # the pressure work was 3 p V, (x0 + x1 + x2) . n / 6 instead of / 18; applied once, skipped when already applied
  PATCH_COMMAND sh -c "git apply --reverse --check ${CMAKE_CURRENT_SOURCE_DIR}/patches/fabsim_pressure_volume.patch 2>/dev/null || git apply ${CMAKE_CURRENT_SOURCE_DIR}/patches/fabsim_pressure_volume.patch"
)
FetchContent_Declare(
  optim
  GIT_REPOSITORY https://github.com/DavidJourdan/optim
  GIT_TAG aab6acc  # Newton solver; the line search settings of the thesis are set in knit_sim.cpp
)
FetchContent_Declare(
  json
  URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.tar.xz
)
set(FABSIM_BUILD_TESTS OFF CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(fabsim optim json)

add_executable(knit_sim src/knit_sim.cpp)
target_link_libraries(knit_sim fabsim optim nlohmann_json::nlohmann_json)
