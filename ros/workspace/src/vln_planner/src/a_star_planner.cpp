#include <ros/ros.h>
#include <nav_msgs/Odometry.h>
#include <sensor_msgs/PointCloud2.h>
#include <geometry_msgs/PoseStamped.h>
#include <nav_msgs/Path.h>
#include <pcl_conversions/pcl_conversions.h>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl/filters/passthrough.h>
#include <vector>
#include <queue>
#include <unordered_map>
#include <cmath>
#include <memory>
#include <algorithm>

// 参数配置
const double RESOLUTION = 0.05;      // 栅格分辨率 (米)
const double Z_MIN = 1.4;           // Z轴最小过滤值
const double Z_MAX = 1.6;           // Z轴最大过滤值
const int GRID_SIZE_X = 500;         // 栅格地图X方向大小 (格)
const int GRID_SIZE_Y = 500;         // 栅格地图Y方向大小 (格)

// 全局变量存储最新数据
geometry_msgs::Pose current_odom;
geometry_msgs::PoseStamped current_goal;
std::vector<std::vector<int>> grid_map(GRID_SIZE_X, std::vector<int>(GRID_SIZE_Y, 0));
bool has_odom = false;
bool has_goal = false;

// A* 节点结构 (使用智能指针管理内存，添加closed标记)
struct Node {
    int x, y;
    double g, h, f;
    std::shared_ptr<Node> parent;
    bool closed; // 标记是否已处理

    Node(int x_, int y_) : x(x_), y(y_), g(0), h(0), f(0), parent(nullptr), closed(false) {}
};

// 计算启发式距离 (8方向移动推荐切比雪夫，若需严格最短路径可用欧几里得)
double heuristic(int x1, int y1, int x2, int y2) {
    // 切比雪夫距离 (更适合8方向网格)
    int dx = std::abs(x2 - x1);
    int dy = std::abs(y2 - y1);
    return std::max(dx, dy);
    
    // 欧几里得距离 (如果需要保留原逻辑，请注释上面两行，取消下面注释)
    // return std::sqrt(std::pow(x2 - x1, 2) + std::pow(y2 - y1, 2));
}

// 世界坐标转栅格坐标
void worldToGrid(double wx, double wy, int &gx, int &gy) {
    gx = static_cast<int>(wx / RESOLUTION) + GRID_SIZE_X / 2;
    gy = static_cast<int>(wy / RESOLUTION) + GRID_SIZE_Y / 2;
    // 边界检查
    gx = std::max(0, std::min(GRID_SIZE_X - 1, gx));
    gy = std::max(0, std::min(GRID_SIZE_Y - 1, gy));
}

// 栅格坐标转世界坐标
void gridToWorld(int gx, int gy, double &wx, double &wy) {
    wx = (gx - GRID_SIZE_X / 2) * RESOLUTION;
    wy = (gy - GRID_SIZE_Y / 2) * RESOLUTION;
}

// 回调函数：处理里程计
void odomCallback(const nav_msgs::Odometry::ConstPtr& msg) {
    current_odom = msg->pose.pose;
    has_odom = true;
}

// 回调函数：处理点云并更新栅格地图 (包含障碍物膨胀)
void cloudCallback(const sensor_msgs::PointCloud2::ConstPtr& msg) {
    // --- 1. 基础点云转换与滤波 (确保 cloud 变量被声明) ---
    pcl::PointCloud<pcl::PointXYZ>::Ptr cloud(new pcl::PointCloud<pcl::PointXYZ>);
    pcl::fromROSMsg(*msg, *cloud);

    // Z轴范围滤波
    pcl::PassThrough<pcl::PointXYZ> pass;
    pass.setInputCloud(cloud);
    pass.setFilterFieldName("z");
    pass.setFilterLimits(Z_MIN, Z_MAX);
    pass.filter(*cloud);

    // --- 2. 重置地图 ---
    for (auto &row : grid_map) std::fill(row.begin(), row.end(), 0);

    // --- 3. 填充原始障碍物 (标记为 1) ---
    std::vector<std::pair<int, int>> raw_obstacles; // 暂存原始障碍坐标
    for (auto &pt : cloud->points) {
        int gx, gy;
        worldToGrid(pt.x, pt.y, gx, gy);
        if (grid_map[gx][gy] == 0) {
            grid_map[gx][gy] = 1; 
            raw_obstacles.emplace_back(gx, gy);
        }
    }

    // --- 4. 障碍物膨胀 (标记为 2) ---
    const int INFLATION_RADIUS = 1; // 膨胀半径 (格)，可根据机器人大小调整
    for (auto &obs : raw_obstacles) {
        int gx = obs.first;
        int gy = obs.second;
        // 遍历周围区域
        for (int dx = -INFLATION_RADIUS; dx <= INFLATION_RADIUS; ++dx) {
            for (int dy = -INFLATION_RADIUS; dy <= INFLATION_RADIUS; ++dy) {
                int nx = gx + dx;
                int ny = gy + dy;
                // 边界检查，且不要覆盖原本的障碍物(1)
                if (nx >= 0 && nx < GRID_SIZE_X && ny >= 0 && ny < GRID_SIZE_Y) {
                    if (grid_map[nx][ny] == 0) {
                        grid_map[nx][ny] = 2; // 2 代表“危险区域/膨胀区”
                    }
                }
            }
        }
    }
}

