"""eyelink_reader module.
"""
from os.path import dirname, join as joinpath

from .edffile import EDFFile

EXAMPLE_FILE = joinpath(dirname(__file__), 'data', 'example.edf')
