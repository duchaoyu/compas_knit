if(TARGET igl::core)
    return()
endif()

include(FetchContent)
FetchContent_Declare(
    libigl
    GIT_REPOSITORY https://github.com/libigl/libigl.git
    GIT_TAG f5702f63e7c54869f1cd54d50f5e262bd57a4275
)
FetchContent_MakeAvailable(libigl)
