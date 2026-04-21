#!/usr/bin/env python3
#rosrun your_package your_script.py _use_subscriber:=true
import rospy
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point, Quaternion
from vln_planner.msg import ObjectCoordinate, ObjectCoordinates

# 静态物体列表（模式1使用）
OBJECTS = [
    ("laptop", 1.891, 1.662, 0.339),
    ("mouse", 5.069, -5.161, 0.393),
    ("keyboard", 2.898, -2.052, 0.068),
    ("bottle", 9.419, 2.811, 1.005),
    ("chair", 3.261, 1.367, 0.378),
    ("cell phone", 4.366, -6.735, 0.614),
    ("refrigerator", 3.730, -0.991, 0.765),
    ("backpack", 0.925, -1.549, -0.803)
]

class ObjectMarkerPublisher:
    def __init__(self):
        rospy.init_node('object_marker_publisher')
        
        # 参数：是否使用订阅模式（默认false=静态模式）
        self.use_subscriber = rospy.get_param('~use_subscriber', True)
        
        # 发布器
        self.pub = rospy.Publisher('/object/markers', MarkerArray, queue_size=10)
        
        if self.use_subscriber:
            # 模式2：订阅自定义话题 ObjectList
            self.sub = rospy.Subscriber('/object/absolute_coords_list', ObjectCoordinates, self.callback)
            rospy.loginfo("Subscribing to /object/absolute_coords_list (ObjectCoordinates)...")
            rospy.spin()
        else:
            # 模式1：静态发布模式
            self.publish_static()

    def create_markers_from_list(self, object_list):
        """通用：从物体列表生成MarkerArray"""
        marker_array = MarkerArray()
        for idx, (name, x, y, z) in enumerate(object_list):
            # 1. 球体标记
            sphere_marker = Marker()
            sphere_marker.header.frame_id = "world"
            sphere_marker.header.stamp = rospy.Time.now()
            sphere_marker.id = idx
            sphere_marker.type = Marker.SPHERE
            sphere_marker.action = Marker.ADD
            sphere_marker.pose.position = Point(x, y, z)
            sphere_marker.pose.orientation = Quaternion(0, 0, 0, 1)
            sphere_marker.scale.x = sphere_marker.scale.y = sphere_marker.scale.z = 0.3
            sphere_marker.color.r = 1.0
            sphere_marker.color.a = 1.0

            # 2. 文字标记
            text_marker = Marker()
            text_marker.header.frame_id = "world"
            text_marker.header.stamp = rospy.Time.now()
            text_marker.id = idx + 1000
            text_marker.type = Marker.TEXT_VIEW_FACING
            text_marker.action = Marker.ADD
            text_marker.pose.position = Point(x, y + 0.5, z)
            text_marker.pose.orientation = Quaternion(0, 0, 0, 1)
            text_marker.text = name
            text_marker.scale.z = 0.5
            text_marker.color.r = text_marker.color.g = text_marker.color.b = text_marker.color.a = 1.0

            marker_array.markers.append(sphere_marker)
            marker_array.markers.append(text_marker)
        return marker_array

    def publish_static(self):
        """静态模式：发布预设OBJECTS"""
        rospy.loginfo("Publishing static objects...")
        rate = rospy.Rate(10)
        while not rospy.is_shutdown():
            marker_array = self.create_markers_from_list(OBJECTS)
            self.pub.publish(marker_array)
            rate.sleep()

    def callback(self, msg):
        """订阅模式回调：解析ObjectList消息"""
        object_list = []
        for obj in msg.objects:
            object_list.append((
                obj.class_name,
                obj.point.x,
                obj.point.y,
                obj.point.z
            ))
        
        marker_array = self.create_markers_from_list(object_list)
        self.pub.publish(marker_array)

if __name__ == '__main__':
    try:
        ObjectMarkerPublisher()
    except rospy.ROSInterruptException:
        pass
