from setuptools import setup

setup(name='mosgi',
      version='1.1.1',
      description='Mosgi Library',
      author='Simon Koch',
      author_email='s9sikoch@stud.uni-saarland.de',
      license='???',
      packages=['mosgi'],
      install_requires=[
          'paramiko',
          'psycopg2',
          'six'
      ],
      zip_safe=False)
