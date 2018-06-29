import os
import re
from distutils.core import setup


tests_require = [
    'pytest',
    'pytest-cov'
]

install_requires = [
    'inflection',
    'marshmallow==2.15.1',
    'requests',
    'prompt-toolkit==2.0.3',
    'tqdm==4.23.4'
]

def parse_version_file():
    here = os.path.abspath(os.path.dirname(__file__))
    ver_dict = {}
    with open(os.path.join(here, 'pydent', '__version__.py'), 'r') as f:
        for line in f.readlines():
            m = re.match('__(\w+)__\s*=\s*(.+)', line)
            if m:
                key = m.group(1)
                val = m.group(2)
                val = re.sub("[\'\"]", "", val)
                ver_dict[key] = val
    return ver_dict


ver = parse_version_file()

# setup
setup(
        title=ver['title'],
        name='pydent',
        version=ver['version'],
        packages=["pydent", "pydent.marshaller", "pydent.utils"],
        url=ver['url'],
        license='',
        author=ver['author'],
        author_email=ver['author_email'],
        keywords='aquarium api',
        description=ver['description'],
        install_requires=install_requires,
        python_requires='>=3.4',
        tests_require=tests_require,
)
