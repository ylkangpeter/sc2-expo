# -*- coding: utf-8 -*-

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from debug_utils import format_time_to_mmss


def test_format_time_to_mmss_formats_seconds():
    assert format_time_to_mmss(65) == "01:05"
