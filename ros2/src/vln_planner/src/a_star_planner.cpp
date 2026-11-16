#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <nav_msgs/msg/path.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <sensor_msgs/point_cloud2_iterator.hpp>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <functional>
#include <limits>
#include <queue>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

class AStarPlanner : public rclcpp::Node {
public:
  AStarPlanner() : rclcpp::Node("a_star_planner") {
    resolution_ = declare_parameter("resolution", 0.05);
    width_ = declare_parameter("grid_width", 500);
    height_ = declare_parameter("grid_height", 500);
    z_min_ = declare_parameter("z_min", 1.4);
    z_max_ = declare_parameter("z_max", 1.6);
    inflation_ = declare_parameter("inflation_radius", 1);
    search_radius_ = declare_parameter("goal_search_radius", 20);
    frame_ = declare_parameter("frame_id", "world");
    if (!std::isfinite(resolution_) || resolution_ <= 0 || width_ <= 0 || height_ <= 0 ||
        static_cast<int64_t>(width_) * height_ > 10000000 || inflation_ < 0 ||
        search_radius_ < 0 || z_min_ > z_max_) {
      throw std::invalid_argument("Invalid grid, filtering or inflation parameters");
    }
    grid_.resize(width_ * height_, false);
    odom_sub_ = create_subscription<nav_msgs::msg::Odometry>(
      declare_parameter("odom_topic", "/Odometry"), rclcpp::SensorDataQoS(),
      [this](nav_msgs::msg::Odometry::ConstSharedPtr msg) {
        if (!check_frame(msg->header.frame_id)) return;
        odom_ = msg->pose.pose;
        has_odom_ = true;
      });
    cloud_sub_ = create_subscription<sensor_msgs::msg::PointCloud2>(
      declare_parameter("cloud_topic", "/cloud_registered"), rclcpp::SensorDataQoS(),
      std::bind(&AStarPlanner::on_cloud, this, std::placeholders::_1));
    goal_sub_ = create_subscription<geometry_msgs::msg::PoseStamped>(
      "/vln_goal", 10, [this](geometry_msgs::msg::PoseStamped::ConstSharedPtr msg) {
        if (!check_frame(msg->header.frame_id)) return;
        goal_ = *msg;
        has_goal_ = true;
      });
    path_pub_ = create_publisher<nav_msgs::msg::Path>("/planned_path", 1);
    timer_ = create_wall_timer(std::chrono::milliseconds(100), std::bind(&AStarPlanner::plan, this));
    RCLCPP_INFO(get_logger(), "Waiting for odometry, point cloud and goal in frame %s", frame_.c_str());
  }

private:
  bool check_frame(const std::string & frame) {
    if (frame == frame_) return true;
    RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 5000,
      "Ignoring frame '%s'; expected '%s'. Transform inputs before publishing.", frame.c_str(), frame_.c_str());
    return false;
  }

  bool world_to_grid(double x, double y, int & gx, int & gy) const {
    if (!std::isfinite(x) || !std::isfinite(y)) return false;
    const double dx = std::floor(x / resolution_) + width_ / 2;
    const double dy = std::floor(y / resolution_) + height_ / 2;
    if (dx < 0 || dx >= width_ || dy < 0 || dy >= height_) return false;
    gx = static_cast<int>(dx);
    gy = static_cast<int>(dy);
    return true;
  }

  int index(int x, int y) const {return x * height_ + y;}
  bool inside(int x, int y) const {return x >= 0 && x < width_ && y >= 0 && y < height_;}
  bool free(int x, int y) const {return inside(x, y) && !grid_[index(x, y)];}

  void on_cloud(sensor_msgs::msg::PointCloud2::ConstSharedPtr msg) {
    if (!check_frame(msg->header.frame_id)) return;
    // A malformed cloud must not turn an old obstacle map into an empty map.
    std::vector<bool> next_grid(grid_.size(), false);
    try {
      // The native iterator expects packed rows and FLOAT32 coordinates.
      if (msg->point_step == 0 ||
          static_cast<uint64_t>(msg->point_step) * msg->width != msg->row_step ||
          static_cast<uint64_t>(msg->row_step) * msg->height != msg->data.size()) {
        throw std::runtime_error("Inconsistent point cloud dimensions or padded rows");
      }
      const uint16_t endian_test = 1;
      const bool host_bigendian = *reinterpret_cast<const uint8_t *>(&endian_test) == 0;
      if (msg->is_bigendian != host_bigendian) {
        throw std::runtime_error("Point cloud byte order differs from host");
      }
      for (const std::string name : {"x", "y", "z"}) {
        const auto field = std::find_if(msg->fields.begin(), msg->fields.end(),
          [&name](const auto & item) {return item.name == name;});
        if (field == msg->fields.end() || field->count != 1 ||
            field->datatype != sensor_msgs::msg::PointField::FLOAT32 ||
            static_cast<uint64_t>(field->offset) + sizeof(float) > msg->point_step) {
          throw std::runtime_error("Expected scalar FLOAT32 XYZ fields");
        }
      }
      if (msg->data.empty()) {
        grid_.swap(next_grid);
        has_cloud_ = true;
        return;
      }
      sensor_msgs::PointCloud2ConstIterator<float> x(*msg, "x"), y(*msg, "y"), z(*msg, "z");
      for (; x != x.end(); ++x, ++y, ++z) {
        if (!std::isfinite(*z) || *z < z_min_ || *z > z_max_) continue;
        int gx, gy;
        if (!world_to_grid(*x, *y, gx, gy)) continue;
        for (int dx = -inflation_; dx <= inflation_; ++dx) {
          for (int dy = -inflation_; dy <= inflation_; ++dy) {
            if (inside(gx + dx, gy + dy)) next_grid[index(gx + dx, gy + dy)] = true;
          }
        }
      }
      grid_.swap(next_grid);
      has_cloud_ = true;
    } catch (const std::runtime_error & error) {
      RCLCPP_ERROR(get_logger(), "Invalid XYZ point cloud: %s", error.what());
    }
  }

  bool nearest_free(int & gx, int & gy) const {
    if (free(gx, gy)) return true;
    for (int r = 1; r <= search_radius_; ++r) {
      for (int dx = -r; dx <= r; ++dx) {
        for (int dy = -r; dy <= r; ++dy) {
          if (std::abs(dx) != r && std::abs(dy) != r) continue;
          if (free(gx + dx, gy + dy)) {
            gx += dx;
            gy += dy;
            return true;
          }
        }
      }
    }
    return false;
  }

  std::vector<int> search(int sx, int sy, int gx, int gy) const {
    // Queue entries hold immutable costs; updating a node cannot corrupt heap order.
    using Entry = std::pair<double, int>;
    std::priority_queue<Entry, std::vector<Entry>, std::greater<Entry>> open;
    std::vector<double> cost(grid_.size(), std::numeric_limits<double>::infinity());
    std::vector<int> parent(grid_.size(), -1);
    std::vector<bool> closed(grid_.size(), false);
    auto heuristic = [gx, gy](int x, int y) {
      const int dx = std::abs(x - gx), dy = std::abs(y - gy);
      return std::max(dx, dy) + (std::sqrt(2.0) - 1.0) * std::min(dx, dy);
    };
    const int start = index(sx, sy), goal = index(gx, gy);
    cost[start] = 0;
    open.emplace(heuristic(sx, sy), start);
    while (!open.empty()) {
      const int current = open.top().second;
      open.pop();
      if (closed[current]) continue;
      if (current == goal) {
        std::vector<int> path;
        for (int cell = goal; cell != -1; cell = parent[cell]) path.push_back(cell);
        std::reverse(path.begin(), path.end());
        return path;
      }
      closed[current] = true;
      const int x = current / height_, y = current % height_;
      for (int dx = -1; dx <= 1; ++dx) {
        for (int dy = -1; dy <= 1; ++dy) {
          if ((dx == 0 && dy == 0) || !free(x + dx, y + dy)) continue;
          // Diagonals may not cross between touching occupied cells.
          if (dx && dy && (!free(x + dx, y) || !free(x, y + dy))) continue;
          const int next = index(x + dx, y + dy);
          const double candidate = cost[current] + (dx && dy ? std::sqrt(2.0) : 1.0);
          if (closed[next] || candidate >= cost[next]) continue;
          cost[next] = candidate;
          parent[next] = current;
          open.emplace(candidate + heuristic(x + dx, y + dy), next);
        }
      }
    }
    return {};
  }

  void plan() {
    if (!has_odom_ || !has_cloud_ || !has_goal_) return;
    has_goal_ = false;
    nav_msgs::msg::Path path;
    path.header.frame_id = frame_;
    path.header.stamp = now();
    int sx, sy, gx, gy;
    if (!world_to_grid(odom_.position.x, odom_.position.y, sx, sy) ||
        !world_to_grid(goal_.pose.position.x, goal_.pose.position.y, gx, gy)) {
      RCLCPP_WARN(get_logger(), "Start or goal outside grid; publishing empty path");
    } else if (!nearest_free(sx, sy) || !nearest_free(gx, gy)) {
      RCLCPP_WARN(get_logger(), "No free start or goal cell; publishing empty path");
    } else {
      for (int cell : search(sx, sy, gx, gy)) {
        geometry_msgs::msg::PoseStamped pose;
        pose.header = path.header;
        pose.pose.position.x = (cell / height_ - width_ / 2) * resolution_;
        pose.pose.position.y = (cell % height_ - height_ / 2) * resolution_;
        pose.pose.orientation.w = 1.0;
        path.poses.push_back(pose);
      }
    }
    path_pub_->publish(path);
    RCLCPP_INFO(get_logger(), "Published path with %zu waypoints", path.poses.size());
  }

  double resolution_, z_min_, z_max_;
  int width_, height_, inflation_, search_radius_;
  std::string frame_;
  std::vector<bool> grid_;
  bool has_odom_ = false, has_cloud_ = false, has_goal_ = false;
  geometry_msgs::msg::Pose odom_;
  geometry_msgs::msg::PoseStamped goal_;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr cloud_sub_;
  rclcpp::Subscription<geometry_msgs::msg::PoseStamped>::SharedPtr goal_sub_;
  rclcpp::Publisher<nav_msgs::msg::Path>::SharedPtr path_pub_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char ** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<AStarPlanner>());
  rclcpp::shutdown();
  return 0;
}
