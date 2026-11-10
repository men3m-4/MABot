from glob import glob

from setuptools import find_packages, setup


package_name = 'mabot_bringup'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name],
        ),
        ('share/' + package_name, ['package.xml', 'README.md']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Mohamed Abdelmoniem',
    maintainer_email='muhammad.abeelmoniem4@gmail.com',
    description=(
        'Centralized simulation, navigation, and warehouse mission '
        'startup for MABot.'
    ),
    license='Apache-2.0',
    extras_require={
        'test': ['pytest'],
    },
)
