from setuptools import setup

setup(
    name='beets-gaana',
    version='0.1',
    description='beets plugin to use Gaana for metadata',
    long_description=open('README.md').read(),
    author='Alok Saboo',
    author_email='',
    url='https://github.com/arsaboo/beets-gaana',
    license='MIT',
    platforms='ALL',
    packages=['beetsplug'],
    install_requires=[
        'beets>=1.6.0',
        'requests',
        'pillow',
    ],
)
