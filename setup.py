import setuptools

setuptools.setup(
    name="arkio",
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "ark = ark.__main__:main",
        ]
    },
    include_package_data=True,
)
