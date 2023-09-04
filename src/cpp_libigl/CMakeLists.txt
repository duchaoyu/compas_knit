cmake_minimum_required(VERSION 3.16)
project(cpp_geodesic)

list(PREPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake)

# Libigl
include(libigl)

# Enable the target igl::glfw
igl_include(glfw)


# Add your project files
file(GLOB SRC_FILES *.cpp)
add_executable(${PROJECT_NAME} ${SRC_FILES})

option(LIBIGL_IMGUI "Build target igl::imgui" ON)
option (LIBIGL_WITH_OPENGL "Use OpenGL" ON)
option (LIBIGL_WITH_OPENGL_GLFW "Use GLFW" ON)
option (LIBIGL_WITH_OPENGL_GLFW_IMGUI "Use ImGui" ON)

target_link_libraries(${PROJECT_NAME} PUBLIC igl::glfw)
