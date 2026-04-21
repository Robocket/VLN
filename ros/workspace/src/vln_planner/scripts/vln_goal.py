#!/usr/bin/env python
# 结合ROS和LLM，解析自然语言指令选择目标物体并发布vln_goal
import rospy
import re
import math
import signal
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from vln_planner.msg import ObjectCoordinate, ObjectCoordinates
from llama_cpp import Llama  # 导入llamacpp库

# -------------------------- 全局变量 --------------------------
object_coords_list = []  # 存储检测到的物体列表
has_received_coords = False
robot_position = None  # 当前机器人坐标
has_received_odom = False
llm = None  # Llama实例
vln_goal_pub = None  # 全局发布者对象
shutdown_requested = False  # 是否请求退出

# -------------------------- 1. 初始化llamacpp加载GGUF模型 --------------------------
def init_llm():
    """
    初始化llamacpp加载GGUF格式的Qwen3.5-2B模型
    负责解析自然语言指令，从物体列表中筛选目标
    """
    global llm
    try:
        rospy.loginfo("开始初始化LLM模型（llamacpp）...")
        model_path = "/home/k325/models/Qwen3.5-9B-GGUF/Qwen3.5-9B-Q4_0.gguf"
        # model_path = "/home/k325/models/Qwen3.5-2B-GGUF/Qwen3.5-2B-Q4_K_M.gguf"
        # 初始化Llama实例
        llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=16,
            # n_gpu_layers=35,
            n_gpu_layers=-1,  # 全部使用GPU推理
            verbose=False,
            # verbose=True,
            rope_scaling={"type": "linear", "factor": 1.0},
            stop=["<|im_end|>", "</tool_call>"]  
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


def odom_callback(msg):
    """订阅/Odometry的回调函数，用于更新机器人自身坐标"""
    global robot_position, has_received_odom
    try:
        robot_position = (
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            msg.pose.pose.position.z
        )
        has_received_odom = True
        rospy.logdebug(f"已更新机器人坐标: {robot_position}")
    except Exception as e:
        rospy.logerr(f"❌ 解析里程计失败：{e}")

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
    if robot_position is not None:
        robot_desc = f"机器人当前坐标(x={robot_position[0]:.2f}, y={robot_position[1]:.2f}, z={robot_position[2]:.2f})"
    else:
        robot_desc = "机器人当前坐标未知，使用世界坐标系原点作为参考。"

    for idx, obj in enumerate(object_coords_list):
        if robot_position is not None:
            dx = obj.point.x - robot_position[0]
            dy = obj.point.y - robot_position[1]
            dz = obj.point.z - robot_position[2]
            distance = math.sqrt(dx*dx + dy*dy + dz*dz)
            distance_label = f"距离机器人：{distance:.2f}米"
        else:
            distance = math.sqrt(obj.point.x**2 + obj.point.y**2 + obj.point.z**2)
            distance_label = f"距离原点：{distance:.2f}米"

        objects_desc.append(
            f"[{idx}] 类别：{obj.class_name}，坐标(x={obj.point.x:.2f}, y={obj.point.y:.2f}, z={obj.point.z:.2f})，{distance_label}"
        )
    objects_text = "\n".join(objects_desc)

    # 关键修复：强制禁止思考，只输出数字
    qwen_prompt = f"""<|im_start|>system
你是一个严格的目标选择器。
规则：
1. 只输出一个数字索引，例如：0
2. 绝对不输出任何文字、不解释、不思考、不输出标签
3. 直接输出数字，不要任何多余内容

{robot_desc}

物体列表：
{objects_text}

请根据机器人当前位置和物体列表，选择一个最合适的目标。
{user_instruction}<|im_end|>
<|im_start|>assistant
"""

    # LLM推理
    try:
        print(f"物体列表：\n{objects_text}")
        result = llm.create_completion(
            prompt=qwen_prompt,
            max_tokens=1024,
            temperature=0.2,    # 完全确定性输出
            stream=False,
            # stop=["<|im_end|>", ""]
        )

        generated_text = result["choices"][0]["text"].strip()
        print(f"LLM输出：{generated_text}")

        # 提取数字
        idx_matches = re.findall(r"\d+", generated_text)  # 提取所有数字
        if not idx_matches:
            rospy.logerr(f"❌ LLM解析失败，输出：{generated_text}")
            return None
        target_idx = int(idx_matches[-1])  # 取最后一个数字（正确答案）
        
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
    goal_msg.pose.position.z = 1  # 固定高度，适合地面机器人
    goal_msg.pose.orientation.w = 0.7071
    goal_msg.pose.orientation.z = 0.7071

    vln_goal_pub.publish(goal_msg)
    rospy.loginfo("\n📤 成功发布vln_goal话题！")


