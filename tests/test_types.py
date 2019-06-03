import nose

import claripy

import angr
from angr.sim_type import SimTypeFunction, SimTypeInt, SimTypePointer, SimTypeChar, SimStruct, SimTypeFloat, SimUnion, SimTypeDouble, SimTypeLongLong, SimTypeLong, SimTypeNum
from angr.utils.library import convert_cproto_to_py


def test_type_annotation():
    my_ty = angr.sim_type.SimTypeTop()
    ptr = claripy.BVS('ptr', 32).annotate(angr.type_backend.TypeAnnotation(angr.sim_type.SimTypePointer(my_ty, label=[])))
    ptroffset = ptr + 4

    bt = angr.type_backend.TypeBackend()
    tv = bt.convert(ptroffset)
    nose.tools.assert_is(tv.ty.pts_to, my_ty)
    nose.tools.assert_true(claripy.is_true(tv.ty.offset == 4))


def test_cproto_conversion():

    # A normal function declaration
    cproto_0 = "int main(int argc, char** argv);"
    pyproto_name, pyproto, the_str = convert_cproto_to_py(cproto_0)

    nose.tools.assert_equal(pyproto_name, "main")
    nose.tools.assert_is_instance(pyproto, SimTypeFunction)
    nose.tools.assert_is_instance(pyproto.args[0], SimTypeInt)
    nose.tools.assert_is_instance(pyproto.args[1], SimTypePointer)
    nose.tools.assert_is_instance(pyproto.args[1].pts_to.pts_to, SimTypeChar)
    nose.tools.assert_is_instance(pyproto.returnty, SimTypeInt)

    # Directly comparing the strings... how bad can I be?
    nose.tools.assert_equal(the_str,
                            '# int main(int argc, char** argv);\n"main": SimTypeFunction([SimTypeInt(signed=True, label=None), SimTypePointer(SimTypePointer(SimTypeChar(label=None), label=None, offset=0), label=None, offset=0)], SimTypeInt(signed=True, label=None), label=None),')

    # A bad function declaration
    cproto_1 = "int bad(xxxxxxx);"
    pyproto_name, pyproto, the_str = convert_cproto_to_py(cproto_1)  # pylint:disable=unused-variable

    nose.tools.assert_equal(pyproto_name, "bad")
    nose.tools.assert_is(pyproto, None)

    # A even worse function declaration
    # Special thanks to @schieb, see GitHub PR #958
    cproto_2 = "__attribute__ ((something)) void foo(void);"
    pyproto_name, pyproto, the_str = convert_cproto_to_py(cproto_2)  # pylint:disable=unused-variable

    nose.tools.assert_equal(pyproto_name, "foo")

def test_struct_deduplication():
    angr.types.define_struct('struct ahdr { int a ;}')
    angr.types.define_struct('struct bhdr { int b ;}')
    angr.types.define_struct('struct chdr { int c ;}')
    angr.types.register_types(angr.types.parse_types('typedef struct ahdr ahdr;'))
    angr.types.register_types(angr.types.parse_types('typedef struct bhdr bhdr;'))
    angr.types.register_types(angr.types.parse_types('typedef struct chdr chdr;'))
    dhdr = angr.types.define_struct('struct dhdr { struct ahdr a; struct bhdr b; struct chdr c;}')
    assert dhdr.fields['a'].fields

def test_parse_type():
    int_ptr = angr.types.parse_type('int *')
    nose.tools.assert_is_instance(int_ptr, SimTypePointer)
    nose.tools.assert_is_instance(int_ptr.pts_to, SimTypeInt)

    struct_abcd = angr.types.parse_type('struct abcd { char c; float f; }')
    nose.tools.assert_is_instance(struct_abcd, SimStruct)
    nose.tools.assert_equal(struct_abcd.name, 'abcd')
    nose.tools.assert_true(len(struct_abcd.fields) == 2)
    nose.tools.assert_is_instance(struct_abcd.fields['c'], SimTypeChar)
    nose.tools.assert_is_instance(struct_abcd.fields['f'], SimTypeFloat)

    union_dcba = angr.types.parse_type('union dcba { double d; long long int lli; }')
    nose.tools.assert_is_instance(union_dcba, SimUnion)
    nose.tools.assert_equal(union_dcba.name, 'dcba')
    nose.tools.assert_true(len(union_dcba.members) == 2)
    nose.tools.assert_is_instance(union_dcba.members['d'], SimTypeDouble)
    nose.tools.assert_is_instance(union_dcba.members['lli'], SimTypeLongLong)

    struct_llist = angr.types.parse_type('struct llist { int data; struct llist * next; }')
    nose.tools.assert_is_instance(struct_llist, SimStruct)
    nose.tools.assert_equal(struct_llist.name, 'llist')
    nose.tools.assert_true(len(struct_llist.fields) == 2)
    nose.tools.assert_is_instance(struct_llist.fields['data'], SimTypeInt)
    nose.tools.assert_is_instance(struct_llist.fields['next'], SimTypePointer)
    nose.tools.assert_is_instance(struct_llist.fields['next'].pts_to, SimStruct)
    nose.tools.assert_equal(struct_llist.fields['next'].pts_to.name, 'llist')

def test_parse_type_no_basic_types():
    time_t = angr.types.parse_type('time_t')
    nose.tools.assert_is_instance(time_t, SimTypeLong)

    byte = angr.types.parse_type('byte')
    nose.tools.assert_is_instance(byte, SimTypeNum)
    nose.tools.assert_true(byte.size, 8)
    nose.tools.assert_false(byte.signed)


if __name__ == '__main__':
    test_type_annotation()
    test_cproto_conversion()
    test_struct_deduplication()
    test_parse_type()
    test_parse_type_no_basic_types()
