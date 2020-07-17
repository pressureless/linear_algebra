from enum import Enum, IntEnum


class VarTypeEnum(Enum):
    INVALID = 0
    # LA types
    SEQUENCE = 1
    MATRIX = 2
    VECTOR = 3
    SET = 4
    SCALAR = 5
    FUNCTION = 6


class LaVarType(object):
    def __init__(self, var_type, desc=None, element_type=None, symbol=None):
        super().__init__()
        self.var_type = var_type
        self.desc = desc   # only parameters need description
        self.element_type = element_type
        self.symbol = symbol

    def is_dim_constant(self):
        constant = False
        if self.var_type == VarTypeEnum.SEQUENCE:
            if isinstance(self.size, int):
                constant = True
        elif self.var_type == VarTypeEnum.MATRIX:
            if isinstance(self.rows, int) and isinstance(self.cols, int):
                constant = True
        elif self.var_type == VarTypeEnum.VECTOR:
            if isinstance(self.rows, int):
                constant = True
        else:
            constant = True
        return constant

    def is_matrix(self):
        return self.var_type == VarTypeEnum.MATRIX

    def is_sequence(self):
        return self.var_type == VarTypeEnum.SEQUENCE

    def is_vector(self):
        return self.var_type == VarTypeEnum.VECTOR

    def is_scalar(self):
        return self.var_type == VarTypeEnum.SCALAR

    def is_set(self):
        return self.var_type == VarTypeEnum.SET

    def is_function(self):
        return self.var_type == VarTypeEnum.FUNCTION

    def is_same_type(self, other):
        same = False
        if self.var_type == other.var_type:
            if self.var_type == VarTypeEnum.SEQUENCE:
                same = self.element_type.is_same_type(other.element_type.is_same_type)
            elif self.var_type == VarTypeEnum.MATRIX:
                same = self.rows == other.rows and self.cols == other.cols
            elif self.var_type == VarTypeEnum.VECTOR:
                same = self.rows == other.rows
            else:
                same = True
        return same


class SequenceType(LaVarType):
    def __init__(self, size=0, desc=None, element_type=None, symbol=None):
        LaVarType.__init__(self, VarTypeEnum.SEQUENCE, desc, element_type, symbol)
        self.size = size


class MatrixType(LaVarType):
    def __init__(self, rows=0, cols=0, desc=None, element_type=None, symbol=None, need_exp=False, diagonal=False, sparse=False, block=False, subs=[], list_dim=None, index_var=None, value_var=None, item_types = None):
        LaVarType.__init__(self, VarTypeEnum.MATRIX, desc, element_type, symbol)
        self.rows = rows
        self.cols = cols
        # attributes
        self.need_exp = need_exp      # need expression
        self.diagonal = diagonal
        self.subs = subs
        # block matrix
        self.block = block
        self.list_dim = list_dim      # used by block mat
        self.item_types = item_types  # type array
        # sparse matrix
        self.sparse = sparse
        self.index_var = index_var    # used by sparse mat
        self.value_var = value_var    # used by sparse mat


class VectorType(LaVarType):
    def __init__(self, rows=0, desc=None, element_type=None, symbol=None):
        LaVarType.__init__(self, VarTypeEnum.VECTOR, desc, element_type, symbol)
        self.rows = rows
        self.cols = 1


class SetType(LaVarType):
    def __init__(self, size=0, desc=None, element_type=None, symbol=None, int_list=None):
        LaVarType.__init__(self, VarTypeEnum.SET, desc, element_type, symbol)
        self.size = size
        self.int_list = int_list     # whether the element is real number or integer


class ScalarType(LaVarType):
    def __init__(self, is_int=False, desc=None, element_type=None, symbol=None):
        LaVarType.__init__(self, VarTypeEnum.SCALAR, desc, element_type, symbol)
        self.is_int = is_int


class FunctionType(LaVarType):
    def __init__(self, desc=None, symbol=None, params=[], ret=None):
        LaVarType.__init__(self, VarTypeEnum.FUNCTION, desc, symbol)
        self.params = params
        self.ret = ret


class SummationAttrs(object):
    def __init__(self, subs=None, var_list=None):
        super().__init__()
        self.subs = subs
        self.var_list = var_list


class NodeInfo(object):
    def __init__(self, la_type=None, content=None, symbols=set(), ir=None):
        super().__init__()
        self.la_type = la_type
        self.content = content
        self.symbols = symbols  # symbols covered by the node
        self.ir = ir


class CodeNodeInfo(object):
    def __init__(self, content=None, pre_list=[]):
        super().__init__()
        self.content = content
        self.pre_list = pre_list


class Identifier(object):
    def __init__(self, main_id='', subs=[]):
        super().__init__()
        self.main_id = main_id
        self.subs = subs

    def contain_subscript(self):
        return len(self.subs) > 0

    def get_all_ids(self):
        return [self.main_id, self.subs]

    def get_main_id(self):
        return self.main_id