;; Auto-generated. Do not edit!


(when (boundp 'yolo_detection_package::ObjectDetections)
  (if (not (find-package "YOLO_DETECTION_PACKAGE"))
    (make-package "YOLO_DETECTION_PACKAGE"))
  (shadow 'ObjectDetections (find-package "YOLO_DETECTION_PACKAGE")))
(unless (find-package "YOLO_DETECTION_PACKAGE::OBJECTDETECTIONS")
  (make-package "YOLO_DETECTION_PACKAGE::OBJECTDETECTIONS"))

(in-package "ROS")
;;//! \htmlinclude ObjectDetections.msg.html
(if (not (find-package "STD_MSGS"))
  (ros::roseus-add-msgs "std_msgs"))


(defclass yolo_detection_package::ObjectDetections
  :super ros::object
  :slots (_header _objects ))

(defmethod yolo_detection_package::ObjectDetections
  (:init
   (&key
    ((:header __header) (instance std_msgs::Header :init))
    ((:objects __objects) ())
    )
   (send-super :init)
   (setq _header __header)
   (setq _objects __objects)
   self)
  (:header
   (&rest __header)
   (if (keywordp (car __header))
       (send* _header __header)
     (progn
       (if __header (setq _header (car __header)))
       _header)))
  (:objects
   (&rest __objects)
   (if (keywordp (car __objects))
       (send* _objects __objects)
     (progn
       (if __objects (setq _objects (car __objects)))
       _objects)))
  (:serialization-length
   ()
   (+
    ;; std_msgs/Header _header
    (send _header :serialization-length)
    ;; yolo_detection_package/ObjectDetection[] _objects
    (apply #'+ (send-all _objects :serialization-length)) 4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; std_msgs/Header _header
       (send _header :serialize s)
     ;; yolo_detection_package/ObjectDetection[] _objects
     (write-long (length _objects) s)
     (dolist (elem _objects)
       (send elem :serialize s)
       )
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; std_msgs/Header _header
     (send _header :deserialize buf ptr-) (incf ptr- (send _header :serialization-length))
   ;; yolo_detection_package/ObjectDetection[] _objects
   (let (n)
     (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4)
     (setq _objects (let (r) (dotimes (i n) (push (instance yolo_detection_package::ObjectDetection :init) r)) r))
     (dolist (elem- _objects)
     (send elem- :deserialize buf ptr-) (incf ptr- (send elem- :serialization-length))
     ))
   ;;
   self)
  )

(setf (get yolo_detection_package::ObjectDetections :md5sum-) "ce6350982d48c66f3e1a08ec1b02cb6f")
(setf (get yolo_detection_package::ObjectDetections :datatype-) "yolo_detection_package/ObjectDetections")
(setf (get yolo_detection_package::ObjectDetections :definition-)
      "# ObjectDetections.msg
Header header
ObjectDetection[] objects
================================================================================
MSG: std_msgs/Header
# Standard metadata for higher-level stamped data types.
# This is generally used to communicate timestamped data 
# in a particular coordinate frame.
# 
# sequence ID: consecutively increasing ID 
uint32 seq
#Two-integer timestamp that is expressed as:
# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')
# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')
# time-handling sugar is provided by the client library
time stamp
#Frame this data is associated with
string frame_id

================================================================================
MSG: yolo_detection_package/ObjectDetection
string class_name
float32 x_center #归一化
float32 y_center
float32 width
float32 height
float32 confidence
")



(provide :yolo_detection_package/ObjectDetections "ce6350982d48c66f3e1a08ec1b02cb6f")


