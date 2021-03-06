from setuptools import setup, find_packages
import sys, os

version = '1.0.11'

setup(name='optilux.cinemacontent',
      version=version,
      description="Cinema content types for the Optilux example application",
      long_description="""\
""",
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
        "Framework :: Zope3",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='Optilux Corp',
      author_email='webmaster@optilux-cinemas.com',
      url='http://optilux-cinemas.com',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['optilux'],
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
          'setuptools',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
