; Auto-generated. Do not edit!


(cl:in-package VLN_planner-msg)


;//! \htmlinclude ObjectDetections.msg.html

(cl:defclass <ObjectDetections> (roslisp-msg-protocol:ros-message)
  ((header
    :reader header
    :initarg :header
    :type std_msgs-msg:Header
    :initform (cl:make-instance 'std_msgs-msg:Header))
   (objects
    :reader objects
    :initarg :objects
    :type (cl:vector VLN_planner-msg:ObjectDetection)
   :initform (cl:make-array 0 :element-type 'VLN_planner-msg:ObjectDetection :initial-element (cl:make-instance 'VLN_planner-msg:ObjectDetection))))
)

(cl:defclass ObjectDetections (<ObjectDetections>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <ObjectDetections>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'ObjectDetections)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name VLN_planner-msg:<ObjectDetections> is deprecated: use VLN_planner-msg:ObjectDetections instead.")))

(cl:ensure-generic-function 'header-val :lambda-list '(m))
(cl:defmethod header-val ((m <ObjectDetections>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader VLN_planner-msg:header-val is deprecated.  Use VLN_planner-msg:header instead.")
  (header m))

(cl:ensure-generic-function 'objects-val :lambda-list '(m))
(cl:defmethod objects-val ((m <ObjectDetections>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader VLN_planner-msg:objects-val is deprecated.  Use VLN_planner-msg:objects instead.")
  (objects m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <ObjectDetections>) ostream)
  "Serializes a message object of type '<ObjectDetections>"
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'header) ostream)
  (cl:let ((__ros_arr_len (cl:length (cl:slot-value msg 'objects))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_arr_len) ostream))
  (cl:map cl:nil #'(cl:lambda (ele) (roslisp-msg-protocol:serialize ele ostream))
   (cl:slot-value msg 'objects))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <ObjectDetections>) istream)
  "Deserializes a message object of type '<ObjectDetections>"
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'header) istream)
  (cl:let ((__ros_arr_len 0))
    (cl:setf (cl:ldb (cl:byte 8 0) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) __ros_arr_len) (cl:read-byte istream))
  (cl:setf (cl:slot-value msg 'objects) (cl:make-array __ros_arr_len))
  (cl:let ((vals (cl:slot-value msg 'objects)))
    (cl:dotimes (i __ros_arr_len)
    (cl:setf (cl:aref vals i) (cl:make-instance 'VLN_planner-msg:ObjectDetection))
  (roslisp-msg-protocol:deserialize (cl:aref vals i) istream))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<ObjectDetections>)))
  "Returns string type for a message object of type '<ObjectDetections>"
  "VLN_planner/ObjectDetections")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'ObjectDetections)))
  "Returns string type for a message object of type 'ObjectDetections"
  "VLN_planner/ObjectDetections")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<ObjectDetections>)))
  "Returns md5sum for a message object of type '<ObjectDetections>"
  "ce6350982d48c66f3e1a08ec1b02cb6f")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'ObjectDetections)))
  "Returns md5sum for a message object of type 'ObjectDetections"
  "ce6350982d48c66f3e1a08ec1b02cb6f")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<ObjectDetections>)))
  "Returns full string definition for message of type '<ObjectDetections>"
  (cl:format cl:nil "# ObjectDetections.msg~%Header header~%ObjectDetection[] objects~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%================================================================================~%MSG: VLN_planner/ObjectDetection~%string class_name~%float32 x_center #归一化~%float32 y_center~%float32 width~%float32 height~%float32 confidence~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'ObjectDetections)))
  "Returns full string definition for message of type 'ObjectDetections"
  (cl:format cl:nil "# ObjectDetections.msg~%Header header~%ObjectDetection[] objects~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%================================================================================~%MSG: VLN_planner/ObjectDetection~%string class_name~%float32 x_center #归一化~%float32 y_center~%float32 width~%float32 height~%float32 confidence~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <ObjectDetections>))
  (cl:+ 0
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'header))
     4 (cl:reduce #'cl:+ (cl:slot-value msg 'objects) :key #'(cl:lambda (ele) (cl:declare (cl:ignorable ele)) (cl:+ (roslisp-msg-protocol:serialization-length ele))))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <ObjectDetections>))
  "Converts a ROS message object to a list"
  (cl:list 'ObjectDetections
    (cl:cons ':header (header msg))
    (cl:cons ':objects (objects msg))
))
