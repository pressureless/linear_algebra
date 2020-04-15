from tatsu.model import NodeWalker
from tatsu.objectmodel import Node
from la_parser.la_types import *


class TypeInferenceEnum(Enum):
    INF_ADD = 0
    INF_SUB = 1
    INF_MUL = 2
    INF_DIV = 3
    INF_MATRIX_ROW = 4


class WalkTypeEnum(Enum):
    RETRIEVE_EXPRESSION = 0   # default
    RETRIEVE_VAR = 1


WALK_TYPE = "walk_type"
LHS = "left_hand_side"
CUR_INDENT = "cur_indent"
INSIDE_MATRIX = "inside_matrix"


def la_is_inside_matrix(**kwargs):
    if INSIDE_MATRIX in kwargs and kwargs[INSIDE_MATRIX] is True:
        return True
    return False


def la_remove_key(keys, **kwargs):
    if isinstance(keys, list):
        for key in keys:
            if key in kwargs:
                del kwargs[key]
    elif keys in kwargs:
        del kwargs[keys]


class TypeWalker(NodeWalker):
    def __init__(self):
        super().__init__()
        self.symtable = {}
        self.parameters = []
        self.subscripts = {}
        self.sub_name_dict = {}  # only for parameter checker
        self.node_dict = {}      # node:var_name
        self.name_cnt_dict = {}
        self.dim_dict = {}       # parameter used. h:w_i

    def generate_var_name(self, base):
        index = -1
        if base in self.name_cnt_dict:
            index = self.name_cnt_dict[base]
        index += 1
        valid = False
        ret = ""
        while not valid:
            ret = "_{}_{}".format(base, index)
            if ret not in self.symtable:
                valid = True
            index += 1
        self.name_cnt_dict[base] = index - 1
        return ret

    def walk_Node(self, node):
        print('Reached Node: ', node)

    def walk_object(self, o):
        raise Exception('Unexpected type %s walked', type(o).__name__)

    def walk_Start(self, node, **kwargs):
        self.walk(node.cond, **kwargs)
        self.walk(node.stat, **kwargs)

    ###################################################################
    def walk_WhereConditions(self, node, **kwargs):
        for cond in node.value:
            self.walk(cond, **kwargs)

    def walk_MatrixCondition(self, node, **kwargs):
        id0_info = self.walk(node.id, **kwargs)
        id0 = id0_info.content
        id1_info = self.walk(node.id1, **kwargs)
        id1 = id1_info.content
        id2_info = self.walk(node.id2, **kwargs)
        id2 = id2_info.content
        ret = node.text.split(':')
        desc = ':'.join(ret[1:len(ret)])
        element_type = ''
        if node.type:
            if node.type == 'ℝ':
                element_type = LaVarType(VarTypeEnum.REAL)
            elif node.type == 'ℤ':
                element_type = LaVarType(VarTypeEnum.INTEGER)
        la_type = LaVarType(VarTypeEnum.MATRIX, [id1, id2], desc=desc, element_type=element_type)
        self.handle_identifier(id0, la_type)
        self.update_parameters(id0)
        if isinstance(id1, str):
            self.symtable[id1] = LaVarType(VarTypeEnum.INTEGER)
            if self.contain_subscript(id0):
                self.dim_dict[id1] = [self.get_main_id(id0), 1]
            else:
                self.dim_dict[id1] = [self.get_main_id(id0), 0]
        if isinstance(id2, str):
            self.symtable[id2] = LaVarType(VarTypeEnum.INTEGER)
            if self.contain_subscript(id0):
                self.dim_dict[id2] = [self.get_main_id(id0), 2]
            else:
                self.dim_dict[id2] = [self.get_main_id(id0), 1]

    def walk_VectorCondition(self, node, **kwargs):
        id0_info = self.walk(node.id, **kwargs)
        id0 = id0_info.content
        id1_info = self.walk(node.id1, **kwargs)
        id1 = id1_info.content
        ret = node.text.split(':')
        desc = ':'.join(ret[1:len(ret)])
        element_type = ''
        if node.type:
            if node.type == 'ℝ':
                element_type = LaVarType(VarTypeEnum.REAL)
            elif node.type == 'ℤ':
                element_type = LaVarType(VarTypeEnum.INTEGER)
        la_type = LaVarType(VarTypeEnum.VECTOR, [id1], desc=desc, element_type=element_type)
        self.handle_identifier(id0, la_type)
        self.update_parameters(id0)
        if isinstance(id1, str):
            self.symtable[id1] = LaVarType(VarTypeEnum.INTEGER)
            self.dim_dict[id1] = [self.get_main_id(id0), 0]

    def walk_ScalarCondition(self, node, **kwargs):
        id0_info = self.walk(node.id, **kwargs)
        id0 = id0_info.content
        ret = node.text.split(':')
        desc = ':'.join(ret[1:len(ret)])
        la_type = LaVarType(VarTypeEnum.SCALAR, desc=desc)
        self.handle_identifier(id0, la_type)
        self.update_parameters(id0)

    def walk_SetCondition(self, node, **kwargs):
        id0_info = self.walk(node.id, **kwargs)
        id0 = id0_info.content
        ret = node.text.split(':')
        desc = ':'.join(ret[1:len(ret)])
        self.symtable[id0] = LaVarType(VarTypeEnum.SET, desc=desc)
        self.handle_identifier(id0, self.symtable[id0])
        self.update_parameters(id0)

    def update_parameters(self, identifier, **kwargs):
        if self.contain_subscript(identifier):
            arr = self.get_all_ids(identifier)
            self.parameters.append(arr[0])
        else:
            self.parameters.append(identifier)

    ###################################################################
    def walk_Statements(self, node, **kwargs):
        for stat in node.value:
            self.walk(stat, **kwargs)

    def walk_Add(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        left_type = left_info.la_type
        right_info = self.walk(node.right, **kwargs)
        right_type = right_info.la_type
        ret_type = self.type_inference(TypeInferenceEnum.INF_ADD, left_type, right_type)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        self.node_dict[node] = ret_info
        return ret_info

    def walk_Subtract(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        left_type = left_info.la_type
        right_info = self.walk(node.right, **kwargs)
        right_type = right_info.la_type
        ret_type = self.type_inference(TypeInferenceEnum.INF_SUB, left_type, right_type)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        self.node_dict[node] = ret_info
        return ret_info

    def walk_Multiply(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        left_type = left_info.la_type
        right_info = self.walk(node.right, **kwargs)
        right_type = right_info.la_type
        ret_type = self.type_inference(TypeInferenceEnum.INF_MUL, left_type, right_type)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        self.node_dict[node] = ret_info
        return ret_info

    def walk_Divide(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        left_type = left_info.la_type
        right_info = self.walk(node.right, **kwargs)
        right_type = right_info.la_type
        ret_type = self.type_inference(TypeInferenceEnum.INF_DIV, left_type, right_type)
        ret_info = NodeInfo(ret_type, symbols=left_info.symbols.union(right_info.symbols))
        self.node_dict[node] = ret_info
        return ret_info

    def walk_Assignment(self, node, **kwargs):
        id0_info = self.walk(node.left, **kwargs)
        id0 = id0_info.content
        kwargs[LHS] = id0
        right_info = self.walk(node.right, **kwargs)
        right_type = right_info.la_type
        la_remove_key(LHS, **kwargs)
        # y_i = stat
        if self.contain_subscript(id0):
            left_ids = self.get_all_ids(id0)
            left_subs = left_ids[1]
            sequence = left_ids[0]    #y
            if len(left_subs) == 2: # matrix
                for symbol in right_info.symbols:
                    if left_subs[0] in symbol and left_subs[1] in symbol:
                        main_id = self.get_main_id(symbol)
                        dim = self.symtable[main_id].dimensions
                        break
                self.symtable[sequence] = LaVarType(VarTypeEnum.MATRIX, dimensions=dim, element_type=right_type)
            elif len(left_subs) == 1: # sequence
                for symbol in right_info.symbols:
                    if left_subs[0] in symbol:
                        main_id = self.get_main_id(symbol)
                        dim = self.symtable[main_id].dimensions[0]
                        break
                self.symtable[sequence] = LaVarType(VarTypeEnum.SEQUENCE, dimensions=[dim], element_type=right_type)
        else:
            self.symtable[id0] = right_type

        self.node_dict[node] = right_info
        return right_info

    def walk_Summation(self, node, **kwargs):
        subs = []
        for sub in node.sub:
            sub_info = self.walk(sub)
            subs.append(sub_info.content)
        new_id = self.generate_var_name("sum")
        ret_info = self.walk(node.exp, **kwargs)
        ret_type = ret_info.la_type
        self.symtable[new_id] = ret_type
        ret_info.symbol = new_id
        self.node_dict[node] = ret_info
        return ret_info

    def walk_Determinant(self, node, **kwargs):
        value_info = self.walk(node.value, **kwargs)
        ret_type = LaVarType(VarTypeEnum.SCALAR)
        node_info = NodeInfo(ret_type, symbols=value_info.symbols)
        self.node_dict[node] = node_info
        return node_info

    def walk_Power(self, node, **kwargs):
        base_info = self.walk(node.base, **kwargs)
        symbols = base_info.symbols
        if node.t:
            assert base_info.la_type.var_type == VarTypeEnum.MATRIX
            node_type = LaVarType(VarTypeEnum.MATRIX,
                                  dimensions=[base_info.la_type.dimensions[1], base_info.la_type.dimensions[0]])
        elif node.r:
            assert base_info.la_type.var_type == VarTypeEnum.MATRIX
            assert base_info.la_type.dimensions[0] == base_info.la_type.dimensions[1]
            node_type = LaVarType(VarTypeEnum.MATRIX,
                                  dimensions=[base_info.la_type.dimensions[1], base_info.la_type.dimensions[0]])
        else:
            power_info = self.walk(node.power, **kwargs)
            symbols += power_info.symbols
            node_type = power_info.la_type
        return NodeInfo(node_type, symbols=symbols)

    def walk_Solver(self, node, **kwargs):
        left_info = self.walk(node.left, **kwargs)
        right_info = self.walk(node.right, **kwargs)
        assert left_info.la_type.var_type == VarTypeEnum.MATRIX
        assert right_info.la_type.var_type == VarTypeEnum.MATRIX or right_info.la_type.var_type == VarTypeEnum.VECTOR
        node_type = None
        if left_info.la_type.var_type == VarTypeEnum.MATRIX:
            assert left_info.la_type.dimensions[0] == right_info.la_type.dimensions[0]
            if right_info.la_type.var_type == VarTypeEnum.MATRIX:
                node_type = LaVarType(VarTypeEnum.MATRIX,
                                      dimensions=[left_info.la_type.dimensions[1], right_info.la_type.dimensions[1]])
            elif right_info.la_type.var_type == VarTypeEnum.VECTOR:
                node_type = LaVarType(VarTypeEnum.VECTOR,
                                      dimensions=[left_info.la_type.dimensions[1]])
        return NodeInfo(node_type, symbols=left_info.symbols.union(right_info.symbols))

    def walk_Transpose(self, node, **kwargs):
        f_info = self.walk(node.f, **kwargs)
        assert f_info.la_type.var_type == VarTypeEnum.MATRIX
        node_type = LaVarType(VarTypeEnum.MATRIX, dimensions=[f_info.la_type.dimensions[1], f_info.la_type.dimensions[0]])
        node_info = NodeInfo(node_type, symbols=f_info.symbols)
        return node_info

    def walk_IdentifierSubscript(self, node, **kwargs):
        node_type = LaVarType(VarTypeEnum.INVALID)
        right = []
        for value in node.right:
            v_info = self.walk(value)
            right.append(v_info.content)
        left_info = self.walk(node.left, **kwargs)
        content = left_info.content + '_' + ''.join(right)
        if left_info.content in self.symtable:
            node_type = self.symtable[left_info.content].element_type
        node_info = NodeInfo(node_type, content, {content})
        self.node_dict[node] = node_info
        return node_info

    def walk_IdentifierAlone(self, node, **kwargs):
        node_type = LaVarType(VarTypeEnum.INVALID)
        if node.value in self.symtable:
            node_type = self.symtable[node.value]
        node_info = NodeInfo(node_type, node.value, {node.value})
        self.node_dict[node] = node_info
        return node_info

    def walk_Factor(self, node, **kwargs):
        node_info = None
        if node.id:
            id0_info = self.walk(node.id, **kwargs)
            id0 = id0_info.content
            id0 = self.get_main_id(id0)
            assert self.symtable.get(id0) is not None, ("error: no symbol:{}".format(id0))
            node_info = NodeInfo(id0_info.la_type, id0, id0_info.symbols)
            # node_info = NodeInfo(self.symtable[id0], id0, id0_info.symbols)
        elif node.num:
            node_info = self.walk(node.num, **kwargs)
        elif node.sub:
            node_info = self.walk(node.sub, **kwargs)
        elif node.m:
            node_info = self.walk(node.m, **kwargs)
        elif node.f:
            node_info = self.walk(node.f, **kwargs)
        elif node.op:
            node_info = self.walk(node.op, **kwargs)
        elif node.s:
            node_info = self.walk(node.s, **kwargs)
        self.node_dict[node] = node_info
        return node_info

    def walk_Number(self, node, **kwargs):
        node_value = self.walk(node.value, **kwargs)
        node_info = NodeInfo(LaVarType(VarTypeEnum.SCALAR), content=node_value)
        self.node_dict[node] = node_info
        return node_info

    def walk_Integer(self, node, **kwargs):
        value = ''.join(node.value)
        node_type = LaVarType(VarTypeEnum.INTEGER)
        node_info = NodeInfo(node_type, content=int(value))
        self.node_dict[node] = node_info
        return node_info

    def walk_SparseMatrix(self, node, **kwargs):
        if LHS in kwargs:
            lhs = kwargs[LHS]
        id1_info = self.walk(node.id1, **kwargs)
        id1 = id1_info.content
        id2_info = self.walk(node.id2, **kwargs)
        id2 = id2_info.content
        matrix_attrs = MatrixAttrs(sparse=True)
        matrix_attrs.index_var = self.generate_var_name("{}ij".format(lhs))
        matrix_attrs.value_var = self.generate_var_name("{}vals".format(lhs))
        new_id = self.generate_var_name('sparse')
        la_type = LaVarType(VarTypeEnum.MATRIX, attrs=matrix_attrs, dimensions=[id1, id2])
        self.symtable[new_id] = la_type
        node_info = NodeInfo(la_type)
        node_info.symbol = new_id
        self.node_dict[node] = node_info
        return node_info

    def walk_Matrix(self, node, **kwargs):
        kwargs[INSIDE_MATRIX] = True
        node_info = self.walk(node.value, **kwargs)
        # check matrix validity
        rows = len(node_info.content)
        cols = 0
        sparse = False
        for row in node_info.content:
            for col in row:
                if col.var_type == VarTypeEnum.MATRIX or col.var_type == VarTypeEnum.VECTOR:
                    sparse = True
            if len(row) > cols:
                cols = len(row)
        m_attr = MatrixAttrs(sparse=sparse)
        node_type = LaVarType(VarTypeEnum.MATRIX, dimensions=[rows, cols], attrs=m_attr)
        node_info = NodeInfo(node_type)
        if LHS in kwargs:
            lhs = kwargs[LHS]
            new_id = self.generate_var_name(lhs)
            self.symtable[new_id] = LaVarType(VarTypeEnum.MATRIX, dimensions=[rows, cols])
            node_info.symbol = new_id
            self.node_dict[node] = node_info
        self.node_dict[node] = node_info
        return node_info

    def walk_MatrixRows(self, node, **kwargs):
        ret_info = None
        rows = []
        symbols = set()
        if node.rs:
            ret_info = self.walk(node.rs, **kwargs)
            rows = rows + ret_info.content
            symbols = ret_info.symbols
        if node.r:
            r_info = self.walk(node.r, **kwargs)
            if ret_info is None:
                ret_info = r_info
                ret_info.content = [ret_info.content]
            else:
                rows.append(r_info.content)
                ret_info.content = rows
            ret_info.symbols = symbols.union(r_info.symbols)
        self.node_dict[node] = ret_info
        return ret_info

    def walk_MatrixRow(self, node, **kwargs):
        ret_info = None
        items = []
        symbols = set()
        if node.rc:
            ret_info = self.walk(node.rc, **kwargs)
            items = items + ret_info.content
            symbols = ret_info.symbols
        if node.exp:
            exp_info = self.walk(node.exp, **kwargs)
            if ret_info is None:
                ret_info = exp_info
                ret_info.content = [exp_info.la_type]
            else:
                new_type = self.type_inference(TypeInferenceEnum.INF_MATRIX_ROW, ret_info.la_type, exp_info.la_type)
                ret_info.la_type = new_type
                items.append(exp_info.la_type)
                ret_info.content = items
            ret_info.symbols = symbols.union(exp_info.symbols)
        self.node_dict[node] = ret_info
        return ret_info

    def walk_MatrixRowCommas(self, node, **kwargs):
        ret_info = None
        items = []
        symbols = set()
        if node.value:
            ret_info = self.walk(node.value, **kwargs)
            items = items + ret_info.content
            symbols = ret_info.symbols
        if node.exp:
            exp_info = self.walk(node.exp, **kwargs)
            if ret_info is None:
                ret_info = exp_info
                ret_info.content = [exp_info.la_type]
            else:
                new_type = self.type_inference(TypeInferenceEnum.INF_MATRIX_ROW, ret_info.la_type, exp_info.la_type)
                ret_info.la_type = new_type
                items.append(exp_info.la_type)
                ret_info.content = items
            ret_info.symbols = symbols.union(exp_info.symbols)
        self.node_dict[node] = ret_info
        return ret_info

    def walk_ExpInMatrix(self, node, **kwargs):
        ret_info = self.walk(node.value, **kwargs)
        self.node_dict[node] = ret_info
        return ret_info

    ###################################################################
    def type_inference(self, op, left_type, right_type):
        ret_type = None
        if op == TypeInferenceEnum.INF_ADD or op == TypeInferenceEnum.INF_SUB:
            assert left_type.var_type == right_type.var_type
            if left_type.var_type == VarTypeEnum.MATRIX:
                assert left_type.dimensions[0] == right_type.dimensions[0] and left_type.dimensions[1] == right_type.dimensions[1], 'error: dimension mismatch'
            elif left_type.var_type == VarTypeEnum.VECTOR:
                assert left_type.dimensions[0] == right_type.dimensions[0], 'error: dimension mismatch'
            ret_type = left_type
        elif op == TypeInferenceEnum.INF_MUL:
            assert left_type.var_type is not VarTypeEnum.SEQUENCE and right_type.var_type is not VarTypeEnum.SEQUENCE, 'error: sequence can not be operated'
            if left_type.var_type == VarTypeEnum.SCALAR:
                ret_type = right_type
            elif left_type.var_type == VarTypeEnum.INTEGER:
                ret_type = right_type
            elif left_type.var_type == VarTypeEnum.MATRIX:
                if right_type.var_type == VarTypeEnum.SCALAR:
                    ret_type = left_type
                if right_type.var_type == VarTypeEnum.INTEGER:
                    ret_type = left_type
                elif right_type.var_type == VarTypeEnum.MATRIX:
                    assert left_type.dimensions[1] == right_type.dimensions[0], 'error: dimension mismatch'
                    ret_type = LaVarType(VarTypeEnum.MATRIX, [left_type.dimensions[0], right_type.dimensions[1]])
                elif right_type.var_type == VarTypeEnum.VECTOR:
                    assert left_type.dimensions[1] == right_type.dimensions[0], 'error: dimension mismatch'
                    ret_type = LaVarType(VarTypeEnum.VECTOR, [left_type.dimensions[0]])
            elif left_type.var_type == VarTypeEnum.VECTOR:
                if right_type.var_type == VarTypeEnum.SCALAR:
                    ret_type = left_type
                if right_type.var_type == VarTypeEnum.INTEGER:
                    ret_type = left_type
                elif right_type.var_type == VarTypeEnum.MATRIX:
                    assert 1 == right_type.dimensions[0], 'error: dimension mismatch'
                    ret_type = LaVarType(VarTypeEnum.MATRIX, [left_type.dimensions[0], right_type.dimensions[1]])
                elif right_type.var_type == VarTypeEnum.VECTOR:
                    assert left_type.dimensions[1] == right_type.dimensions[0], 'error: dimension mismatch'
                    ret_type = LaVarType(VarTypeEnum.MATRIX, [left_type.dimensions[0]])
        elif op == TypeInferenceEnum.INF_DIV:
            assert (left_type.var_type == VarTypeEnum.SCALAR or left_type.var_type == VarTypeEnum.INTEGER), 'error: type mismatch'
            assert (right_type.var_type == VarTypeEnum.SCALAR or right_type.var_type == VarTypeEnum.INTEGER), 'error: type mismatch'
            ret_type = LaVarType(VarTypeEnum.SCALAR)
        elif op == TypeInferenceEnum.INF_MATRIX_ROW:
            # assert left_type.var_type == right_type.var_type
            ret_type = left_type
        return ret_type

    def contain_subscript(self, identifier):
        return identifier.find("_") != -1

    def get_all_ids(self, identifier):
        res = identifier.split('_')
        subs = []
        for index in range(len(res[1])):
            subs.append(res[1][index])
        return [res[0], subs]

    def get_main_id(self, identifier):
        if self.contain_subscript(identifier):
            ret = self.get_all_ids(identifier)
            return ret[0]
        return identifier

    # handle subscripts only (where block)
    def handle_identifier(self, identifier, id_type):
        if self.contain_subscript(identifier):
            arr = self.get_all_ids(identifier)
            new_var_name = None
            for val in arr[1]:
                if val in self.sub_name_dict:
                    new_var_name = self.sub_name_dict[val]
                else:
                    new_var_name = self.generate_var_name("dim")
                    self.sub_name_dict[val] = new_var_name
                    self.dim_dict[new_var_name] = [arr[0], 0]
                if val in self.subscripts:
                    var_list = self.subscripts[val]
                    var_list.append(arr[0])
                    self.subscripts[val] = var_list
                else:
                    # first sequence
                    self.subscripts[val] = [arr[0]]
            self.symtable[arr[0]] = LaVarType(VarTypeEnum.SEQUENCE, dimensions=[new_var_name], element_type=id_type,
                                              desc=id_type.desc)
        else:
            self.symtable[identifier] = id_type
