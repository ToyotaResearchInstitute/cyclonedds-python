import array
import struct
import pytest

from dataclasses import dataclass

from cyclonedds.idl import IdlStruct, IdlBitmask, IdlUnion, IdlEnum
from cyclonedds.idl._support import Buffer, Endianness
import cyclonedds.idl._machinery as mc
import cyclonedds.idl.types as tp


class A(IdlEnum):
    V1 = 0xca
    V2 = 0xef


@dataclass
class B(IdlBitmask):
    V1: bool
    V2: bool


@dataclass
class C(IdlStruct):
    A: tp.uint8
    B: tp.uint16


class D(IdlUnion, discriminator=bool):
    A: tp.case[True, tp.uint16]
    B: tp.default[tp.int8]



def test_all_machine_serializers():
    b = Buffer()
    b.set_endianness(Endianness.Little)

    m = mc.CharMachine()
    m.serialize(b, "a")
    m.serialize(b, "b")
    assert b.asbytes() == b"ab"

    m = mc.PrimitiveMachine(tp.uint8)
    b.zero_out()
    b.seek(0)
    m.serialize(b, 0xab)
    assert b.asbytes() == b"\xab"

    m2 = mc.SequenceMachine(m, add_size_header=False)
    b.zero_out()
    b.seek(0)
    m2.serialize(b, [0x0a, 0x0b])
    assert b.asbytes() == b"\x02\x00\x00\x00\x0a\x0b"

    m2 = mc.SequenceMachine(m, add_size_header=True)
    b.zero_out()
    b.seek(0)
    m2.serialize(b, [0x0a, 0x0b])
    assert b.asbytes() == b"\x06\x00\x00\x00\x02\x00\x00\x00\x0a\x0b"

    m2 = mc.ArrayMachine(m, 2, add_size_header=False)
    b.zero_out()
    b.seek(0)
    m2.serialize(b, [0x0a, 0x0b])
    assert b.asbytes() == b"\x0a\x0b"

    m2 = mc.ArrayMachine(m, 2, add_size_header=True)
    b.zero_out()
    b.seek(0)
    m2.serialize(b, [0x0a, 0x0b])
    assert b.asbytes() == b"\x02\x00\x00\x00\x0a\x0b"

    m2 = mc.PlainCdrV2SequenceOfPrimitiveMachine(tp.uint8)
    b.seek(0)
    m2.serialize(b, [0x0a, 0x0b])
    assert b.asbytes() == b"\x02\x00\x00\x00\x0a\x0b"

    m2 = mc.PlainCdrV2ArrayOfPrimitiveMachine(tp.uint8, 2)
    b.zero_out()
    b.seek(0)
    m2.serialize(b, [0x0a, 0x0b])
    assert b.asbytes() == b"\x0a\x0b"

    m2 = mc.ByteArrayMachine(3)
    b.zero_out()
    b.seek(0)
    m2.serialize(b, bytearray([1,2,3]))
    m2.serialize(b, b"\x03\x02\x01")
    assert b.asbytes() == b"\x01\x02\x03\x03\x02\x01"

    m2 = mc.EnumMachine(A)
    b.zero_out()
    b.seek(0)
    m2.serialize(b, A.V2)
    m2.serialize(b, A.V1)
    assert b.asbytes() == b"\xef\x00\x00\x00\xca\x00\x00\x00"

    m2 = mc.BitBoundEnumMachine(A, 8)
    b.zero_out()
    b.seek(0)
    m2.serialize(b, A.V2)
    m2.serialize(b, A.V1)
    assert b.asbytes() == b"\xef\xca"

    m2 = mc.BitBoundEnumMachine(A, 16)
    b.zero_out()
    b.seek(0)
    m2.serialize(b, A.V2)
    m2.serialize(b, A.V1)
    assert b.asbytes() == b"\xef\x00\xca\x00"

    m2 = mc.BitMaskMachine(B, 8)
    b.zero_out()
    b.seek(0)
    m2.serialize(b, B(True, False))
    m2.serialize(b, B(False, True))
    assert b.asbytes() == b"\x01\x02"

    m2 = mc.BitMaskMachine(B, 16)
    b.zero_out()
    b.seek(0)
    m2.serialize(b, B(True, False))
    m2.serialize(b, B(False, True))
    assert b.asbytes() == b"\x01\x00\x02\x00"

    m2 = mc.OptionalMachine(m)
    b.zero_out()
    b.seek(0)
    m2.serialize(b, None)
    m2.serialize(b, 0x12)
    m2.serialize(b, 0)
    assert b.asbytes() == b"\x00\x01\x12\x01\x00"

    m2 = mc.StringMachine()
    b.zero_out()
    b.seek(0)
    m2.serialize(b, "ab")
    assert b.asbytes() == b"\x03\x00\x00\x00ab\x00"

    m3 = mc.StructMachine(C, {
        'A': mc.PrimitiveMachine(tp.uint8),
        'B': mc.PrimitiveMachine(tp.uint16)
    }, [])
    b.zero_out()
    b.seek(0)
    m3.serialize(b, C(0x0a, 0x0b))
    assert b.asbytes() == b"\x0a\x00\x0b\x00"

    m3 = mc.DelimitedCdrAppendableStructMachine(C, {
        'A': mc.PrimitiveMachine(tp.uint8),
        'B': mc.PrimitiveMachine(tp.uint16)
    }, [])
    b.zero_out()
    b.seek(0)
    m3.serialize(b, C(0x0a, 0x0b))
    assert b.asbytes() == b"\x04\x00\x00\x00\x0a\x00\x0b\x00"

    m3 = mc.PLCdrMutableStructMachine(C, [
        mc.MutableMember(
            'A', key=False, optional=True, lentype=mc.LenType.OneByte,
            must_understand=True, memberid=1, machine=mc.PrimitiveMachine(tp.uint8)
        ),
        mc.MutableMember(
            'B', key=False, optional=True, lentype=mc.LenType.TwoByte,
            must_understand=True, memberid=2, machine=mc.PrimitiveMachine(tp.uint16)
        )
    ])

    b.zero_out()
    b.seek(0)
    m3.serialize(b, C(0x0a, 0x0b))
    assert b.asbytes() == (
        b"\x0e\x00\x00\x00"
        b"\x01\x00\x00\x80"
        b"\x0a\x00\x00\x00"
        b"\x02\x00\x00\x90"
        b"\x0b\x00"
    )

    b.zero_out()
    b.seek(0)
    m3.serialize(b, C(None, 0x0b))
    assert b.asbytes() == (
        b"\x06\x00\x00\x00"
        b"\x02\x00\x00\x90"
        b"\x0b\x00"
    )

    b.zero_out()
    b.seek(0)
    m3.serialize(b, C(None, None))
    assert b.asbytes() == b"\x00\x00\x00\x00"

    m3 = mc.UnionMachine(D, mc.PrimitiveMachine(bool), {
        True: mc.PrimitiveMachine(tp.uint16),
    }, default_case=mc.PrimitiveMachine(tp.uint8))

    b.zero_out()
    b.seek(0)
    m3.serialize(b, D(A=0x1234))
    m3.serialize(b, D(B=0x77))
    assert b.asbytes() == b"\x01\x00\x34\x12\x00\x77"

    m3 = mc.DelimitedCdrAppendableUnionMachine(D, mc.PrimitiveMachine(bool), {
        True: mc.PrimitiveMachine(tp.uint16),
    }, default_case=mc.PrimitiveMachine(tp.uint8))

    b.zero_out()
    b.seek(0)
    m3.serialize(b, D(A=0x1234))
    m3.serialize(b, D(B=0x77))
    assert b.asbytes() == b"\x04\x00\x00\x00\x01\x00\x34\x12\x02\x00\x00\x00\x00\x77"


