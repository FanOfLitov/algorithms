import unittest
import tempfile
import os
from xml_parser import parse_xml_file



root = parse_xml_file("test.xml")
print(root)