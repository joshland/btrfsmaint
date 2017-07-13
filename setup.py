from setuptools import setup

setup(
    name="btrfsmaint",
    description='BTRFS Filesystem Maintenace Scripts.',
    long_description='BTRFS Filesystem Maintenance Script for local btrfs filesystem upkeep.',
    url='https://github.com/joshland/btrfsmaint',
    author='Joshua M. Schmidlkofer',
    author_email='joshland@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Filesystems',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    version="0.5",
    install_requires=[
        "click",
    ],
    keywords='btrfs maintenance administration',
    packages=['btrfsmaint'],
    entry_points={
        'console_scripts': [
            'btrfsmaint=btrfsmaint:Main',
        ],
    },
)
