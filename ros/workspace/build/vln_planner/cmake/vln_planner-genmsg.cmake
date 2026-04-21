# generated from genmsg/cmake/pkg-genmsg.cmake.em

message(STATUS "vln_planner: 4 messages, 0 services")

set(MSG_I_FLAGS "-Ivln_planner:/home/k325/VLN/ros/workspace/src/vln_planner/msg;-Isensor_msgs:/opt/ros/noetic/share/sensor_msgs/cmake/../msg;-Istd_msgs:/opt/ros/noetic/share/std_msgs/cmake/../msg;-Igeometry_msgs:/opt/ros/noetic/share/geometry_msgs/cmake/../msg")

# Find all generators
find_package(gencpp REQUIRED)
find_package(geneus REQUIRED)
find_package(genlisp REQUIRED)
find_package(gennodejs REQUIRED)
find_package(genpy REQUIRED)

add_custom_target(vln_planner_generate_messages ALL)

# verify that message/service dependencies have not changed since configure



get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetection.msg" NAME_WE)
add_custom_target(_vln_planner_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "vln_planner" "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetection.msg" ""
)

get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetections.msg" NAME_WE)
add_custom_target(_vln_planner_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "vln_planner" "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetections.msg" "vln_planner/ObjectDetection:std_msgs/Header"
)

get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinate.msg" NAME_WE)
add_custom_target(_vln_planner_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "vln_planner" "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinate.msg" "geometry_msgs/Point"
)

get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinates.msg" NAME_WE)
add_custom_target(_vln_planner_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "vln_planner" "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinates.msg" "geometry_msgs/Point:std_msgs/Header:vln_planner/ObjectCoordinate"
)

#
#  langs = gencpp;geneus;genlisp;gennodejs;genpy
#

### Section generating for lang: gencpp
### Generating Messages
_generate_msg_cpp(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetection.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/vln_planner
)
_generate_msg_cpp(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetections.msg"
  "${MSG_I_FLAGS}"
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetection.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/vln_planner
)
_generate_msg_cpp(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinate.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/vln_planner
)
_generate_msg_cpp(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinates.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinate.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/vln_planner
)

### Generating Services

### Generating Module File
_generate_module_cpp(vln_planner
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/vln_planner
  "${ALL_GEN_OUTPUT_FILES_cpp}"
)

add_custom_target(vln_planner_generate_messages_cpp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_cpp}
)
add_dependencies(vln_planner_generate_messages vln_planner_generate_messages_cpp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetection.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_cpp _vln_planner_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetections.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_cpp _vln_planner_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinate.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_cpp _vln_planner_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinates.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_cpp _vln_planner_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(vln_planner_gencpp)
add_dependencies(vln_planner_gencpp vln_planner_generate_messages_cpp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS vln_planner_generate_messages_cpp)

### Section generating for lang: geneus
### Generating Messages
_generate_msg_eus(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetection.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/vln_planner
)
_generate_msg_eus(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetections.msg"
  "${MSG_I_FLAGS}"
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetection.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/vln_planner
)
_generate_msg_eus(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinate.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/vln_planner
)
_generate_msg_eus(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinates.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinate.msg"
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/vln_planner
)

### Generating Services

### Generating Module File
_generate_module_eus(vln_planner
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/vln_planner
  "${ALL_GEN_OUTPUT_FILES_eus}"
)

add_custom_target(vln_planner_generate_messages_eus
  DEPENDS ${ALL_GEN_OUTPUT_FILES_eus}
)
add_dependencies(vln_planner_generate_messages vln_planner_generate_messages_eus)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetection.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_eus _vln_planner_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetections.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_eus _vln_planner_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinate.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_eus _vln_planner_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinates.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_eus _vln_planner_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(vln_planner_geneus)
add_dependencies(vln_planner_geneus vln_planner_generate_messages_eus)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS vln_planner_generate_messages_eus)

### Section generating for lang: genlisp
### Generating Messages
_generate_msg_lisp(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetection.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/vln_planner
)
_generate_msg_lisp(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetections.msg"
  "${MSG_I_FLAGS}"
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetection.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/vln_planner
)
_generate_msg_lisp(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinate.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/vln_planner
)
_generate_msg_lisp(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinates.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinate.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/vln_planner
)

### Generating Services

### Generating Module File
_generate_module_lisp(vln_planner
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/vln_planner
  "${ALL_GEN_OUTPUT_FILES_lisp}"
)

add_custom_target(vln_planner_generate_messages_lisp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_lisp}
)
add_dependencies(vln_planner_generate_messages vln_planner_generate_messages_lisp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetection.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_lisp _vln_planner_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetections.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_lisp _vln_planner_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinate.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_lisp _vln_planner_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinates.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_lisp _vln_planner_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(vln_planner_genlisp)
add_dependencies(vln_planner_genlisp vln_planner_generate_messages_lisp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS vln_planner_generate_messages_lisp)

### Section generating for lang: gennodejs
### Generating Messages
_generate_msg_nodejs(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetection.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/vln_planner
)
_generate_msg_nodejs(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetections.msg"
  "${MSG_I_FLAGS}"
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetection.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/vln_planner
)
_generate_msg_nodejs(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinate.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/vln_planner
)
_generate_msg_nodejs(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinates.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinate.msg"
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/vln_planner
)

### Generating Services

### Generating Module File
_generate_module_nodejs(vln_planner
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/vln_planner
  "${ALL_GEN_OUTPUT_FILES_nodejs}"
)

add_custom_target(vln_planner_generate_messages_nodejs
  DEPENDS ${ALL_GEN_OUTPUT_FILES_nodejs}
)
add_dependencies(vln_planner_generate_messages vln_planner_generate_messages_nodejs)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetection.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_nodejs _vln_planner_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetections.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_nodejs _vln_planner_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinate.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_nodejs _vln_planner_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinates.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_nodejs _vln_planner_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(vln_planner_gennodejs)
add_dependencies(vln_planner_gennodejs vln_planner_generate_messages_nodejs)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS vln_planner_generate_messages_nodejs)

