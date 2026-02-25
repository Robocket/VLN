; Auto-generated. Do not edit!


(cl:in-package yolo_detection_package-msg)


;//! \htmlinclude ObjectDetection.msg.html

(cl:defclass <ObjectDetection> (roslisp-msg-protocol:ros-message)
  ((class_name
    :reader class_name
    :initarg :class_name
    :type cl:string
    :initform "")
   (x_center
    :reader x_center
    :initarg :x_center
    :type cl:float
    :initform 0.0)
   (y_center
    :reader y_center
    :initarg :y_center
    :type cl:float
    :initform 0.0)
   (width
    :reader width
    :initarg :width
    :type cl:float
    :initform 0.0)
   (height
    :reader height
    :initarg :height
    :type cl:float
    :initform 0.0)
   (confidence
    :reader confidence
    :initarg :confidence
    :type cl:float
    :initform 0.0))
)

(cl:defclass ObjectDetection (<ObjectDetection>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <ObjectDetection>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'ObjectDetection)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name yolo_detection_package-msg:<ObjectDetection> is deprecated: use yolo_detection_package-msg:ObjectDetection instead.")))

(cl:ensure-generic-function 'class_name-val :lambda-list '(m))
(cl:defmethod class_name-val ((m <ObjectDetection>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader yolo_detection_package-msg:class_name-val is deprecated.  Use yolo_detection_package-msg:class_name instead.")
  (class_name m))

(cl:ensure-generic-function 'x_center-val :lambda-list '(m))
(cl:defmethod x_center-val ((m <ObjectDetection>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader yolo_detection_package-msg:x_center-val is deprecated.  Use yolo_detection_package-msg:x_center instead.")
  (x_center m))

(cl:ensure-generic-function 'y_center-val :lambda-list '(m))
(cl:defmethod y_center-val ((m <ObjectDetection>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader yolo_detection_package-msg:y_center-val is deprecated.  Use yolo_detection_package-msg:y_center instead.")
  (y_center m))

(cl:ensure-generic-function 'width-val :lambda-list '(m))
(cl:defmethod width-val ((m <ObjectDetection>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader yolo_detection_package-msg:width-val is deprecated.  Use yolo_detection_package-msg:width instead.")
  (width m))

(cl:ensure-generic-function 'height-val :lambda-list '(m))
(cl:defmethod height-val ((m <ObjectDetection>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader yolo_detection_package-msg:height-val is deprecated.  Use yolo_detection_package-msg:height instead.")
  (height m))

(cl:ensure-generic-function 'confidence-val :lambda-list '(m))
(cl:defmethod confidence-val ((m <ObjectDetection>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader yolo_detection_package-msg:confidence-val is deprecated.  Use yolo_detection_package-msg:confidence instead.")
  (confidence m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <ObjectDetection>) ostream)
  "Serializes a message object of type '<ObjectDetection>"
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'class_name))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'class_name))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'x_center))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'y_center))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'width))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'height))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'confidence))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <ObjectDetection>) istream)
  "Deserializes a message object of type '<ObjectDetection>"
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'class_name) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'class_name) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'x_center) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'y_center) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'width) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'height) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'confidence) (roslisp-utils:decode-single-float-bits bits)))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<ObjectDetection>)))
  "Returns string type for a message object of type '<ObjectDetection>"
  "yolo_detection_package/ObjectDetection")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'ObjectDetection)))
  "Returns string type for a message object of type 'ObjectDetection"
  "yolo_detection_package/ObjectDetection")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<ObjectDetection>)))
  "Returns md5sum for a message object of type '<ObjectDetection>"
  "c42afd1b09ce5e8fc8ab40cda3991fcf")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'ObjectDetection)))
  "Returns md5sum for a message object of type 'ObjectDetection"
  "c42afd1b09ce5e8fc8ab40cda3991fcf")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<ObjectDetection>)))
  "Returns full string definition for message of type '<ObjectDetection>"
  (cl:format cl:nil "string class_name~%float32 x_center #归一化~%float32 y_center~%float32 width~%float32 height~%float32 confidence~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'ObjectDetection)))
  "Returns full string definition for message of type 'ObjectDetection"
  (cl:format cl:nil "string class_name~%float32 x_center #归一化~%float32 y_center~%float32 width~%float32 height~%float32 confidence~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <ObjectDetection>))
  (cl:+ 0
     4 (cl:length (cl:slot-value msg 'class_name))
     4
     4
     4
     4
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <ObjectDetection>))
  "Converts a ROS message object to a list"
  (cl:list 'ObjectDetection
    (cl:cons ':class_name (class_name msg))
    (cl:cons ':x_center (x_center msg))
    (cl:cons ':y_center (y_center msg))
    (cl:cons ':width (width msg))
    (cl:cons ':height (height msg))
    (cl:cons ':confidence (confidence msg))
))
