    from setuptools import find_packages, setup
    import os
    from glob import glob # glob might still be useful for users editing setup.py later

    package_name = 'my_detailed_py_pkg_for_debug'

    setup(
        name=package_name,
        version='2.1.2',
        packages=find_packages(exclude=['test']),
        data_files=[
('share/ament_index/resource_index/packages', ['resource/my_detailed_py_pkg_for_debug']),
('share/my_detailed_py_pkg_for_debug', ['package.xml']),
        ],
        install_requires=['setuptools'], # Add other python dependencies from PackageConfig here eventually
        zip_safe=True,
        maintainer='Main Developer',
        maintainer_email='main.dev@example.com',
        description='A Python package for debugging attributes.',
        license='Apache License 2.0',
        tests_require=['pytest'],
        entry_points={
            'console_scripts': [
                'hello_world = my_detailed_py_pkg_for_debug.hello_world_node:main'
            ],
        },
    )
