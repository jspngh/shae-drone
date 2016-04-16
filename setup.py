from distutils.core import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
# def read(fname):
#    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='shae',
    version='0.1',
    author='Project Shae',
    author_email='contact@shae.be',
    description=('The drone code for Project Shae'),
    packages=['shae', 'shae.simulator', 'shae.onboard'],
    package_dir={'shae': 'src', 'shae.simulator': 'src/simulator', 'shae.onboard': 'src/onboard'},
    package_data={'shae.simulator': ['videos/*.h264', 'videos/*.mp4']}
    # long_description=read('README'),
)
