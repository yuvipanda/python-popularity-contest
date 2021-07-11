import setuptools

setuptools.setup(
    name='popularity-contest',
    version='0.4.1',
    url="https://github.com/yuvipanda/python-popularity-contest",
    description="Privacy-friendly data collection of the libraries your users are using",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Yuvi Panda",
    packages=setuptools.find_packages(),
    install_requires=[
        'statsd',
        'importlib_metadata'
    ]
)
