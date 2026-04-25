from pathlib import Path
from setuptools import find_packages, setup

_readme = Path(__file__).resolve().parent / "README.md"
long_description = _readme.read_text(encoding="utf-8") if _readme.is_file() else ""

# Distribution name is django-arc-pay; import package is django_arc_monitize_api.
# Runtime depends on circle-titanoboa-sdk (import name: circlekit), installed
# directly from GitHub via a PEP 508 direct URL.

setup(
    name="django-arc-pay",
    version="0.1.0",
    description="Django x402 / Arc USDC paywall via @monetize decorator (Circle Gateway).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=("tests", "tests.*")),
    install_requires=[
        "django>=4.0",
        "circle-titanoboa-sdk @ git+https://github.com/vyperlang/circle-titanoboa-sdk.git",
    ],
    extras_require={
        "test": ["pytest>=8.0"],
    },
)
