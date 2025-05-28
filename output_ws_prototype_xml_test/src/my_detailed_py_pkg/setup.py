from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'my_detailed_py_pkg'

setup(
    name=package_name,
    version='2.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Example: include launch files
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*')))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Main Developer',
    maintainer_email='main.dev@example.com',
    description='A more detailed Python package for testing XML generation.',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'hello_world = my_detailed_py_pkg.hello_world_node:main'
        ],
    },
)
