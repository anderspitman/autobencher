# Import this file into all test files before importing anything from
# autobencher so they can find the autobencher package
import sys
import os

testing_path = os.path.dirname(os.path.abspath(__file__))
package_path = testing_path + '/../../'
sys.path.insert(0, package_path)


def use_package_so_flake8_is_happy():
    pass
