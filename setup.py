from setuptools import setup, find_packages

setup(name='gspn_lib',
      version='1.0',
      description='Package to create, manipulate and simulate generalized stochastic Petri nets.',
      url='github.com/cazevedo/gspn-lib',
      author='Carlos Azevedo',
      install_requires=['numpy', 'sparse', 'graphviz', 'pathlib'],
      author_email='cguerraazevedo@tecnico.ulisboa.pt',
      packages=['gspn_lib'],
      zip_safe=False
)