# All array.array-compatible primitive typecodes used by the IDL machinery.
_SEQUENCE_CASES = [
    ('b', [0, -1, 127, -128]),
    ('B', [0, 1, 127, 255]),
    ('h', [0, -1, 32767, -32768]),
    ('H', [0, 1, 32767, 65535]),
    ('i', [0, -1, 2**31 - 1, -(2**31)]),
    ('I', [0, 1, 2**31 - 1, 2**32 - 1]),
    ('q', [0, -1, 2**63 - 1, -(2**63)]),
    ('Q', [0, 1, 2**63 - 1, 2**64 - 1]),
    ('f', [0.0, 1.5, -1.5, 3.14]),
    ('d', [0.0, 1.5, -1.5, 3.14159265358979]),
]


@pytest.mark.parametrize("code,values", _SEQUENCE_CASES)
def test_write_read_sequence_roundtrip_native(code, values):
    """write_sequence followed by read_sequence returns the original values."""
    b = Buffer()
    b.write_sequence(code, values)
    b.seek(0)
    result = b.read_sequence(code, len(values))
    if code in ('f',):
        assert result == pytest.approx(values, rel=1e-6)
    else:
        assert result == values


@pytest.mark.parametrize("code,values", _SEQUENCE_CASES)
def test_write_read_sequence_roundtrip_non_native(code, values):
    """Round-trip is correct when buffer endianness is opposite to the host."""
    non_native = Endianness.Big if Endianness.native() == Endianness.Little else Endianness.Little
    b = Buffer()
    b.set_endianness(non_native)
    b.write_sequence(code, values)
    b.seek(0)
    result = b.read_sequence(code, len(values))
    if code in ('f',):
        assert result == pytest.approx(values, rel=1e-6)
    else:
        assert result == values


