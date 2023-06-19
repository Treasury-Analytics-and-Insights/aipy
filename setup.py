from distutils.core import setup

def main():
    """ obvs the main script """
    setup(
        name="aipy",
        package_dir={'aipy':'aipy'},
        packages=['aipy'],
        scripts=[])

if __name__ == '__main__':
    main()