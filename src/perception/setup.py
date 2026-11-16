from setuptools import find_packages, setup

setup(
    name='vln_perception',
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/vln_perception']),
        ('share/vln_perception', ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='TODO',
    maintainer_email='TODO@example.com',
    description='vln perception for ROS 2',
    license='TODO',
    tests_require=['pytest'],
    entry_points={'console_scripts': ['streaming_semantics = vln_perception.semantic_node:main']},
)
