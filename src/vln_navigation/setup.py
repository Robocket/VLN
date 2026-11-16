from setuptools import find_packages, setup

setup(
    name='vln_navigation',
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/vln_navigation']),
        ('share/vln_navigation', ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='TODO',
    maintainer_email='TODO@example.com',
    description='vln navigation for ROS 2',
    license='TODO',
    tests_require=['pytest'],
    entry_points={'console_scripts': ['vln_goal = vln_navigation.goal_selector:main', 'instruction_cli = vln_navigation.instruction_cli:main']},
)
