cmake_minimum_required(VERSION 3.0)
project(socket)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11 -static" )
find_package(Threads)


include_directories(. include)
set(./src SRC_DIR)

add_executable(server src/server.cpp src/TCPServer.cpp)
add_executable(client src/client.cpp src/TCPClient.cpp)

target_link_libraries (server ${CMAKE_THREAD_LIBS_INIT})
# target_link_libraries (client ${CMAKE_THREAD_LIBS_INIT})
