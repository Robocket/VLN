import cv2
# 打开默认摄像头（参数0对应/dev/video0）
cap = cv2.VideoCapture(0)
# 检查摄像头是否成功打开
if not cap.isOpened():
    print("摄像头打开失败")
    exit()
while True:
    # 读取摄像头画面
    ret, frame = cap.read()
    # 若读取失败则退出循环
    if not ret:
        print("无法读取画面")
        break
    # 显示实时画面
    cv2.imshow("Camera Capture", frame)
    # 按下q键退出
    if cv2.waitKey(1) == ord('q'):
        break
# 释放摄像头资源并关闭窗口
cap.release()
cv2.destroyAllWindows()
