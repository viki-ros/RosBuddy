    from setuptools import find_packages, setup
    import os
    from glob import glob # glob might still be useful for users editing setup.py later

    package_name = 'py_pkg_with_files'

    setup(
        name=package_name,
        version='3.0.0',
        packages=find_packages(exclude=['test']),
        data_files=[
('share/ament_index/resource_index/packages', ['resource/py_pkg_with_files']),
('share/py_pkg_with_files', ['package.xml']),
('share/py_pkg_with_files/launch', ['launch/my_robot.launch.py', 'launch/another_utility.launch.xml']),
('share/py_pkg_with_files/config', ['config/robot_params.yaml', 'config/pid_gains.yaml']),
        ],
        install_requires=['setuptools'], # Add other python dependencies from PackageConfig here eventually
        zip_safe=True,
        maintainer='Install Dev',
        maintainer_email='installer@example.com',
        description='Python package to test installation of launch/config/interface files.',
        license='Apache License 2.0',
        tests_require=['pytest'],
        entry_points={
            'console_scripts': [
                'hello_world = py_pkg_with_files.hello_world_node:main'
            ],
        },
    )
