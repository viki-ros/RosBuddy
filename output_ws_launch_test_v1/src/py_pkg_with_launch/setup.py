    from setuptools import find_packages, setup
    import os
    from glob import glob # glob might still be useful for users editing setup.py later

    package_name = 'py_pkg_with_launch'

    setup(
        name=package_name,
        version='4.0.0',
        packages=find_packages(exclude=['test']),
        data_files=[
('share/ament_index/resource_index/packages', ['resource/py_pkg_with_launch']),
('share/py_pkg_with_launch', ['package.xml']),
('share/py_pkg_with_launch/launch', ['launch/main_robot.launch.py', 'launch/included_utility.launch.py']),
('share/py_pkg_with_launch/config', ['config/main_robot_params.yaml']),
        ],
        install_requires=['setuptools'],
        zip_safe=True,
        maintainer='Launch Dev',
        maintainer_email='launcher@example.com',
        description='Python package to test launch file generation and installation.',
        license='Apache License 2.0',
        tests_require=['pytest'],
        entry_points={
            'console_scripts': [
                'hello_world = py_pkg_with_launch.hello_world_node:main'
            ],
        },
    )
