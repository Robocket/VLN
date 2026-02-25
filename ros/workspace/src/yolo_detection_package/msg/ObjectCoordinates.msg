# msg/ObjectCoordinates.msg
# 多物体的类别+坐标列表
std_msgs/Header header  # 消息头（时间戳+坐标系）
ObjectCoordinate[] objects  # 物体坐标列表
