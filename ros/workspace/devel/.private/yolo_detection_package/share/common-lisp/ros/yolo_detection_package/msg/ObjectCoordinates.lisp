; Auto-generated. Do not edit!


(cl:in-package yolo_detection_package-msg)


;//! \htmlinclude ObjectCoordinates.msg.html

(cl:defclass <ObjectCoordinates> (roslisp-msg-protocol:ros-message)
  ((header
    :reader header
    :initarg :header
    :type std_msgs-msg:Header
    :initform (cl:make-instance 'std_msgs-msg:Header))
   (objects
    :reader objects
    :initarg :objects
    :type (cl:vector yolo_detection_package-msg:ObjectCoordinate)
   :initform (cl:make-array 0 :element-type 'yolo_detection_package-msg:ObjectCoordinate :initial-element (cl:make-instance 'yolo_detection_package-msg:ObjectCoordinate))))
)

(cl:defclass ObjectCoordinates (<ObjectCoordinates>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <ObjectCoordinates>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'ObjectCoordinates)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name yolo_detection_package-msg:<ObjectCoordinates> is deprecated: use yolo_detection_package-msg:ObjectCoordinates instead.")))

(cl:ensure-generic-function 'header-val :lambda-list '(m))
(cl:defmethod header-val ((m <ObjectCoordinates>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader yolo_detection_package-msg:header-val is deprecated.  Use yolo_detection_package-msg:header instead.")
  (header m))

(cl:ensure-generic-function 'objects-val :lambda-list '(m))
(cl:defmethod objects-val ((m <ObjectCoordinates>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader yolo_detection_package-msg:objects-val is deprecated.  Use yolo_detection_package-msg:objects instead.")
  (objects m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <ObjectCoordinates>) ostream)
  "Serializes a message object of type '<ObjectCoordinates>"
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'header) ostream)
  (cl:let ((__ros_arr_len (cl:length (cl:slot-value msg 'objects))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_arr_len) ostream))
  (cl:map cl:nil #'(cl:lambda (ele) (roslisp-msg-protocol:serialize ele ostream))
   (cl:slot-value msg 'objects))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <ObjectCoordinates>) istream)
  "Deserializes a message object of type '<ObjectCoordinates>"
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'header) istream)
  (cl:let ((__ros_arr_len 0))
    (cl:setf (cl:ldb (cl:byte 8 0) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) __ros_arr_len) (cl:read-byte istream))
  (cl:setf (cl:slot-value msg 'objects) (cl:make-array __ros_arr_len))
  (cl:let ((vals (cl:slot-value msg 'objects)))
    (cl:dotimes (i __ros_arr_len)
    (cl:setf (cl:aref vals i) (cl:make-instance 'yolo_detection_package-msg:ObjectCoordinate))
  (roslisp-msg-protocol:deserialize (cl:aref vals i) istream))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<ObjectCoordinates>)))
  "Returns string type for a message object of type '<ObjectCoordinates>"
  "yolo_detection_package/ObjectCoordinates")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'ObjectCoordinates)))
  "Returns string type for a message object of type 'ObjectCoordinates"
  "yolo_detection_package/ObjectCoordinates")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<ObjectCoordinates>)))
  "Returns md5sum for a message object of type '<ObjectCoordinates>"
  "e0318b91e668fb7389ebc4d82bc5b870")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'ObjectCoordinates)))
  "Returns md5sum for a message object of type 'ObjectCoordinates"
  "e0318b91e668fb7389ebc4d82bc5b870")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<ObjectCoordinates>)))
  "Returns full string definition for message of type '<ObjectCoordinates>"
  (cl:format cl:nil "# msg/ObjectCoordinates.msg~%# 多物体的类别+坐标列表~%std_msgs/Header header  # 消息头（时间戳+坐标系）~%ObjectCoordinate[] objects  # 物体坐标列表~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%================================================================================~%MSG: yolo_detection_package/ObjectCoordinate~%# msg/ObjectCoordinate.msg~%# 单个物体的类别名称和绝对坐标~%string class_name       # 物体类别名称（如person/laptop/bottle）~%geometry_msgs/Point point  # 物体的绝对坐标（x/y/z）~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'ObjectCoordinates)))
  "Returns full string definition for message of type 'ObjectCoordinates"
  (cl:format cl:nil "# msg/ObjectCoordinates.msg~%# 多物体的类别+坐标列表~%std_msgs/Header header  # 消息头（时间戳+坐标系）~%ObjectCoordinate[] objects  # 物体坐标列表~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%================================================================================~%MSG: yolo_detection_package/ObjectCoordinate~%# msg/ObjectCoordinate.msg~%# 单个物体的类别名称和绝对坐标~%string class_name       # 物体类别名称（如person/laptop/bottle）~%geometry_msgs/Point point  # 物体的绝对坐标（x/y/z）~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <ObjectCoordinates>))
  (cl:+ 0
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'header))
     4 (cl:reduce #'cl:+ (cl:slot-value msg 'objects) :key #'(cl:lambda (ele) (cl:declare (cl:ignorable ele)) (cl:+ (roslisp-msg-protocol:serialization-length ele))))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <ObjectCoordinates>))
  "Converts a ROS message object to a list"
  (cl:list 'ObjectCoordinates
    (cl:cons ':header (header msg))
    (cl:cons ':objects (objects msg))
))
