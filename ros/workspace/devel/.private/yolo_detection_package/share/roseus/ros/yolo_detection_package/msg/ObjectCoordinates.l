;; Auto-generated. Do not edit!


(when (boundp 'yolo_detection_package::ObjectCoordinates)
  (if (not (find-package "YOLO_DETECTION_PACKAGE"))
    (make-package "YOLO_DETECTION_PACKAGE"))
  (shadow 'ObjectCoordinates (find-package "YOLO_DETECTION_PACKAGE")))
(unless (find-package "YOLO_DETECTION_PACKAGE::OBJECTCOORDINATES")
  (make-package "YOLO_DETECTION_PACKAGE::OBJECTCOORDINATES"))

(in-package "ROS")
;;//! \htmlinclude ObjectCoordinates.msg.html
(if (not (find-package "STD_MSGS"))
  (ros::roseus-add-msgs "std_msgs"))


(defclass yolo_detection_package::ObjectCoordinates
  :super ros::object
  :slots (_header _objects ))

(defmethod yolo_detection_package::ObjectCoordinates
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
    ;; yolo_detection_package/ObjectCoordinate[] _objects
    (apply #'+ (send-all _objects :serialization-length)) 4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; std_msgs/Header _header
       (send _header :serialize s)
     ;; yolo_detection_package/ObjectCoordinate[] _objects
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
   ;; yolo_detection_package/ObjectCoordinate[] _objects
   (let (n)
     (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4)
     (setq _objects (let (r) (dotimes (i n) (push (instance yolo_detection_package::ObjectCoordinate :init) r)) r))
     (dolist (elem- _objects)
     (send elem- :deserialize buf ptr-) (incf ptr- (send elem- :serialization-length))
     ))
   ;;
   self)
  )

(setf (get yolo_detection_package::ObjectCoordinates :md5sum-) "e0318b91e668fb7389ebc4d82bc5b870")
(setf (get yolo_detection_package::ObjectCoordinates :datatype-) "yolo_detection_package/ObjectCoordinates")
(setf (get yolo_detection_package::ObjectCoordinates :definition-)
      "# msg/ObjectCoordinates.msg
# 多物体的类别+坐标列表
std_msgs/Header header  # 消息头（时间戳+坐标系）
ObjectCoordinate[] objects  # 物体坐标列表

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
MSG: yolo_detection_package/ObjectCoordinate
# msg/ObjectCoordinate.msg
# 单个物体的类别名称和绝对坐标
string class_name       # 物体类别名称（如person/laptop/bottle）
geometry_msgs/Point point  # 物体的绝对坐标（x/y/z）

================================================================================
MSG: geometry_msgs/Point
# This contains the position of a point in free space
float64 x
float64 y
float64 z

")



(provide :yolo_detection_package/ObjectCoordinates "e0318b91e668fb7389ebc4d82bc5b870")


