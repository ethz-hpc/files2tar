from setuptools import setup

import files2tar

setup(
    name='files2tar',
    version=files2tar.__version__,
    author='Steven Armstrong',
    author_email='steven.armstrong@id.ethz.ch',
    description=files2tar.__description__,
    py_modules=['files2tar'],
    entry_points='''
        [console_scripts]
        files2tar=files2tar:run
    ''',
)
