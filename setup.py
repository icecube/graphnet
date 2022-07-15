import subprocess
import sys
from setuptools import setup, find_packages
import versioneer

# Requirements definitions
SETUP_REQUIRES = [
    "setuptools>=59.5.0",
]

INSTALL_REQUIRES = [
    "awkward>=1.8",
    "dill>=0.3",
    "matplotlib>=3.5",
    "numpy>=1.21",
    "pandas>=1.3",
    "pyarrow",
    "scikit_learn>=1.0",
    "scipy>=1.7",
    "sqlalchemy>=1.4",
    "timer>=0.2",
    "tqdm>=4.64",
    "wandb>=0.12",
]

EXTRAS_REQUIRE = {
    "develop": [
        "black",
        "colorlog",
        "coverage",
        "pre-commit",
        "pydocstyle",
        "pylint",
        "pytest",
        "pytest-order",
        "sphinx",
        "sphinx_rtd_theme",
        "versioneer",
    ],
    "torch": [
        "torch==1.11",
        "torch-cluster==1.6.0",
        "torch-scatter==2.0.9",
        "torch-sparse==0.6.13",
        "torch-spline-conv==1.2.1",
        "torch-geometric==2.0.4",
        "pytorch-lightning>=1.6",
    ],
}

# https://pypi.org/classifiers/
CLASSIFIERS = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Environment :: CPU",
    "Environment :: GPU",
    "License :: OSI Approved :: Apache Software License",
    "Topic :: Scientific/Engineering",
    "Topic :: Scientific/Engineering :: Physics",
    "Topic :: Scientific/Engineering :: Mathematics",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Software Development",
    "Topic :: Software Development :: Libraries",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

setup(
    name="graphnet",
    version=versioneer.get_version(),
    description=(
        "A common library for using graph neural networks (GNNs) in netrino "
        "telescope experiments."
    ),
    license="Apache 2.0",
    author="The IceCube Collaboration",
    url="https://github.com/icecube/graphnet",
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    setup_requires=SETUP_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    classifiers=CLASSIFIERS,
)
