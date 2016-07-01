import dagger
import setuptools

REQUIRES = []

# read the requirements file and add all non-comment/non-whitespace lines to the
# requirements for setuptools.
with open("requirements.txt", 'r') as f:
    for ln in f.readlines():
        if len(ln) > 0 and ln[0] not in (' ', "#"):
            REQUIRES.append(ln.strip())

# declare the package with setuptools
setuptools.setup(
    name='dagger',
    maintainer='tychoish',
    maintainer_email='sam@mongodb.com',
    description='Library Linking Graph Introspection Tool',
    version=dagger.__version__,
    url='http://github.com/mongodb/dagger',
    packages=setuptools.find_packages(),
    test_suite="nose.collector",
    install_requires=REQUIRES,
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'Programming Language :: Python',
    ],
    entry_points={
        'console_scripts': [
            "dagger = dagger.cli:main"
            ],
        },
    )
