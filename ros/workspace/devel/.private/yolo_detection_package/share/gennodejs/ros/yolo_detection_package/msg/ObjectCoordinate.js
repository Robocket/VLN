// Auto-generated. Do not edit!

// (in-package yolo_detection_package.msg)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;
let geometry_msgs = _finder('geometry_msgs');

//-----------------------------------------------------------

class ObjectCoordinate {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.class_name = null;
      this.point = null;
    }
    else {
      if (initObj.hasOwnProperty('class_name')) {
        this.class_name = initObj.class_name
      }
      else {
        this.class_name = '';
      }
      if (initObj.hasOwnProperty('point')) {
        this.point = initObj.point
      }
      else {
        this.point = new geometry_msgs.msg.Point();
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type ObjectCoordinate
    // Serialize message field [class_name]
    bufferOffset = _serializer.string(obj.class_name, buffer, bufferOffset);
    // Serialize message field [point]
    bufferOffset = geometry_msgs.msg.Point.serialize(obj.point, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type ObjectCoordinate
    let len;
    let data = new ObjectCoordinate(null);
    // Deserialize message field [class_name]
    data.class_name = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [point]
    data.point = geometry_msgs.msg.Point.deserialize(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += _getByteLength(object.class_name);
    return length + 28;
  }

  static datatype() {
    // Returns string type for a message object
    return 'yolo_detection_package/ObjectCoordinate';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '4c88e551183bc43bf1db8b23e63043da';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
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
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new ObjectCoordinate(null);
    if (msg.class_name !== undefined) {
      resolved.class_name = msg.class_name;
    }
    else {
      resolved.class_name = ''
    }

    if (msg.point !== undefined) {
      resolved.point = geometry_msgs.msg.Point.Resolve(msg.point)
    }
    else {
      resolved.point = new geometry_msgs.msg.Point()
    }

    return resolved;
    }
};

module.exports = ObjectCoordinate;
