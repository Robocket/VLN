;; Auto-generated. Do not edit!


(when (boundp 'yolo_detection_package::ObjectCoordinate)
  (if (not (find-package "YOLO_DETECTION_PACKAGE"))
    (make-package "YOLO_DETECTION_PACKAGE"))
  (shadow 'ObjectCoordinate (find-package "YOLO_DETECTION_PACKAGE")))
(unless (find-package "YOLO_DETECTION_PACKAGE::OBJECTCOORDINATE")
  (make-package "YOLO_DETECTION_PACKAGE::OBJECTCOORDINATE"))

(in-package "ROS")
;;//! \htmlinclude ObjectCoordinate.msg.html
(if (not (find-package "GEOMETRY_MSGS"))
  (ros::roseus-add-msgs "geometry_msgs"))


(defclass yolo_detection_package::ObjectCoordinate
  :super ros::object
  :slots (_class_name _point ))

(defmethod yolo_detection_package::ObjectCoordinate
  (:init
   (&key
    ((:class_name __class_name) "")
    ((:point __point) (instance geometry_msgs::Point :init))
    )
   (send-super :init)
   (setq _class_name (string __class_name))
   (setq _point __point)
   self)
  (:class_name
   (&optional __class_name)
   (if __class_name (setq _class_name __class_name)) _class_name)
  (:point
   (&rest __point)
   (if (keywordp (car __point))
       (send* _point __point)
     (progn
       (if __point (setq _point (car __point)))
       _point)))
  (:serialization-length
   ()
   (+
    ;; string _class_name
    4 (length _class_name)
    ;; geometry_msgs/Point _point
    (send _point :serialization-length)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; string _class_name
       (write-long (length _class_name) s) (princ _class_name s)
     ;; geometry_msgs/Point _point
       (send _point :serialize s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; string _class_name
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _class_name (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; geometry_msgs/Point _point
     (send _point :deserialize buf ptr-) (incf ptr- (send _point :serialization-length))
   ;;
   self)
  )

(setf (get yolo_detection_package::ObjectCoordinate :md5sum-) "4c88e551183bc43bf1db8b23e63043da")
(setf (get yolo_detection_package::ObjectCoordinate :datatype-) "yolo_detection_package/ObjectCoordinate")
(setf (get yolo_detection_package::ObjectCoordinate :definition-)
      "# msg/ObjectCoordinate.msg
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



(provide :yolo_detection_package/ObjectCoordinate "4c88e551183bc43bf1db8b23e63043da")


