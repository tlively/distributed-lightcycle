# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: paxosmsg.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='paxosmsg.proto',
  package='Paxosmsg',
  serialized_pb=_b('\n\x0epaxosmsg.proto\x12\x08Paxosmsg\"\x80\x01\n\x03msg\x12\x1c\n\x04type\x18\x01 \x02(\x0e\x32\x0e.Paxosmsg.type\x12\x10\n\x08\x66rom_uid\x18\x02 \x02(\x05\x12\x13\n\x0bproposal_id\x18\x03 \x01(\t\x12\x13\n\x0bprevious_id\x18\x04 \x01(\t\x12\r\n\x05value\x18\x05 \x01(\t\x12\x10\n\x08instance\x18\x06 \x02(\x05*\x86\x01\n\x04type\x12\x0b\n\x07PREPARE\x10\x01\x12\x0b\n\x07PROMISE\x10\x02\x12\n\n\x06\x41\x43\x43\x45PT\x10\x03\x12\x0c\n\x08\x41\x43\x43\x45PTED\x10\x04\x12\x10\n\x0cNACK_PREPARE\x10\x05\x12\x0f\n\x0bNACK_ACCEPT\x10\x06\x12\r\n\tHEARTBEAT\x10\x07\x12\x0b\n\x07REQUEST\x10\x08\x12\x0b\n\x07REFUSAL\x10\t')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

_TYPE = _descriptor.EnumDescriptor(
  name='type',
  full_name='Paxosmsg.type',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='PREPARE', index=0, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='PROMISE', index=1, number=2,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ACCEPT', index=2, number=3,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ACCEPTED', index=3, number=4,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='NACK_PREPARE', index=4, number=5,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='NACK_ACCEPT', index=5, number=6,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='HEARTBEAT', index=6, number=7,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='REQUEST', index=7, number=8,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='REFUSAL', index=8, number=9,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=160,
  serialized_end=294,
)
_sym_db.RegisterEnumDescriptor(_TYPE)

type = enum_type_wrapper.EnumTypeWrapper(_TYPE)
PREPARE = 1
PROMISE = 2
ACCEPT = 3
ACCEPTED = 4
NACK_PREPARE = 5
NACK_ACCEPT = 6
HEARTBEAT = 7
REQUEST = 8
REFUSAL = 9



_MSG = _descriptor.Descriptor(
  name='msg',
  full_name='Paxosmsg.msg',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='type', full_name='Paxosmsg.msg.type', index=0,
      number=1, type=14, cpp_type=8, label=2,
      has_default_value=False, default_value=1,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='from_uid', full_name='Paxosmsg.msg.from_uid', index=1,
      number=2, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='proposal_id', full_name='Paxosmsg.msg.proposal_id', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='previous_id', full_name='Paxosmsg.msg.previous_id', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='value', full_name='Paxosmsg.msg.value', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='instance', full_name='Paxosmsg.msg.instance', index=5,
      number=6, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=29,
  serialized_end=157,
)

_MSG.fields_by_name['type'].enum_type = _TYPE
DESCRIPTOR.message_types_by_name['msg'] = _MSG
DESCRIPTOR.enum_types_by_name['type'] = _TYPE

msg = _reflection.GeneratedProtocolMessageType('msg', (_message.Message,), dict(
  DESCRIPTOR = _MSG,
  __module__ = 'paxosmsg_pb2'
  # @@protoc_insertion_point(class_scope:Paxosmsg.msg)
  ))
_sym_db.RegisterMessage(msg)


# @@protoc_insertion_point(module_scope)
