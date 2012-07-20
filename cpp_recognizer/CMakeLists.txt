project( RecogServer )
find_package( OpenCV REQUIRED )
find_package( Boost COMPONENTS system filesystem REQUIRED )
add_executable( RecogServer RecogServer )
target_link_libraries( RecogServer ${OpenCV_LIBS} )
target_link_libraries( RecogServer
    ${Boost_FILESYSTEM_LIBRARY}
    ${Boost_SYSTEM_LIBRARY}
)