// 寻找最近的自由栅格 (螺旋搜索算法)
bool findNearestFreeCell(int &gx, int &gy, int max_search_radius = 20) {
    // 1. 如果当前点本身就是自由的，直接返回
    if (grid_map[gx][gy] == 0) return true;

    // 2. 螺旋式向外搜索
    for (int r = 1; r <= max_search_radius; ++r) {
        // 搜索正方形的四条边
        for (int dx = -r; dx <= r; ++dx) {
            for (int dy = -r; dy <= r; ++dy) {
                // 跳过内部点，只搜索当前半径的边界
                if (std::abs(dx) != r && std::abs(dy) != r) continue;
                
                int nx = gx + dx;
                int ny = gy + dy;
                
                // 边界检查
                if (nx >= 0 && nx < GRID_SIZE_X && ny >= 0 && ny < GRID_SIZE_Y) {
                    if (grid_map[nx][ny] == 0) { // 找到自由空间
                        gx = nx;
                        gy = ny;
                        ROS_WARN("Goal was in obstacle! Moved to nearest free cell.");
                        return true;
                    }
                }
            }
        }
    }
    ROS_ERROR("No valid free cell found near goal within search radius.");
    return false;
}


// 回调函数：处理目标点并触发规划
void goalCallback(const geometry_msgs::PoseStamped::ConstPtr& msg) {
    current_goal = *msg;
    has_goal = true;
}

// --- 修复后的 A* 算法核心实现 ---
std::vector<std::shared_ptr<Node>> aStarSearch(std::shared_ptr<Node> start, std::shared_ptr<Node> goal) {
    // 1. 优先队列 (小顶堆：f值最小的在顶部)
    auto cmp = [](std::shared_ptr<Node> a, std::shared_ptr<Node> b) { return a->f > b->f; };
    std::priority_queue<std::shared_ptr<Node>, std::vector<std::shared_ptr<Node>>, decltype(cmp)> open_list(cmp);
    
    // 2. 哈希表：存储所有节点 (Key优化为 x * GRID_SIZE_Y + y，避免冲突)
    std::unordered_map<int, std::shared_ptr<Node>> all_nodes;

    // 3. 初始化起点
    start->h = heuristic(start->x, start->y, goal->x, goal->y);
    start->f = start->g + start->h;
    open_list.push(start);
    all_nodes[start->x * GRID_SIZE_Y + start->y] = start;

    // 4. 8方向移动
    int dirs[8][2] = {{-1,0}, {1,0}, {0,-1}, {0,1}, {-1,-1}, {-1,1}, {1,-1}, {1,1}};

    while (!open_list.empty()) {
        // 5. 取出f值最小的节点
        auto current = open_list.top();
        open_list.pop();

        // 6. 【关键修复】跳过已处理的旧节点 (优先队列中可能存在重复副本)
        if (current->closed) continue;

        // 7. 到达终点，回溯路径
        if (current->x == goal->x && current->y == goal->y) {
            std::vector<std::shared_ptr<Node>> path;
            while (current) {
                path.push_back(current);
                current = current->parent;
            }
            std::reverse(path.begin(), path.end());
            return path;
        }

        // 8. 标记为已处理
        current->closed = true;

        // 9. 遍历邻居
        for (auto &dir : dirs) {
            int nx = current->x + dir[0];
            int ny = current->y + dir[1];

            // 10. 边界与碰撞检测
            // 现在不仅要避开 1(障碍)，还要避开 2(膨胀区)，只有 0 能走
            if (nx < 0 || nx >= GRID_SIZE_X || ny < 0 || ny >= GRID_SIZE_Y || grid_map[nx][ny] != 0)
                continue;

            // 11. 计算代价
            double move_cost = (dir[0] != 0 && dir[1] != 0) ? 1.414 : 1.0;
            double tentative_g = current->g + move_cost;

            int key = nx * GRID_SIZE_Y + ny;
            auto it = all_nodes.find(key);

            if (it == all_nodes.end()) {
                // 12. 节点未访问过：新建节点
                auto neighbor = std::make_shared<Node>(nx, ny);
                neighbor->parent = current;
                neighbor->g = tentative_g;
                neighbor->h = heuristic(nx, ny, goal->x, goal->y);
                neighbor->f = neighbor->g + neighbor->h;

                all_nodes[key] = neighbor;
                open_list.push(neighbor);
            } else {
                // 13. 【关键修复】节点已存在：检查是否找到更优路径
                auto neighbor = it->second;
                if (!neighbor->closed && tentative_g < neighbor->g) {
                    // 更新路径
                    neighbor->parent = current;
                    neighbor->g = tentative_g;
                    neighbor->f = neighbor->g + neighbor->h;
                    // 重新加入队列 (旧副本会在步骤6被跳过)
                    open_list.push(neighbor);
                }
            }
        }
    }
    return {}; // 未找到路径
}

