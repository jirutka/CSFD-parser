from distutils.core import setup

__version__ = '1.0.5'

setup(
    name='csfd-parser',
    version=__version__,
    py_modules=['csfd'],
    url='https://github.com/jirutka/CSFD-parser',
    license='LGPL version 3',
    author='Jakub Jirutka',
    author_email='jakub@jirutka.cz',
    description='Parser for movie pages and search on CSFD.cz',
    long_description=open('README.md').read(),
    requires=[
        'lxml',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
