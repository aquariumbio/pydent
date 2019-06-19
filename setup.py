from distutils.core import setup

tests_require = ["pytest", "pytest-cov", "vcrpy"]

install_requires = [
    "inflection",
    "requests",
    "networkx",
    "pandas",
    "tqdm",
    "nest_asyncio",
]

# setup
setup(
    title="Trident",
    name="pydent",
    version="0.1.0a",
    packages=["pydent", "pydent.marshaller", "pydent.utils", "pydent.planner"],
    tests_require=tests_require,
    install_requires=install_requires,
)
