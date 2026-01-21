from setuptools import setup

setup(
    name="masonite-app",
    version="1.0.0",
    install_requires=[
        "masonite==4.20.2",
        "gunicorn==21.2.0",
        "pendulum==2.1.2",
    ],
)
