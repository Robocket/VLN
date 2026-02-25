; Auto-generated. Do not edit!


(cl:in-package yolo_detection_package-msg)


;//! \htmlinclude ObjectCoordinate.msg.html

(cl:defclass <ObjectCoordinate> (roslisp-msg-protocol:ros-message)
  ((class_name
    :reader class_name
    :initarg :class_name
    :type cl:string
    :initform "")
   (point
    :reader point
    :initarg :point
    :type geometry_msgs-msg:Point
    :initform (cl:make-instance 'geometry_msgs-msg:Point)))
)

(cl:defclass ObjectCoordinate (<ObjectCoordinate>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <ObjectCoordinate>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'ObjectCoordinate)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name yolo_detection_package-msg:<ObjectCoordinate> is deprecated: use yolo_detection_package-msg:ObjectCoordinate instead.")))

(cl:ensure-generic-function 'class_name-val :lambda-list '(m))
(cl:defmethod class_name-val ((m <ObjectCoordinate>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader yolo_detection_package-msg:class_name-val is deprecated.  Use yolo_detection_package-msg:class_name instead.")
  (class_name m))

(cl:ensure-generic-function 'point-val :lambda-list '(m))
(cl:defmethod point-val ((m <ObjectCoordinate>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader yolo_detection_package-msg:point-val is deprecated.  Use yolo_detection_package-msg:point instead.")
  (point m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <ObjectCoordinate>) ostream)
  "Serializes a message object of type '<ObjectCoordinate>"
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'class_name))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'class_name))
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'point) ostream)
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <ObjectCoordinate>) istream)
  "Deserializes a message object of type '<ObjectCoordinate>"
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'class_name) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'class_name) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'point) istream)
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<ObjectCoordinate>)))
  "Returns string type for a message object of type '<ObjectCoordinate>"
  "yolo_detection_package/ObjectCoordinate")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'ObjectCoordinate)))
  "Returns string type for a message object of type 'ObjectCoordinate"
  "yolo_detection_package/ObjectCoordinate")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<ObjectCoordinate>)))
  "Returns md5sum for a message object of type '<ObjectCoordinate>"
  "4c88e551183bc43bf1db8b23e63043da")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'ObjectCoordinate)))
  "Returns md5sum for a message object of type 'ObjectCoordinate"
  "4c88e551183bc43bf1db8b23e63043da")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<ObjectCoordinate>)))
  "Returns full string definition for message of type '<ObjectCoordinate>"
  (cl:format cl:nil "# msg/ObjectCoordinate.msg~%# 单个物体的类别名称和绝对坐标~%string class_name       # 物体类别名称（如person/laptop/bottle）~%geometry_msgs/Point point  # 物体的绝对坐标（x/y/z）~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'ObjectCoordinate)))
  "Returns full string definition for message of type 'ObjectCoordinate"
  (cl:format cl:nil "# msg/ObjectCoordinate.msg~%# 单个物体的类别名称和绝对坐标~%string class_name       # 物体类别名称（如person/laptop/bottle）~%geometry_msgs/Point point  # 物体的绝对坐标（x/y/z）~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <ObjectCoordinate>))
  (cl:+ 0
     4 (cl:length (cl:slot-value msg 'class_name))
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'point))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <ObjectCoordinate>))
  "Converts a ROS message object to a list"
  (cl:list 'ObjectCoordinate
    (cl:cons ':class_name (class_name msg))
    (cl:cons ':point (point msg))
))
