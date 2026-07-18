# This file is part of cooperative_ar. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

"""Test scenario."""
from trytond.tests.test_tryton import load_doc_tests


def load_tests(*args, **kwargs):
    """Load test"""
    return load_doc_tests(__name__, __file__, *args, **kwargs)
