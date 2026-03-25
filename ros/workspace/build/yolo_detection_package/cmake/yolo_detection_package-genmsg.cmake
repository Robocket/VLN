# generated from genmsg/cmake/pkg-genmsg.cmake.em

message(STATUS "yolo_detection_package: 4 messages, 0 services")

set(MSG_I_FLAGS "-Iyolo_detection_package:/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg;-Isensor_msgs:/opt/ros/noetic/share/sensor_msgs/cmake/../msg;-Istd_msgs:/opt/ros/noetic/share/std_msgs/cmake/../msg;-Igeometry_msgs:/opt/ros/noetic/share/geometry_msgs/cmake/../msg")

# Find all generators
find_package(gencpp REQUIRED)
find_package(geneus REQUIRED)
find_package(genlisp REQUIRED)
find_package(gennodejs REQUIRED)
find_package(genpy REQUIRED)

add_custom_target(yolo_detection_package_generate_messages ALL)

# verify that message/service dependencies have not changed since configure



get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetection.msg" NAME_WE)
add_custom_target(_yolo_detection_package_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "yolo_detection_package" "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetection.msg" ""
)

get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetections.msg" NAME_WE)
add_custom_target(_yolo_detection_package_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "yolo_detection_package" "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetections.msg" "std_msgs/Header:yolo_detection_package/ObjectDetection"
)

get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinate.msg" NAME_WE)
add_custom_target(_yolo_detection_package_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "yolo_detection_package" "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinate.msg" "geometry_msgs/Point"
)

get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinates.msg" NAME_WE)
add_custom_target(_yolo_detection_package_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "yolo_detection_package" "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinates.msg" "std_msgs/Header:yolo_detection_package/ObjectCoordinate:geometry_msgs/Point"
)

#
#  langs = gencpp;geneus;genlisp;gennodejs;genpy
#

### Section generating for lang: gencpp
### Generating Messages
_generate_msg_cpp(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetection.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/yolo_detection_package
)
_generate_msg_cpp(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetections.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetection.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/yolo_detection_package
)
_generate_msg_cpp(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinate.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/yolo_detection_package
)
_generate_msg_cpp(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinates.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinate.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/yolo_detection_package
)

### Generating Services

### Generating Module File
_generate_module_cpp(yolo_detection_package
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/yolo_detection_package
  "${ALL_GEN_OUTPUT_FILES_cpp}"
)

add_custom_target(yolo_detection_package_generate_messages_cpp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_cpp}
)
add_dependencies(yolo_detection_package_generate_messages yolo_detection_package_generate_messages_cpp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetection.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_cpp _yolo_detection_package_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetections.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_cpp _yolo_detection_package_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinate.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_cpp _yolo_detection_package_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinates.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_cpp _yolo_detection_package_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(yolo_detection_package_gencpp)
add_dependencies(yolo_detection_package_gencpp yolo_detection_package_generate_messages_cpp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS yolo_detection_package_generate_messages_cpp)

### Section generating for lang: geneus
### Generating Messages
_generate_msg_eus(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetection.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/yolo_detection_package
)
_generate_msg_eus(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetections.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetection.msg"
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/yolo_detection_package
)
_generate_msg_eus(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinate.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/yolo_detection_package
)
_generate_msg_eus(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinates.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinate.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/yolo_detection_package
)

### Generating Services

### Generating Module File
_generate_module_eus(yolo_detection_package
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/yolo_detection_package
  "${ALL_GEN_OUTPUT_FILES_eus}"
)

add_custom_target(yolo_detection_package_generate_messages_eus
  DEPENDS ${ALL_GEN_OUTPUT_FILES_eus}
)
add_dependencies(yolo_detection_package_generate_messages yolo_detection_package_generate_messages_eus)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetection.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_eus _yolo_detection_package_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetections.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_eus _yolo_detection_package_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinate.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_eus _yolo_detection_package_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinates.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_eus _yolo_detection_package_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(yolo_detection_package_geneus)
add_dependencies(yolo_detection_package_geneus yolo_detection_package_generate_messages_eus)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS yolo_detection_package_generate_messages_eus)

### Section generating for lang: genlisp
### Generating Messages
_generate_msg_lisp(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetection.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/yolo_detection_package
)
_generate_msg_lisp(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetections.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetection.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/yolo_detection_package
)
_generate_msg_lisp(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinate.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/yolo_detection_package
)
_generate_msg_lisp(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinates.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinate.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/yolo_detection_package
)

### Generating Services

### Generating Module File
_generate_module_lisp(yolo_detection_package
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/yolo_detection_package
  "${ALL_GEN_OUTPUT_FILES_lisp}"
)

add_custom_target(yolo_detection_package_generate_messages_lisp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_lisp}
)
add_dependencies(yolo_detection_package_generate_messages yolo_detection_package_generate_messages_lisp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetection.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_lisp _yolo_detection_package_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetections.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_lisp _yolo_detection_package_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinate.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_lisp _yolo_detection_package_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinates.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_lisp _yolo_detection_package_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(yolo_detection_package_genlisp)
add_dependencies(yolo_detection_package_genlisp yolo_detection_package_generate_messages_lisp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS yolo_detection_package_generate_messages_lisp)

### Section generating for lang: gennodejs
### Generating Messages
_generate_msg_nodejs(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetection.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/yolo_detection_package
)
_generate_msg_nodejs(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetections.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetection.msg"
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/yolo_detection_package
)
_generate_msg_nodejs(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinate.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/yolo_detection_package
)
_generate_msg_nodejs(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinates.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinate.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/yolo_detection_package
)

### Generating Services

### Generating Module File
_generate_module_nodejs(yolo_detection_package
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/yolo_detection_package
  "${ALL_GEN_OUTPUT_FILES_nodejs}"
)

add_custom_target(yolo_detection_package_generate_messages_nodejs
  DEPENDS ${ALL_GEN_OUTPUT_FILES_nodejs}
)
add_dependencies(yolo_detection_package_generate_messages yolo_detection_package_generate_messages_nodejs)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetection.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_nodejs _yolo_detection_package_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetections.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_nodejs _yolo_detection_package_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinate.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_nodejs _yolo_detection_package_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinates.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_nodejs _yolo_detection_package_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(yolo_detection_package_gennodejs)
add_dependencies(yolo_detection_package_gennodejs yolo_detection_package_generate_messages_nodejs)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS yolo_detection_package_generate_messages_nodejs)