### Section generating for lang: genpy
### Generating Messages
_generate_msg_py(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetection.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/vln_planner
)
_generate_msg_py(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetections.msg"
  "${MSG_I_FLAGS}"
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetection.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/vln_planner
)
_generate_msg_py(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinate.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/vln_planner
)
_generate_msg_py(vln_planner
  "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinates.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinate.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/vln_planner
)

### Generating Services

### Generating Module File
_generate_module_py(vln_planner
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/vln_planner
  "${ALL_GEN_OUTPUT_FILES_py}"
)

add_custom_target(vln_planner_generate_messages_py
  DEPENDS ${ALL_GEN_OUTPUT_FILES_py}
)
add_dependencies(vln_planner_generate_messages vln_planner_generate_messages_py)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetection.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_py _vln_planner_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectDetections.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_py _vln_planner_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinate.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_py _vln_planner_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/vln_planner/msg/ObjectCoordinates.msg" NAME_WE)
add_dependencies(vln_planner_generate_messages_py _vln_planner_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(vln_planner_genpy)
add_dependencies(vln_planner_genpy vln_planner_generate_messages_py)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS vln_planner_generate_messages_py)



if(gencpp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/vln_planner)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/vln_planner
    DESTINATION ${gencpp_INSTALL_DIR}
  )
endif()
if(TARGET sensor_msgs_generate_messages_cpp)
  add_dependencies(vln_planner_generate_messages_cpp sensor_msgs_generate_messages_cpp)
endif()
if(TARGET std_msgs_generate_messages_cpp)
  add_dependencies(vln_planner_generate_messages_cpp std_msgs_generate_messages_cpp)
endif()
if(TARGET geometry_msgs_generate_messages_cpp)
  add_dependencies(vln_planner_generate_messages_cpp geometry_msgs_generate_messages_cpp)
endif()

if(geneus_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/vln_planner)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/vln_planner
    DESTINATION ${geneus_INSTALL_DIR}
  )
endif()
if(TARGET sensor_msgs_generate_messages_eus)
  add_dependencies(vln_planner_generate_messages_eus sensor_msgs_generate_messages_eus)
endif()
if(TARGET std_msgs_generate_messages_eus)
  add_dependencies(vln_planner_generate_messages_eus std_msgs_generate_messages_eus)
endif()
if(TARGET geometry_msgs_generate_messages_eus)
  add_dependencies(vln_planner_generate_messages_eus geometry_msgs_generate_messages_eus)
endif()

if(genlisp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/vln_planner)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/vln_planner
    DESTINATION ${genlisp_INSTALL_DIR}
  )
endif()
if(TARGET sensor_msgs_generate_messages_lisp)
  add_dependencies(vln_planner_generate_messages_lisp sensor_msgs_generate_messages_lisp)
endif()
if(TARGET std_msgs_generate_messages_lisp)
  add_dependencies(vln_planner_generate_messages_lisp std_msgs_generate_messages_lisp)
endif()
if(TARGET geometry_msgs_generate_messages_lisp)
  add_dependencies(vln_planner_generate_messages_lisp geometry_msgs_generate_messages_lisp)
endif()

if(gennodejs_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/vln_planner)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/vln_planner
    DESTINATION ${gennodejs_INSTALL_DIR}
  )
endif()
if(TARGET sensor_msgs_generate_messages_nodejs)
  add_dependencies(vln_planner_generate_messages_nodejs sensor_msgs_generate_messages_nodejs)
endif()
if(TARGET std_msgs_generate_messages_nodejs)
  add_dependencies(vln_planner_generate_messages_nodejs std_msgs_generate_messages_nodejs)
endif()
if(TARGET geometry_msgs_generate_messages_nodejs)
  add_dependencies(vln_planner_generate_messages_nodejs geometry_msgs_generate_messages_nodejs)
endif()

if(genpy_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/vln_planner)
  install(CODE "execute_process(COMMAND \"/home/k325/miniconda3/envs/vln/bin/python3\" -m compileall \"${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/vln_planner\")")
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/vln_planner
    DESTINATION ${genpy_INSTALL_DIR}
  )
endif()
if(TARGET sensor_msgs_generate_messages_py)
  add_dependencies(vln_planner_generate_messages_py sensor_msgs_generate_messages_py)
endif()
if(TARGET std_msgs_generate_messages_py)
  add_dependencies(vln_planner_generate_messages_py std_msgs_generate_messages_py)
endif()
if(TARGET geometry_msgs_generate_messages_py)
  add_dependencies(vln_planner_generate_messages_py geometry_msgs_generate_messages_py)
endif()
