from enum import Enum


class LaMsgTypeEnum(Enum):
    DEFAULT = 0
    PARSE_ERROR = 1
    TYPE_ERROR = 2


class LaMsg(object):
    __instance = None
    @staticmethod
    def getInstance():
        if LaMsg.__instance is None:
            LaMsg()
        return LaMsg.__instance

    def __init__(self):
        if LaMsg.__instance is not None:
            raise Exception("Class LaMsg is a singleton!")
        else:
            self.rule_convention_dict = {
                # base.ebnf
                "identifier_with_subscript": "identifier with subscript",
                "identifier_alone": "identifier",
                "pi": "pi",
                # LA.ebnf
                "statements": "statement",
                "import": "import",
                "where_conditions": "where conditions",
                "where_condition": "where condition",
                "matrix_type": "matrix type",
                "vector_type": "vector type",
                "scalar_type": "scalar type",
                "set_type": "set type",
                "function_type": "function type",
                "expression": "expression",
                "if_condition": "if condition",
                "in": "in condition",
                "not_in": "not in condition",
                "not_equal": "not equal condition",
                "equal": "equal condition",
                "greater": "greater condition",
                "greater_equal": "greater or equal condition",
                "less": "less condition",
                "less_equal": "less or equal condition",
                # matrix.ebnf
                "matrix": "matrix",
                "sparse_matrix": "sparse matrix",
                "sparse_if_conditions": "if conditions for sparse matrix",
                "sparse_if_condition": "if condition for sparse matrix",
                "rows": "rows for matrix",
                "row": "row for matrix",
                "row_with_commas": "row for matrix",
                "expr_in_matrix": "expression in matrix",
                "addition_in_matrix": "addition in matrix",
                "subtraction_in_matrix": "subtraction in matrix",
                "multiplication_in_matrix": "multiplication in matrix",
                "division_in_matrix": "division in matrix",
                "number_matrix": "number matrix",
                # operators.ebnf
                "addition": "addition",
                "subtraction": "subtraction",
                "add_sub_operator": "add_sub_operator",
                "multiplication": "multiplication",
                "division": "division",
                "derivative_operator": "derivative",
                "power_operator": "power",
                "solver_operator": "solver",
                "sum_operator": "sum",
                "optimize_operator": "optimize",
                "multi_cond": "multi",
                "domain": "domain",
                "norm_operator": "norm",
                "inner_product_operator": "inner product",
                "frobenius_product_operator": "frobenius product",
                "hadamard_product_operator": "hadamard product",
                "cross_product_operator": "cross product",
                "kronecker_product_operator": "kronecker product",
                "trans_operator": "transpose",
                "function_operator": "function",
                "exp_func": "exponential",
                "log_func": "log",
                "ln_func": "ln",
                "sqrt_func": "sqrt",
                # number.ebnf
                "integer": "integer",
                "exponent": "exponent",
                "mantissa": "mantissa",
                "floating_point": "floating point",
                "double": "double",
                # trigonometry.ebnf
                "sin_func": "sin function",
                "asin_func": "asin function",
                "cos_func": "cos function",
                "acos_func": "acos function",
                "tan_func": "tan function",
                "atan_func": "atan function",
                "sinh_func": "sinh function",
                "asinh_func": "asinh function",
                "cosh_func": "cosh function",
                "acosh_func": "acosh function",
                "tanh_func": "tanh function",
                "atanh_func": "atanh function",
                "cot_func": "cot function",
                "sec_func": "sec function",
                "csc_func": "csc function",
                "atan2_func": "atan2 function",
            }
            LaMsg.__instance = self

    def get_line_desc(self, line_info):
        return "Error on line {} at column {}".format(line_info.line + 1, line_info.col + 1)

    def get_line_desc_with_col(self, line, col):
        return "Error on line {} at column {}".format(line + 1, col + 1)

    def get_pos_marker(self, column):
        return ''.join([' '] * column) + '^\n'

    def get_parse_error(self, err):
        line_info = err.buf.line_info(err.pos)
        converted_name = None
        for rule in reversed(err.stack):
            if rule in self.rule_convention_dict:
                converted_name = self.rule_convention_dict[rule]
                break
        content = "{}. Failed to parse {}: {}\n".format(self.get_line_desc(line_info), converted_name, err.message)
        content += line_info.text
        content += self.get_pos_marker(line_info.col)
        return content