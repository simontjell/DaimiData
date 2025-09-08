#!/usr/bin/env python3
"""
Utilities for normalizing names in PhD data.
Handles variations in names to ensure consistent matching.
"""

import re


def parse_supervisors(supervisor_str):
    """Parse supervisor string to extract individual names"""
    if not supervisor_str:
        return []
    supervisors = re.split(r',\s*|\s+and\s+|\s+&\s+|\s+og\s+', supervisor_str)
    return [s.strip() for s in supervisors if s.strip()]


def normalize_name(name):
    """Normalize names to handle variations"""
    name_map = {
        'Ole Lehrmann': 'Ole Lehrmann Madsen',
        'Clemens Klokmose': 'Clemens Nylandsted Klokmose',
        'Christian N. S. Pedersen': 'Christian N. Storm Pedersen',
        'Christian Nørgaard Storm Pedersen': 'Christian N. Storm Pedersen',
        'Christian Storm Pedersen': 'Christian N. Storm Pedersen',
        'Jesper Buus': 'Jesper Buus Nielsen',
        'Ivan Damgaard': 'Ivan Bjerre Damgård',
        'Ivan Damgård': 'Ivan Bjerre Damgård',
        'Gerth S. Brodal': 'Gerth Stølting Brodal',
        'Peter Mosses': 'Peter D. Mosses',
        'Michael Schwartzbach': 'Michael I. Schwartzbach',
        'Marianne Graves': 'Marianne Graves Petersen',
        'Jakob Bardram': 'Jakob Eyvind Bardram',
    }
    return name_map.get(name, name)