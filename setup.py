from setuptools import setup

setup(
    name='files2tar',
    version='0.1.0',
    author='Steven Armstrong',
    author_email='steven.armstrong@id.ethz.ch',
    description='pack a list of files into tar archives of a given size',
    py_modules=['files2tar'],
    entry_points='''
        [console_scripts]
        files2tar=files2tar:run
    ''',
)