from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="micro_users",
    version="1.0.2",
    author="DeBeski",
    author_email="debeski1@gmail.com",
    description="Arabic django user management app with abstract user, permissions, and activity logging",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/debeski/micro-users",
    packages=["users"],
    include_package_data=True,
    classifiers=[
        "Framework :: Django",
        "Framework :: Django :: 5",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "Django>=5.17",
        "django-crispy-forms>=2.4",
        "django-tables2>=2.7",
        "django-filter>=24.3",
        "pillow>=11.0",
        "babel>=2.1",
    ],
    license="MIT",
)