#!/usr/bin/env python3
import cv2
import numpy as np
from ultralytics import YOLO

# ===================== 初始化模块 =====================
# 1. 摄像头配置
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
if not cap.isOpened():
    print("摄像头打开失败！")
    exit()

# 2. YOLOv5模型（轻量版，自动下载权重）
yolov5_model = YOLO('yolov5n.pt')  # n版最小最快，s版更准
conf_threshold = 0.5  # 置信度阈值

# 3. ORB检测器（保留原优化参数）
orb = cv2.ORB_create(
    nfeatures=300,
    scaleFactor=1.3,
    edgeThreshold=15,
    patchSize=15
)

# ===================== 核心函数 =====================
def filter_orb_in_box(kp, box):
    """仅保留检测框内的ORB特征点"""
    x1, y1, x2, y2 = box
    # 条件：坐标在框内（+5像素余量）+ 特征点尺寸<20
    filtered_kp = [
        p for p in kp 
        if (x1-5 <= p.pt[0] <= x2+5) and (y1-5 <= p.pt[1] <= y2+5) and p.size < 20
    ]
    return filtered_kp

# ===================== 主循环 =====================
if __name__ == '__main__':
    while True:
        # 读取摄像头画面
        ret, frame = cap.read()
        if not ret:
            print("无法读取摄像头画面！")
            break
        
        # 1. YOLOv5目标检测
        results = yolov5_model(frame, conf=conf_threshold)
        detection_boxes = []  # 存储：[x1,y1,x2,y2,类别名,置信度]
        
        # 解析检测结果
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # 检测框坐标
                conf = float(box.conf[0])                # 置信度
                cls_name = yolov5_model.names[int(box.cls[0])]  # 类别名
                detection_boxes.append([x1, y1, x2, y2, cls_name, conf])
        
        # 2. 全图ORB特征点检测
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        kp, _ = orb.detectAndCompute(gray, None)
        
        # 3. 绘制检测框 + 仅框内ORB特征点
        frame_draw = frame.copy()
        for box_info in detection_boxes:
            x1, y1, x2, y2, cls_name, conf = box_info
            
            # 绘制检测框和标签
            cv2.rectangle(frame_draw, (x1, y1), (x2, y2), (0, 0, 255), 2)
            label = f"{cls_name}: {conf:.2f}"
            cv2.putText(frame_draw, label, (x1, y1-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # 过滤并绘制该框内的ORB特征点
            box_kp = filter_orb_in_box(kp, (x1, y1, x2, y2))
            frame_draw = cv2.drawKeypoints(
                frame_draw, box_kp, None, (0, 255, 0), flags=0
            )
        
        # 显示画面（标注特征点数量）
        total_orb = sum([len(filter_orb_in_box(kp, b[:4])) for b in detection_boxes])
        cv2.putText(frame_draw, f"ORB in boxes: {total_orb}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        cv2.imshow("YOLOv5 + ORB (Only in Detection Box)", frame_draw)
        
        # 按q退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # 释放资源
    cap.release()
    cv2.destroyAllWindows()