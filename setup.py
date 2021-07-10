import setuptools

setuptools.setup(
    name='popularity-contest',
    version='0.2',
    url="https://github.com/yuvipanda/python-popularity-contest",
    author="Yuvi Panda",
    packages=setuptools.find_packages(),
    install_requires=[
        'statsd',
        'importlib_metadata'
    ]
)
