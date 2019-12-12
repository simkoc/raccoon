from setuptools import setup

setup(name='selrun',
      version='0.0.1',
      description='Selenese Runner API',
      author='Giancarlo Pellegrino',
      author_email='gpellegrino@cispa.saarland',
      license='MIT',
      packages=['selrun'],
      install_requires=['lxml'],
      zip_safe=False)