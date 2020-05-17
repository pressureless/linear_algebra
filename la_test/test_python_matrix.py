import sys
sys.path.append('./')
from la_test.base_python_test import BasePythonTest
from la_parser.parser import parse_la, ParserTypeEnum
import numpy as np
import scipy
from scipy import sparse


class TestMatrix(BasePythonTest):
    def test_square_matrix(self):
        la_str = """A = [a 2; b 3]
        where
        a: scalar
        b: scalar"""
        fun_name = self.set_up(la_str, None)
        a = 1
        b = 4
        B = np.array([[1, 2], [4, 3]])
        self.assertDMatrixEqual(fun_name(a, b), B)

    def test_transpose(self):
        # T
        la_str = """B = A^T
        where
        A: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[1, 2], [4, 3]])
        B = np.array([[1, 4], [2, 3]])
        self.assertDMatrixEqual(fun_name(A), B)

        # unicode t
        la_str = """B = Aᵀ
        where
        A: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[1, 2], [4, 3]])
        B = np.array([[1, 4], [2, 3]])
        self.assertDMatrixEqual(fun_name(A), B)

    def test_inverse(self):
        # -1
        la_str = """B = A^(-1)
        where
        A: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[4, 0], [0, 0.5]])
        B = np.array([[0.25, 0], [0, 2]])
        self.assertDMatrixEqual(fun_name(A), B)

    def test_block_matrix(self):
        # normal block
        la_str = """C = [A ; B]
        where
        A: ℝ ^ (2 × 2): a matrix
        B: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[5, 6], [7, 8]])
        C = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        self.assertDMatrixEqual(fun_name(A, B), C)

        la_str = """C = [A B]
        where
        A: ℝ ^ (2 × 2): a matrix
        B: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[5, 6], [7, 8]])
        C = np.array([[1, 2, 5, 6], [3, 4, 7, 8]])
        self.assertDMatrixEqual(fun_name(A, B), C)

        # expression as item
        la_str = """C = [A+B A-B]
        where
        A: ℝ ^ (2 × 2): a matrix
        B: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[5, 6], [7, 8]])
        C = np.array([[6, 8, -4, -4], [10, 12, -4, -4]])
        self.assertDMatrixEqual(fun_name(A, B), C)

        # number matrix
        la_str = """C = [A 1_2,2; 0 0_2,2]
        where
        A: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[1, 2], [3, 4]])
        C = np.array([[1, 2, 1, 1], [3, 4, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]])
        self.assertDMatrixEqual(fun_name(A), C)

        # I identity matrix
        la_str = """C = [A 3; 2 I_2]
        where
        A: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[1, 2], [3, 4]])
        C = np.array([[1, 2, 3, 3], [3, 4, 3, 3], [2, 2, 1, 0], [2, 2, 0, 1]])
        self.assertDMatrixEqual(fun_name(A), C)

    def test_identity_matrix(self):
        # outside matrix
        la_str = """C = I_2 + A
        where
        A: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[2, 2], [3, 5]])
        self.assertDMatrixEqual(fun_name(A), B)

        # I used as symbol rather than identity matrix
        la_str = """I = A
        B = I + A
        where
        A: ℝ ^ (2 × 2): a matrix"""
        fun_name = self.set_up(la_str, None)
        A = np.array([[1, 2], [3, 4]])
        B = np.array([[2, 4], [6, 8]])
        self.assertDMatrixEqual(fun_name(A), B)

    def test_sparse_matrix(self):
        # sparse matrix: =
        la_str = """G_ij = { P_ij + J_ij  if  ( i , j ) ∈ E
        0 otherwise
        is 10  × 10
        where
        P: ℝ ^ (4 × 4): a matrix
        J: ℝ ^ (4 × 4): a matrix
        E: { ℤ × ℤ } 
        """
        fun_name = self.set_up(la_str, None)
        P = np.array([[-6, 9, -1, -11], [17, 14, 0, 0], [6, -2, 11, 0], [2, -9, -2, -9]])
        J = np.array([[-9, -6, 0, -3], [1, 10, 0, 14], [-14, -2, 10, 13], [5, 9, 0, -10]])
        E = [(3, 0), (1, 2), (3, 2), (0, 1), (3, 1), (0, 2), (2, 0)]
        value = np.array([7, 0, -2, 3, 0, -1, -8])
        B = scipy.sparse.coo_matrix((value, np.asarray(E).T), shape=(10, 10))
        self.assertSMatrixEqual(fun_name(P, J, E), B)

        # sparse matrix: +=
        la_str = """G_ij = { P_ij + J_ij  if  ( i , j ) ∈ E
        0 otherwise
        is 10  × 10

        G_jk += { ( j , k ) ∈ F : P_jk + J_jk
        0 otherwise
        is 10 × 10
        where
        P: ℝ ^ (4 × 4): a matrix
        J: ℝ ^ (4 × 4): a matrix
        E: { ℤ × ℤ }
        F: { ℤ × ℤ }"""
        fun_name = self.set_up(la_str, None)
        P = np.array([[-6, 9, -1, -11], [17, 14, 0, 0], [6, -2, 11, 0], [2, -9, -2, -9]])
        J = np.array([[-9, -6, 0, -3], [1, 10, 0, 14], [-14, -2, 10, 13], [5, 9, 0, -10]])
        E = [(3, 0), (1, 2), (3, 2), (0, 1), (3, 1), (0, 2), (2, 0)]
        F = [(1, 1), (2, 2), (3, 3)]
        G = [(1, 1), (2, 2), (3, 3), (3, 0), (1, 2), (3, 2), (0, 1), (3, 1), (0, 2), (2, 0)]
        value = np.array([24, 21, -19, 7, 0, -2, 3, 0, -1, -8])
        B = scipy.sparse.coo_matrix((value, np.asarray(G).T), shape=(10, 10))
        self.assertSMatrixEqual(fun_name(P, J, E, F), B)