@pytest.mark.parametrize("code,values", _SEQUENCE_CASES)
def test_write_sequence_matches_struct_little_endian(code, values):
    """write_sequence produces the same bytes as struct.pack with '<' prefix."""
    b = Buffer()
    b.set_endianness(Endianness.Little)
    b.write_sequence(code, values)
    expected = struct.pack(f"<{len(values)}{code}", *values)
    assert b.asbytes() == expected


@pytest.mark.parametrize("code,values", _SEQUENCE_CASES)
def test_write_sequence_matches_struct_big_endian(code, values):
    """write_sequence produces the same bytes as struct.pack with '>' prefix."""
    b = Buffer()
    b.set_endianness(Endianness.Big)
    b.write_sequence(code, values)
    expected = struct.pack(f">{len(values)}{code}", *values)
    assert b.asbytes() == expected


def test_write_sequence_uint8_special_case():
    """'B' (uint8) fast path produces identical bytes to the generic array path."""
    values = list(range(256))
    b_special = Buffer()
    b_special.write_sequence('B', values)

    b_generic = Buffer()
    a = array.array('B', values)
    b_generic.write_bytes(a.tobytes())

    assert b_special.asbytes() == b_generic.asbytes()


@pytest.mark.parametrize("idl_type,code,values", [
    (tp.uint16, 'H', [0x0102, 0x0304, 0x0506]),
    (tp.int32,  'i', [1, -1, 2**16]),
    (tp.float64,'d', [1.0, -1.0, 0.5]),
])
def test_plain_cdr_v2_array_roundtrip(idl_type, code, values):
    """PlainCdrV2ArrayOfPrimitiveMachine serializes and deserializes correctly."""
    m = mc.PlainCdrV2ArrayOfPrimitiveMachine(idl_type, len(values))
    b = Buffer()
    b.set_endianness(Endianness.Little)
    m.serialize(b, values)
    b.seek(0)
    result = m.deserialize(b)
    if code == 'd':
        assert result == pytest.approx(values)
    else:
        assert result == values


@pytest.mark.parametrize("idl_type,code,values", [
    (tp.uint16, 'H', [0x0102, 0x0304, 0x0506]),
    (tp.int32,  'i', [1, -1, 2**16]),
    (tp.float64,'d', [1.0, -1.0, 0.5]),
])
def test_plain_cdr_v2_sequence_roundtrip(idl_type, code, values):
    """PlainCdrV2SequenceOfPrimitiveMachine serializes and deserializes correctly."""
    m = mc.PlainCdrV2SequenceOfPrimitiveMachine(idl_type)
    b = Buffer()
    b.set_endianness(Endianness.Little)
    m.serialize(b, values)
    b.seek(0)
    result = m.deserialize(b)
    if code == 'd':
        assert result == pytest.approx(values)
    else:
        assert result == values