def cleanup():
    """释放程序使用的外部资源。"""
    global llm
    rospy.loginfo("🔒 正在释放资源...")
    import threading
    def close_llm_with_timeout(llm_obj, timeout=3):
        if hasattr(llm_obj, 'close'):
            done = [False]
            def target():
                try:
                    llm_obj.close()
                except Exception:
                    pass
                done[0] = True
            t = threading.Thread(target=target)
            t.start()
            t.join(timeout)
            if not done[0]:
                rospy.logwarn("⚠️ LLM关闭超时，已跳过。")
            else:
                rospy.loginfo("✅ 已关闭LLM模型。")

    try:
        if llm is not None:
            close_llm_with_timeout(llm, timeout=3)
            llm = None
    except Exception as e:
        rospy.logwarn(f"⚠️ 释放LLM资源时出现错误：{e}")
    rospy.loginfo("✅ 资源释放完成。")


# -------------------------- 5. 主流程 --------------------------
def handle_sigint(signum, frame):
    global shutdown_requested
    shutdown_requested = True
    rospy.logwarn("⚠️ 收到中断信号，正在关闭节点...")
    try:
        rospy.signal_shutdown('SIGINT')
    except Exception:
        pass


def main():
    rospy.init_node('llm_goal_selector', anonymous=True, disable_signals=True)
    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)
    
    global vln_goal_pub
    vln_goal_pub = rospy.Publisher('vln_goal', PoseStamped, queue_size=10)
    
    init_llm()
    
    rospy.Subscriber('/object/absolute_coords_list', ObjectCoordinates, object_coords_callback)
    rospy.Subscriber('/Odometry', Odometry, odom_callback)
    rospy.loginfo("🔍 已订阅/object/absolute_coords_list 和 /Odometry 话题，等待接收数据...")
    
    # 等待物体数据
    timeout = 15
    start_time = rospy.Time.now()
    sleep_interval = 0.02  # 更短的sleep间隔
    while not has_received_coords and not shutdown_requested and (rospy.Time.now() - start_time).to_sec() < timeout:
        rospy.sleep(sleep_interval)
        if shutdown_requested:
            break

    if shutdown_requested:
        rospy.logwarn("⚠️ 中断请求已收到，退出程序。")
        cleanup()
        return

    if not has_received_coords:
        rospy.logerr(f"❌ 等待{timeout}秒未收到物体数据，程序退出！")
        cleanup()
        return

    if not has_received_odom:
        rospy.logwarn("⚠️ 未收到里程计数据，将继续运行，但无法使用机器人当前位置做更精确判断。")

    print("\n=====================================")
    print("输入目标选择指令，输入 quit / q / exit 退出。")
    print("> ", end="", flush=True)

    while not rospy.is_shutdown() and not shutdown_requested:
        try:
            # 检查shutdown_requested，避免input阻塞
            import select, sys
            ready, _, _ = select.select([sys.stdin], [], [], 0.2)
            if shutdown_requested:
                break
            if ready:
                user_instruction = sys.stdin.readline().strip()
            else:
                continue
        except (EOFError, KeyboardInterrupt):
            rospy.loginfo("⚠️ 终止输入，退出程序。")
            break

        if not user_instruction:
            continue

        if user_instruction.lower() in ['q', 'quit', 'exit', 'bye']:
            rospy.loginfo("✅ 已退出目标选择循环。")
            break

        selected_obj = parse_goal_instruction(user_instruction)
        if selected_obj:
            publish_vln_goal(selected_obj)

    cleanup()
    rospy.loginfo("🔚 程序结束。")

if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        rospy.logwarn("⚠️ 节点被中断！")
    except KeyboardInterrupt:
        rospy.logwarn("⚠️ 用户手动终止程序！")
    except Exception as e:
        rospy.logerr(f"❌ 程序异常：{e}")
