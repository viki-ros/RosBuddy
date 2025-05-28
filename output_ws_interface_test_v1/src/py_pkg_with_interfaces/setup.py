    from setuptools import find_packages, setup
    import os
    from glob import glob # glob might still be useful for users editing setup.py later

    package_name = 'py_pkg_with_interfaces'

    setup(
        name=package_name,
        version='1.0.0',
        packages=find_packages(exclude=['test']),
        data_files=[
('share/ament_index/resource_index/packages', ['resource/py_pkg_with_interfaces']),
('share/py_pkg_with_interfaces', ['package.xml']),
        ],
        install_requires=['setuptools'],
        zip_safe=True,
        maintainer='Py Interface Dev',
        maintainer_email='if_py@example.com',
        description='Python package to test interface definitions in package.xml.',
        license='Apache License 2.0',
        tests_require=['pytest'],
        entry_points={
            'console_scripts': [
                'hello_world = py_pkg_with_interfaces.hello_world_node:main'
            ],
        },
    )
