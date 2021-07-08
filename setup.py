import setuptools

setuptools.setup(
    name='popularity-contest',
    version='0.1',
    url="https://github.com/yuvipanda/python-popularity-contest",
    author="Yuvi Panda",
    packages=setuptools.find_packages(),
    install_requires=[
        'stdlib-list',
        'statsd'
    ]
)