int main(int argc, char** argv) {
    ros::init(argc, argv, "a_star_planner");
    ros::NodeHandle nh;

    // 订阅者
    ros::Subscriber sub_odom = nh.subscribe("/Odometry", 1, odomCallback);
    ros::Subscriber sub_cloud = nh.subscribe("/cloud_registered", 1, cloudCallback);
    ros::Subscriber sub_goal = nh.subscribe("/vln_goal", 1, goalCallback);

    // 发布者
    ros::Publisher pub_path = nh.advertise<nav_msgs::Path>("/planned_path", 1);

    ros::Rate rate(10); // 10Hz
    ROS_INFO("A* Planner Node Started. Waiting for goal...");

    while (ros::ok()) {
        ros::spinOnce();

        // 只有当有起点、终点时才规划
        if (has_odom && has_goal) {
            // 1. 坐标转换
            int start_gx, start_gy, goal_gx, goal_gy;
            worldToGrid(current_odom.position.x, current_odom.position.y, start_gx, start_gy);
            worldToGrid(current_goal.pose.position.x, current_goal.pose.position.y, goal_gx, goal_gy);

            // 2. 【关键修正】强制目标点移动到安全区域
            if (!findNearestFreeCell(goal_gx, goal_gy)) {
                has_goal = false;
                continue; // 找不到安全目标，放弃本次规划
            }
            
            // 3. 【可选】检查起点是否被卡住 (如果机器人启动时在障碍里)
            if (grid_map[start_gx][start_gy] != 0) {
                if (!findNearestFreeCell(start_gx, start_gy)) {
                    ROS_ERROR("Robot is trapped!");
                    has_goal = false;
                    continue;
                }
            }

            // 4. 执行A* (使用智能指针)
            auto start_node = std::make_shared<Node>(start_gx, start_gy);
            auto goal_node = std::make_shared<Node>(goal_gx, goal_gy);
            std::vector<std::shared_ptr<Node>> path = aStarSearch(start_node, goal_node);

            // 5. 生成并发布Path消息
            nav_msgs::Path path_msg;
            path_msg.header.stamp = ros::Time::now();
            path_msg.header.frame_id = "world"; // 请确保与你的TF坐标系匹配

            if (!path.empty()) {
                for (auto &n : path) {
                    geometry_msgs::PoseStamped pose;
                    pose.header = path_msg.header;
                    gridToWorld(n->x, n->y, pose.pose.position.x, pose.pose.position.y);
                    pose.pose.position.z = 0;
                    pose.pose.orientation.w = 1.0;
                    path_msg.poses.push_back(pose);
                }
                ROS_INFO("Path found with %zu waypoints", path_msg.poses.size());
            } else {
                ROS_WARN("No valid path found!");
            }
            pub_path.publish(path_msg);
            
            has_goal = false; // 规划完一次后重置，等待下一个goal
        }
        rate.sleep();
    }
    return 0;
}
