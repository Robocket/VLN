# 1. 导入torch库
import torch

# 2. 打印torch版本号（核心命令）
print("PyTorch版本：", torch.__version__)

# 可选：查看适配的CUDA版本（如果安装了CUDA版本的torch）
print("适配的CUDA版本：", torch.version.cuda)

# 可选：检查CUDA是否可用（验证GPU环境）
print("CUDA是否可用：", torch.cuda.is_available())