### Section generating for lang: genpy
### Generating Messages
_generate_msg_py(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetection.msg"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/yolo_detection_package
)
_generate_msg_py(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetections.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetection.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/yolo_detection_package
)
_generate_msg_py(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinate.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/yolo_detection_package
)
_generate_msg_py(yolo_detection_package
  "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinates.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinate.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/yolo_detection_package
)

### Generating Services

### Generating Module File
_generate_module_py(yolo_detection_package
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/yolo_detection_package
  "${ALL_GEN_OUTPUT_FILES_py}"
)

add_custom_target(yolo_detection_package_generate_messages_py
  DEPENDS ${ALL_GEN_OUTPUT_FILES_py}
)
add_dependencies(yolo_detection_package_generate_messages yolo_detection_package_generate_messages_py)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetection.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_py _yolo_detection_package_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectDetections.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_py _yolo_detection_package_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinate.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_py _yolo_detection_package_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/k325/VLN/ros/workspace/src/yolo_detection_package/msg/ObjectCoordinates.msg" NAME_WE)
add_dependencies(yolo_detection_package_generate_messages_py _yolo_detection_package_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(yolo_detection_package_genpy)
add_dependencies(yolo_detection_package_genpy yolo_detection_package_generate_messages_py)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS yolo_detection_package_generate_messages_py)



if(gencpp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/yolo_detection_package)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/yolo_detection_package
    DESTINATION ${gencpp_INSTALL_DIR}
  )
endif()
if(TARGET sensor_msgs_generate_messages_cpp)
  add_dependencies(yolo_detection_package_generate_messages_cpp sensor_msgs_generate_messages_cpp)
endif()
if(TARGET std_msgs_generate_messages_cpp)
  add_dependencies(yolo_detection_package_generate_messages_cpp std_msgs_generate_messages_cpp)
endif()
if(TARGET geometry_msgs_generate_messages_cpp)
  add_dependencies(yolo_detection_package_generate_messages_cpp geometry_msgs_generate_messages_cpp)
endif()

if(geneus_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/yolo_detection_package)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/yolo_detection_package
    DESTINATION ${geneus_INSTALL_DIR}
  )
endif()
if(TARGET sensor_msgs_generate_messages_eus)
  add_dependencies(yolo_detection_package_generate_messages_eus sensor_msgs_generate_messages_eus)
endif()
if(TARGET std_msgs_generate_messages_eus)
  add_dependencies(yolo_detection_package_generate_messages_eus std_msgs_generate_messages_eus)
endif()
if(TARGET geometry_msgs_generate_messages_eus)
  add_dependencies(yolo_detection_package_generate_messages_eus geometry_msgs_generate_messages_eus)
endif()

if(genlisp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/yolo_detection_package)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/yolo_detection_package
    DESTINATION ${genlisp_INSTALL_DIR}
  )
endif()
if(TARGET sensor_msgs_generate_messages_lisp)
  add_dependencies(yolo_detection_package_generate_messages_lisp sensor_msgs_generate_messages_lisp)
endif()
if(TARGET std_msgs_generate_messages_lisp)
  add_dependencies(yolo_detection_package_generate_messages_lisp std_msgs_generate_messages_lisp)
endif()
if(TARGET geometry_msgs_generate_messages_lisp)
  add_dependencies(yolo_detection_package_generate_messages_lisp geometry_msgs_generate_messages_lisp)
endif()

if(gennodejs_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/yolo_detection_package)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/yolo_detection_package
    DESTINATION ${gennodejs_INSTALL_DIR}
  )
endif()
if(TARGET sensor_msgs_generate_messages_nodejs)
  add_dependencies(yolo_detection_package_generate_messages_nodejs sensor_msgs_generate_messages_nodejs)
endif()
if(TARGET std_msgs_generate_messages_nodejs)
  add_dependencies(yolo_detection_package_generate_messages_nodejs std_msgs_generate_messages_nodejs)
endif()
if(TARGET geometry_msgs_generate_messages_nodejs)
  add_dependencies(yolo_detection_package_generate_messages_nodejs geometry_msgs_generate_messages_nodejs)
endif()

if(genpy_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/yolo_detection_package)
  install(CODE "execute_process(COMMAND \"/home/k325/miniconda3/envs/vln/bin/python3\" -m compileall \"${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/yolo_detection_package\")")
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/yolo_detection_package
    DESTINATION ${genpy_INSTALL_DIR}
  )
endif()
if(TARGET sensor_msgs_generate_messages_py)
  add_dependencies(yolo_detection_package_generate_messages_py sensor_msgs_generate_messages_py)
endif()
if(TARGET std_msgs_generate_messages_py)
  add_dependencies(yolo_detection_package_generate_messages_py std_msgs_generate_messages_py)
endif()
if(TARGET geometry_msgs_generate_messages_py)
  add_dependencies(yolo_detection_package_generate_messages_py geometry_msgs_generate_messages_py)
endif()
