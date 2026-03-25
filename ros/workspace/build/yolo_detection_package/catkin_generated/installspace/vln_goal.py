#!/usr/bin/env python3
# 结合ROS和LLM，解析自然语言指令选择目标物体并发布vln_goal
import rospy
import re
import math
from geometry_msgs.msg import PoseStamped
from yolo_detection_package.msg import ObjectCoordinate, ObjectCoordinates
from llama_cpp import Llama  # 导入llamacpp库

# -------------------------- 全局变量 --------------------------
object_coords_list = []  # 存储检测到的物体列表
has_received_coords = False
llm = None  # Llama实例
vln_goal_pub = None  # 全局发布者对象

# -------------------------- 1. 初始化llamacpp加载GGUF模型 --------------------------
def init_llm():
    """
    初始化llamacpp加载GGUF格式的Qwen3.5-4B模型
    负责解析自然语言指令，从物体列表中筛选目标
    """
    global llm
    try:
        rospy.loginfo("开始初始化LLM模型（llamacpp）...")
        model_path = "/home/k325/models/Qwen3.5-2B-GGUF/Qwen3.5-2B-Q4_K_M.gguf"
        
        # 初始化Llama实例
        llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=8,
            n_gpu_layers=20,
            verbose=False,
            rope_scaling={"type": "linear", "factor": 1.0},
            stop=["<|im_end|>", "</think>"]  # 关键修复：增加停止词
        )
        
        rospy.loginfo("✅ LLM模型（llamacpp）初始化成功！")
    except Exception as e:
        rospy.logerr(f"❌ LLM初始化失败：{e}")
        raise

# -------------------------- 2. ROS回调：接收物体坐标列表 --------------------------
def object_coords_callback(msg):
    """订阅/object/absolute_coords_list的回调函数"""
    global object_coords_list, has_received_coords
    object_coords_list = msg.objects
    has_received_coords = True

# -------------------------- 3. LLM解析指令：从物体列表选目标 --------------------------
def parse_goal_instruction(user_instruction):
    """
    让LLM解析自然语言指令，从物体列表中选择目标
    参数：user_instruction - 自然语言指令（如“选瓶子”“选最近的人”“选x坐标最大的物体”）
    返回：选中的ObjectCoordinate对象 | None
    """
    if llm is None:
        rospy.logerr("❌ LLM模型未初始化，无法解析指令！")
        return None
        
    if len(object_coords_list) == 0:
        rospy.logerr("❌ 无物体数据，无法解析指令！")
        return None
    
    # 构造物体列表描述
    objects_desc = []
    for idx, obj in enumerate(object_coords_list):
        distance = math.sqrt(obj.point.x**2 + obj.point.y**2 + obj.point.z**2)
        objects_desc.append(
            f"[{idx}] 类别：{obj.class_name}，坐标(x={obj.point.x:.2f}, y={obj.point.y:.2f}, z={obj.point.z:.2f})，距离原点：{distance:.2f}米"
        )
    objects_text = "\n".join(objects_desc)

    # 关键修复：强制禁止思考，只输出数字
    qwen_prompt = f"""<|im_start|>system
你是一个严格的目标选择器。
规则：
1. 只输出一个数字索引，例如：0
2. 绝对不输出任何文字、不解释、不思考、不输出标签
3. 直接输出数字，不要任何多余内容

物体列表：
{objects_text}<|im_end|>
<|im_start|>user
{user_instruction}<|im_end|>
<|im_start|>assistant
"""

    # LLM推理
    try:
        print(f"物体列表：\n{objects_text}")
        result = llm.create_completion(
            prompt=qwen_prompt,
            max_tokens=1024,
            temperature=0.7,    # 完全确定性输出
            stream=False,
            # stop=["<|im_end|>", ""]
        )

        generated_text = result["choices"][0]["text"].strip()
        print(f"LLM输出：{generated_text}")

        # 提取数字
        idx_match = re.search(r"\d+", generated_text)
        if not idx_match:
            rospy.logerr(f"❌ LLM解析失败，输出：{generated_text}")
            return None
        target_idx = int(idx_match.group())
        
        # 校验索引
        if 0 <= target_idx < len(object_coords_list):
            selected_obj = object_coords_list[target_idx]
            rospy.loginfo(f"\n✅ LLM选中目标：[{target_idx}] {selected_obj.class_name}")
            return selected_obj
        else:
            rospy.logerr(f"❌ 索引{target_idx}超出范围！")
            return None
    except Exception as e:
        rospy.logerr(f"❌ 解析指令失败：{e}")
        return None

# -------------------------- 4. 发布vln_goal话题 --------------------------
def publish_vln_goal(selected_obj):
    """将选中的物体坐标发布为vln_goal"""
    if vln_goal_pub is None:
        rospy.logerr("❌ 发布者未初始化！")
        return

    goal_msg = PoseStamped()
    goal_msg.header.frame_id = "world"
    goal_msg.header.stamp = rospy.Time.now()
    goal_msg.pose.position.x = selected_obj.point.x
    goal_msg.pose.position.y = selected_obj.point.y
    goal_msg.pose.position.z = 0.0
    goal_msg.pose.orientation.w = 0.7071
    goal_msg.pose.orientation.z = 0.7071

    vln_goal_pub.publish(goal_msg)
    rospy.loginfo("\n📤 成功发布vln_goal话题！")

# -------------------------- 5. 主流程 --------------------------
def main():
    rospy.init_node('llm_goal_selector', anonymous=True)
    
    global vln_goal_pub
    vln_goal_pub = rospy.Publisher('vln_goal', PoseStamped, queue_size=10)
    
    init_llm()
    
    rospy.Subscriber('/object/absolute_coords_list', ObjectCoordinates, object_coords_callback)
    rospy.loginfo("🔍 已订阅/object/absolute_coords_list话题，等待接收物体数据...")
    
    # 等待物体数据
    timeout = 15
    start_time = rospy.Time.now()
    while not has_received_coords and (rospy.Time.now() - start_time).to_sec() < timeout:
        rospy.sleep(0.1)
    
    if not has_received_coords:
        rospy.logerr(f"❌ 等待{timeout}秒未收到物体数据，程序退出！")
        return
    
    print("\n=====================================")
    print("请输入目标选择指令：")
    user_instruction = input("> ").strip()
    
    selected_obj = parse_goal_instruction(user_instruction)
    if not selected_obj:
        return
    
    publish_vln_goal(selected_obj)
    rospy.spin()

if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        rospy.logwarn("⚠️ 节点被中断！")
    except KeyboardInterrupt:
        rospy.logwarn("⚠️ 用户手动终止程序！")
    except Exception as e:
        rospy.logerr(f"❌ 程序异常：{e}")
