;; Auto-generated. Do not edit!


(when (boundp 'yolo_detection_package::ObjectDetection)
  (if (not (find-package "YOLO_DETECTION_PACKAGE"))
    (make-package "YOLO_DETECTION_PACKAGE"))
  (shadow 'ObjectDetection (find-package "YOLO_DETECTION_PACKAGE")))
(unless (find-package "YOLO_DETECTION_PACKAGE::OBJECTDETECTION")
  (make-package "YOLO_DETECTION_PACKAGE::OBJECTDETECTION"))

(in-package "ROS")
;;//! \htmlinclude ObjectDetection.msg.html


(defclass yolo_detection_package::ObjectDetection
  :super ros::object
  :slots (_class_name _x_center _y_center _width _height _confidence ))

(defmethod yolo_detection_package::ObjectDetection
  (:init
   (&key
    ((:class_name __class_name) "")
    ((:x_center __x_center) 0.0)
    ((:y_center __y_center) 0.0)
    ((:width __width) 0.0)
    ((:height __height) 0.0)
    ((:confidence __confidence) 0.0)
    )
   (send-super :init)
   (setq _class_name (string __class_name))
   (setq _x_center (float __x_center))
   (setq _y_center (float __y_center))
   (setq _width (float __width))
   (setq _height (float __height))
   (setq _confidence (float __confidence))
   self)
  (:class_name
   (&optional __class_name)
   (if __class_name (setq _class_name __class_name)) _class_name)
  (:x_center
   (&optional __x_center)
   (if __x_center (setq _x_center __x_center)) _x_center)
  (:y_center
   (&optional __y_center)
   (if __y_center (setq _y_center __y_center)) _y_center)
  (:width
   (&optional __width)
   (if __width (setq _width __width)) _width)
  (:height
   (&optional __height)
   (if __height (setq _height __height)) _height)
  (:confidence
   (&optional __confidence)
   (if __confidence (setq _confidence __confidence)) _confidence)
  (:serialization-length
   ()
   (+
    ;; string _class_name
    4 (length _class_name)
    ;; float32 _x_center
    4
    ;; float32 _y_center
    4
    ;; float32 _width
    4
    ;; float32 _height
    4
    ;; float32 _confidence
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; string _class_name
       (write-long (length _class_name) s) (princ _class_name s)
     ;; float32 _x_center
       (sys::poke _x_center (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _y_center
       (sys::poke _y_center (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _width
       (sys::poke _width (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _height
       (sys::poke _height (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _confidence
       (sys::poke _confidence (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; string _class_name
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _class_name (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; float32 _x_center
     (setq _x_center (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _y_center
     (setq _y_center (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _width
     (setq _width (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _height
     (setq _height (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _confidence
     (setq _confidence (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;;
   self)
  )

(setf (get yolo_detection_package::ObjectDetection :md5sum-) "c42afd1b09ce5e8fc8ab40cda3991fcf")
(setf (get yolo_detection_package::ObjectDetection :datatype-) "yolo_detection_package/ObjectDetection")
(setf (get yolo_detection_package::ObjectDetection :definition-)
      "string class_name
float32 x_center #归一化
float32 y_center
float32 width
float32 height
float32 confidence
")



(provide :yolo_detection_package/ObjectDetection "c42afd1b09ce5e8fc8ab40cda3991fcf")


