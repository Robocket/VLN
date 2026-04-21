
(cl:in-package :asdf)

(defsystem "vln_planner-msg"
  :depends-on (:roslisp-msg-protocol :roslisp-utils :geometry_msgs-msg
               :std_msgs-msg
)
  :components ((:file "_package")
    (:file "ObjectCoordinate" :depends-on ("_package_ObjectCoordinate"))
    (:file "_package_ObjectCoordinate" :depends-on ("_package"))
    (:file "ObjectCoordinates" :depends-on ("_package_ObjectCoordinates"))
    (:file "_package_ObjectCoordinates" :depends-on ("_package"))
    (:file "ObjectDetection" :depends-on ("_package_ObjectDetection"))
    (:file "_package_ObjectDetection" :depends-on ("_package"))
    (:file "ObjectDetections" :depends-on ("_package_ObjectDetections"))
    (:file "_package_ObjectDetections" :depends-on ("_package"))
  ))