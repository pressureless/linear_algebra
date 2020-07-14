import sys
sys.path.append('./')
from la_test.base_python_test import BasePythonTest, eigen_path, TestFuncInfo
from la_parser.parser import parse_la, ParserTypeEnum
import numpy as np
import cppyy
cppyy.add_include_path(eigen_path)


class TestOthers(BasePythonTest):
    def test_integral_1(self):
        # no return symbol
        la_str = """c = int_[1, 2] ia ∂i
        where 
        a: scalar """
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(2), 3)

    def test_integral_2(self):
        # no return symbol
        la_str = """c = int_1^2 ia ∂i
        where 
        a: scalar """
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(2), 3)

    def test_nested_integral(self):
        # no return symbol
        la_str = """c = int_0^3  int_[1, 2] ia ∂i ∂j
        where 
        a: scalar """
        func_info = self.gen_func_info(la_str)
        self.assertEqual(func_info.numpy_func(2), 9)