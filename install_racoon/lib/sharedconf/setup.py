from setuptools import setup

setup(name='sharedconf',
      version='0.0.1',
      description='Shared Configuration of Deep Modeling',
      author='Giancarlo Pellegrino',
      author_email='gpellegrino@cispa.saarland',
      license='MIT',
      packages=['sharedconf'],
      install_requires=[
          'ConfigParser',
          'AttrDict'
      ],
      zip_safe=False)