# ----------------------------------------------------------------------------
# vectypes
# Copyright (c) 2009 Alex Holkner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of vectypes nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

'''
Implements GLSL vector and matrix types, with some exceptions detailed below.
This implementation is based on the GLSL 1.20.8 specification, see
http://www.opengl.org/registry/doc/GLSLangSpec.Full.1.20.8.pdf

int, bool and float types from GLSL are substituted directly for
Python types of the same names.  As such, casting rules may differ from
the GLSL specification.

Types implemented:
  vec2,  vec3,  vec4
  ivec2, ivec3, ivec4
  bvec2, bvec3, bvec4

  mat2, mat2x2, mat2x3, mat2x4
  mat3, mat3x2, mat3x3, mat3x4,
  mat4, mat4x2, mat4x3, mat4x4

Exceptions and additions to the specification:

  - Vectors can be constructed with no arguments; this is equivalent to
    initialising them from the (possibly truncated) vector vec4(0, 0, 0, 1).
  - Matrices can be constructed with no arguments, creating the identity matrix.
  - Vector components are accessible only in "xyzw" form.  The "rgba" and
    "stpq" forms are not available.
  - Only scalar attributes are accessible in the vector, for example "v.x".
    The vector and swizzzled forms, for example "v.xyz" and "v.xxx" are
    not supported.
  - Component indexing of vectors with indices less than zero is permitted and behaves
    as per the usual Python indexing (it addresses counting back from the end
    of the vector).  Additionally, slice indices can be used, and return
    a tuple of the components requested.

    For example:
      - vec2()[-1] is equivalent to vec2().y
      - v = vec2(); v[:] is equivalent to (v.x, v.y)

  - Division by zero raises ArithmeticException
  - True division and floor division are supported
  - Pre- and post-increment and decrement operators are not supported.
  - Positive unary operator (+) is supported in addition to unary negation (-)

'''

import math as _math






def _dot2(a, b):
    # Implement dot product between two vectors of size 2
    return (
        a.x * b.x
      + a.y * b.y
    )
def _dot3(a, b):
    # Implement dot product between two vectors of size 3
    return (
        a.x * b.x
      + a.y * b.y
      + a.z * b.z
    )
def _dot4(a, b):
    # Implement dot product between two vectors of size 4
    return (
        a.x * b.x
      + a.y * b.y
      + a.z * b.z
      + a.w * b.w
    )





def _unwrapvec2args(args):
    if not args:
        # Identity constructor
        yield float(0)
        yield float(0)

    elif len(args) == 1:
        arg = args[0]
        if hasattr(arg, '_vector_components'):
            # Copy constructor with optional truncation
            yield arg.x
            yield arg.y
        else:
            # Unit scalar cast and replication
            yield float(arg)
            yield float(arg)

    else:
        # Initialize components sequentially from all arguments.
        for arg in args:
            argtype = type(arg)
            if argtype is float:
                # Fast path for common case -- scalar component
                yield arg
            else:
                try:
                    components = arg._vector_components
                except AttributeError:
                    # Cast scalar component
                    yield float(arg)
                    continue

                # Component-wise cast components
                yield float(arg.x)
                yield float(arg.y)
                if components >= 3:
                    yield float(arg.z)
                    if components == 4:
                        yield float(arg.w)

class vec2(object):
    _vector_components = 2
    __slots__ = tuple('xy')

    _vector_base_type = 'vec'

    def __init__(self, *args):
        self.x, self.y = _unwrapvec2args(args)

    def __repr__(self):
        return 'vec2%r' % (self[:],)

    def __getitem__(self, index):
        return (
            self.x,
            self.y,
        )[index]

    def __setitem__(self, index, value):
        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value

    def __len__(self):
        return 2

    def __add__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar +
            return vec2(
                self.x + (other),
                self.y + (other),
            )
        else:
            # Component-wise vector +
            return vec2(
                self.x + (other.x),
                self.y + (other.y),
            )

    def __sub__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar -
            return vec2(
                self.x - (other),
                self.y - (other),
            )
        else:
            # Component-wise vector -
            return vec2(
                self.x - (other.x),
                self.y - (other.y),
            )

    def __mul__(self, other):
        if hasattr(other, '_matrix_rows'):
            # row vector * matrix
            cols = other._cols
            assert other._matrix_rows == 2, 'Vector and matrix must have compatible size'
            if other._matrix_cols == 2:
                return vec2(_dot2(self, cols[0]),
                            _dot2(self, cols[1]))
            elif other._matrix_cols == 3:
                return vec3(_dot2(self, cols[0]),
                            _dot2(self, cols[1]),
                            _dot2(self, cols[2]))
            elif other._matrix_cols == 4:
                return vec4(_dot2(self, cols[0]),
                            _dot2(self, cols[1]),
                            _dot2(self, cols[2]),
                            _dot2(self, cols[3]))

        if not hasattr(other, '_vector_components'):
            # Component-wise scalar *
            return vec2(
                self.x * (other),
                self.y * (other),
            )
        else:
            # Component-wise vector *
            return vec2(
                self.x * (other.x),
                self.y * (other.y),
            )

    def __div__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar /
            return vec2(
                self.x / (other),
                self.y / (other),
            )
        else:
            # Component-wise vector /
            return vec2(
                self.x / (other.x),
                self.y / (other.y),
            )

    def __truediv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar .__truediv__
            return vec2(
                self.x .__truediv__ (other),
                self.y .__truediv__ (other),
            )
        else:
            # Component-wise vector .__truediv__
            return vec2(
                self.x .__truediv__ (other.x),
                self.y .__truediv__ (other.y),
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar //
            return vec2(
                self.x // (other),
                self.y // (other),
            )
        else:
            # Component-wise vector //
            return vec2(
                self.x // (other.x),
                self.y // (other.y),
            )

    def __radd__(self, other):
        # Component-wise scalar +
        return vec2(
            other + (self.x),
            other + (self.y),
        )

    def __rsub__(self, other):
        # Component-wise scalar -
        return vec2(
            other - (self.x),
            other - (self.y),
        )

    def __rmul__(self, other):
        # Component-wise scalar *
        return vec2(
            other * (self.x),
            other * (self.y),
        )

    def __rdiv__(self, other):
        # Component-wise scalar /
        return vec2(
            other / (self.x),
            other / (self.y),
        )

    def __rtruediv__(self, other):
        # Component-wise scalar .__truediv__
        return vec2(
            other .__truediv__ (self.x),
            other .__truediv__ (self.y),
        )

    def __rfloordiv__(self, other):
        # Component-wise scalar //
        return vec2(
            other // (self.x),
            other // (self.y),
        )

    def __neg__(self):
        # Component-wise scalar -
        return vec2(
            - self.x,
            - self.y,
        )

    def __pos__(self):
        # Component-wise scalar +
        return vec2(
            + self.x,
            + self.y,
        )

    def __eq__(self, other):
        if not hasattr(other, '_vector_components') or other._vector_components != self._vector_components:
            return False
        else:
            # Component-wise vector equality check
            return (self.x == other.x
                and self.y == other.y
            )

    def __ne__(self, other):
        if hasattr(other, '_vector_components') and other._vector_components == self._vector_components:
            # Component-wise vector equality check
            return (self.x != other.x
                 or self.y != other.y
            )
        else:
            return True

    def _outer_product(self, other):
        col = self[:]
        row = other[:]
        cols = len(row)
        if cols == 2:
            return mat2x2(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[1] * row[0],
                    col[1] * row[1],
            )
        elif cols == 3:
            return mat3x2(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[2] * row[0],
                    col[2] * row[1],
            )
        elif cols == 4:
            return mat4x2(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[2] * row[0],
                    col[2] * row[1],
                    col[3] * row[0],
                    col[3] * row[1],
            )

def _unwrapvec3args(args):
    if not args:
        # Identity constructor
        yield float(0)
        yield float(0)
        yield float(0)

    elif len(args) == 1:
        arg = args[0]
        if hasattr(arg, '_vector_components'):
            # Copy constructor with optional truncation
            yield arg.x
            yield arg.y
            yield arg.z
        else:
            # Unit scalar cast and replication
            yield float(arg)
            yield float(arg)
            yield float(arg)

    else:
        # Initialize components sequentially from all arguments.
        for arg in args:
            argtype = type(arg)
            if argtype is float:
                # Fast path for common case -- scalar component
                yield arg
            else:
                try:
                    components = arg._vector_components
                except AttributeError:
                    # Cast scalar component
                    yield float(arg)
                    continue

                # Component-wise cast components
                yield float(arg.x)
                yield float(arg.y)
                if components >= 3:
                    yield float(arg.z)
                    if components == 4:
                        yield float(arg.w)

class vec3(object):
    _vector_components = 3
    __slots__ = tuple('xyz')

    _vector_base_type = 'vec'

    def __init__(self, *args):
        self.x, self.y, self.z = _unwrapvec3args(args)

    def __repr__(self):
        return 'vec3%r' % (self[:],)

    def __getitem__(self, index):
        return (
            self.x,
            self.y,
            self.z,
        )[index]

    def __setitem__(self, index, value):
        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value
        elif index == 2:
            self.z = value

    def __len__(self):
        return 3

    def __add__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar +
            return vec3(
                self.x + (other),
                self.y + (other),
                self.z + (other),
            )
        else:
            # Component-wise vector +
            return vec3(
                self.x + (other.x),
                self.y + (other.y),
                self.z + (other.z),
            )

    def __sub__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar -
            return vec3(
                self.x - (other),
                self.y - (other),
                self.z - (other),
            )
        else:
            # Component-wise vector -
            return vec3(
                self.x - (other.x),
                self.y - (other.y),
                self.z - (other.z),
            )

    def __mul__(self, other):
        if hasattr(other, '_matrix_rows'):
            # row vector * matrix
            cols = other._cols
            assert other._matrix_rows == 3, 'Vector and matrix must have compatible size'
            if other._matrix_cols == 2:
                return vec2(_dot3(self, cols[0]),
                            _dot3(self, cols[1]))
            elif other._matrix_cols == 3:
                return vec3(_dot3(self, cols[0]),
                            _dot3(self, cols[1]),
                            _dot3(self, cols[2]))
            elif other._matrix_cols == 4:
                return vec4(_dot3(self, cols[0]),
                            _dot3(self, cols[1]),
                            _dot3(self, cols[2]),
                            _dot3(self, cols[3]))

        if not hasattr(other, '_vector_components'):
            # Component-wise scalar *
            return vec3(
                self.x * (other),
                self.y * (other),
                self.z * (other),
            )
        else:
            # Component-wise vector *
            return vec3(
                self.x * (other.x),
                self.y * (other.y),
                self.z * (other.z),
            )

    def __div__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar /
            return vec3(
                self.x / (other),
                self.y / (other),
                self.z / (other),
            )
        else:
            # Component-wise vector /
            return vec3(
                self.x / (other.x),
                self.y / (other.y),
                self.z / (other.z),
            )

    def __truediv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar .__truediv__
            return vec3(
                self.x .__truediv__ (other),
                self.y .__truediv__ (other),
                self.z .__truediv__ (other),
            )
        else:
            # Component-wise vector .__truediv__
            return vec3(
                self.x .__truediv__ (other.x),
                self.y .__truediv__ (other.y),
                self.z .__truediv__ (other.z),
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar //
            return vec3(
                self.x // (other),
                self.y // (other),
                self.z // (other),
            )
        else:
            # Component-wise vector //
            return vec3(
                self.x // (other.x),
                self.y // (other.y),
                self.z // (other.z),
            )

    def __radd__(self, other):
        # Component-wise scalar +
        return vec3(
            other + (self.x),
            other + (self.y),
            other + (self.z),
        )

    def __rsub__(self, other):
        # Component-wise scalar -
        return vec3(
            other - (self.x),
            other - (self.y),
            other - (self.z),
        )

    def __rmul__(self, other):
        # Component-wise scalar *
        return vec3(
            other * (self.x),
            other * (self.y),
            other * (self.z),
        )

    def __rdiv__(self, other):
        # Component-wise scalar /
        return vec3(
            other / (self.x),
            other / (self.y),
            other / (self.z),
        )

    def __rtruediv__(self, other):
        # Component-wise scalar .__truediv__
        return vec3(
            other .__truediv__ (self.x),
            other .__truediv__ (self.y),
            other .__truediv__ (self.z),
        )

    def __rfloordiv__(self, other):
        # Component-wise scalar //
        return vec3(
            other // (self.x),
            other // (self.y),
            other // (self.z),
        )

    def __neg__(self):
        # Component-wise scalar -
        return vec3(
            - self.x,
            - self.y,
            - self.z,
        )

    def __pos__(self):
        # Component-wise scalar +
        return vec3(
            + self.x,
            + self.y,
            + self.z,
        )

    def __eq__(self, other):
        if not hasattr(other, '_vector_components') or other._vector_components != self._vector_components:
            return False
        else:
            # Component-wise vector equality check
            return (self.x == other.x
                and self.y == other.y
                and self.z == other.z
            )

    def __ne__(self, other):
        if hasattr(other, '_vector_components') and other._vector_components == self._vector_components:
            # Component-wise vector equality check
            return (self.x != other.x
                 or self.y != other.y
                 or self.z != other.z
            )
        else:
            return True

    def _outer_product(self, other):
        col = self[:]
        row = other[:]
        cols = len(row)
        if cols == 2:
            return mat2x3(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
            )
        elif cols == 3:
            return mat3x3(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
                    col[2] * row[0],
                    col[2] * row[1],
                    col[2] * row[2],
            )
        elif cols == 4:
            return mat4x3(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
                    col[2] * row[0],
                    col[2] * row[1],
                    col[2] * row[2],
                    col[3] * row[0],
                    col[3] * row[1],
                    col[3] * row[2],
            )

def _unwrapvec4args(args):
    if not args:
        # Identity constructor
        yield float(0)
        yield float(0)
        yield float(0)
        yield float(1)

    elif len(args) == 1:
        arg = args[0]
        if hasattr(arg, '_vector_components'):
            # Copy constructor with optional truncation
            yield arg.x
            yield arg.y
            yield arg.z
            yield arg.w
        else:
            # Unit scalar cast and replication
            yield float(arg)
            yield float(arg)
            yield float(arg)
            yield float(arg)

    else:
        # Initialize components sequentially from all arguments.
        for arg in args:
            argtype = type(arg)
            if argtype is float:
                # Fast path for common case -- scalar component
                yield arg
            else:
                try:
                    components = arg._vector_components
                except AttributeError:
                    # Cast scalar component
                    yield float(arg)
                    continue

                # Component-wise cast components
                yield float(arg.x)
                yield float(arg.y)
                if components >= 3:
                    yield float(arg.z)
                    if components == 4:
                        yield float(arg.w)

class vec4(object):
    _vector_components = 4
    __slots__ = tuple('xyzw')

    _vector_base_type = 'vec'

    def __init__(self, *args):
        self.x, self.y, self.z, self.w = _unwrapvec4args(args)

    def __repr__(self):
        return 'vec4%r' % (self[:],)

    def __getitem__(self, index):
        return (
            self.x,
            self.y,
            self.z,
            self.w,
        )[index]

    def __setitem__(self, index, value):
        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value
        elif index == 2:
            self.z = value
        elif index == 3:
            self.w = value

    def __len__(self):
        return 4

    def __add__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar +
            return vec4(
                self.x + (other),
                self.y + (other),
                self.z + (other),
                self.w + (other)
            )
        else:
            # Component-wise vector +
            return vec4(
                self.x + (other.x),
                self.y + (other.y),
                self.z + (other.z),
                self.w + (other.w)
            )

    def __sub__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar -
            return vec4(
                self.x - (other),
                self.y - (other),
                self.z - (other),
                self.w - (other)
            )
        else:
            # Component-wise vector -
            return vec4(
                self.x - (other.x),
                self.y - (other.y),
                self.z - (other.z),
                self.w - (other.w)
            )

    def __mul__(self, other):
        if hasattr(other, '_matrix_rows'):
            # row vector * matrix
            cols = other._cols
            assert other._matrix_rows == 4, 'Vector and matrix must have compatible size'
            if other._matrix_cols == 2:
                return vec2(_dot4(self, cols[0]),
                            _dot4(self, cols[1]))
            elif other._matrix_cols == 3:
                return vec3(_dot4(self, cols[0]),
                            _dot4(self, cols[1]),
                            _dot4(self, cols[2]))
            elif other._matrix_cols == 4:
                return vec4(_dot4(self, cols[0]),
                            _dot4(self, cols[1]),
                            _dot4(self, cols[2]),
                            _dot4(self, cols[3]))

        if not hasattr(other, '_vector_components'):
            # Component-wise scalar *
            return vec4(
                self.x * (other),
                self.y * (other),
                self.z * (other),
                self.w * (other)
            )
        else:
            # Component-wise vector *
            return vec4(
                self.x * (other.x),
                self.y * (other.y),
                self.z * (other.z),
                self.w * (other.w)
            )

    def __div__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar /
            return vec4(
                self.x / (other),
                self.y / (other),
                self.z / (other),
                self.w / (other)
            )
        else:
            # Component-wise vector /
            return vec4(
                self.x / (other.x),
                self.y / (other.y),
                self.z / (other.z),
                self.w / (other.w)
            )

    def __truediv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar .__truediv__
            return vec4(
                self.x .__truediv__ (other),
                self.y .__truediv__ (other),
                self.z .__truediv__ (other),
                self.w .__truediv__ (other)
            )
        else:
            # Component-wise vector .__truediv__
            return vec4(
                self.x .__truediv__ (other.x),
                self.y .__truediv__ (other.y),
                self.z .__truediv__ (other.z),
                self.w .__truediv__ (other.w)
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar //
            return vec4(
                self.x // (other),
                self.y // (other),
                self.z // (other),
                self.w // (other)
            )
        else:
            # Component-wise vector //
            return vec4(
                self.x // (other.x),
                self.y // (other.y),
                self.z // (other.z),
                self.w // (other.w)
            )

    def __radd__(self, other):
        # Component-wise scalar +
        return vec4(
            other + (self.x),
            other + (self.y),
            other + (self.z),
            other + (self.w)
        )

    def __rsub__(self, other):
        # Component-wise scalar -
        return vec4(
            other - (self.x),
            other - (self.y),
            other - (self.z),
            other - (self.w)
        )

    def __rmul__(self, other):
        # Component-wise scalar *
        return vec4(
            other * (self.x),
            other * (self.y),
            other * (self.z),
            other * (self.w)
        )

    def __rdiv__(self, other):
        # Component-wise scalar /
        return vec4(
            other / (self.x),
            other / (self.y),
            other / (self.z),
            other / (self.w)
        )

    def __rtruediv__(self, other):
        # Component-wise scalar .__truediv__
        return vec4(
            other .__truediv__ (self.x),
            other .__truediv__ (self.y),
            other .__truediv__ (self.z),
            other .__truediv__ (self.w)
        )

    def __rfloordiv__(self, other):
        # Component-wise scalar //
        return vec4(
            other // (self.x),
            other // (self.y),
            other // (self.z),
            other // (self.w)
        )

    def __neg__(self):
        # Component-wise scalar -
        return vec4(
            - self.x,
            - self.y,
            - self.z,
            - self.w
        )

    def __pos__(self):
        # Component-wise scalar +
        return vec4(
            + self.x,
            + self.y,
            + self.z,
            + self.w
        )

    def __eq__(self, other):
        if not hasattr(other, '_vector_components') or other._vector_components != self._vector_components:
            return False
        else:
            # Component-wise vector equality check
            return (self.x == other.x
                and self.y == other.y
                and self.z == other.z
                and self.w == other.w
            )

    def __ne__(self, other):
        if hasattr(other, '_vector_components') and other._vector_components == self._vector_components:
            # Component-wise vector equality check
            return (self.x != other.x
                 or self.y != other.y
                 or self.z != other.z
                 or self.w != other.w
            )
        else:
            return True

    def _outer_product(self, other):
        col = self[:]
        row = other[:]
        cols = len(row)
        if cols == 2:
            return mat2x4(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[0] * row[3],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
                    col[1] * row[3],
            )
        elif cols == 3:
            return mat3x4(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[0] * row[3],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
                    col[1] * row[3],
                    col[2] * row[0],
                    col[2] * row[1],
                    col[2] * row[2],
                    col[2] * row[3],
            )
        elif cols == 4:
            return mat4x4(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[0] * row[3],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
                    col[1] * row[3],
                    col[2] * row[0],
                    col[2] * row[1],
                    col[2] * row[2],
                    col[2] * row[3],
                    col[3] * row[0],
                    col[3] * row[1],
                    col[3] * row[2],
                    col[3] * row[3],
            )

def _unwrapivec2args(args):
    if not args:
        # Identity constructor
        yield int(0)
        yield int(0)

    elif len(args) == 1:
        arg = args[0]
        if hasattr(arg, '_vector_components'):
            # Copy constructor with optional truncation
            yield arg.x
            yield arg.y
        else:
            # Unit scalar cast and replication
            yield int(arg)
            yield int(arg)

    else:
        # Initialize components sequentially from all arguments.
        for arg in args:
            argtype = type(arg)
            if argtype is int:
                # Fast path for common case -- scalar component
                yield arg
            else:
                try:
                    components = arg._vector_components
                except AttributeError:
                    # Cast scalar component
                    yield int(arg)
                    continue

                # Component-wise cast components
                yield int(arg.x)
                yield int(arg.y)
                if components >= 3:
                    yield int(arg.z)
                    if components == 4:
                        yield int(arg.w)

class ivec2(object):
    _vector_components = 2
    __slots__ = tuple('xy')

    _vector_base_type = 'ivec'

    def __init__(self, *args):
        self.x, self.y = _unwrapivec2args(args)

    def __repr__(self):
        return 'ivec2%r' % (self[:],)

    def __getitem__(self, index):
        return (
            self.x,
            self.y,
        )[index]

    def __setitem__(self, index, value):
        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value

    def __len__(self):
        return 2

    def __add__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar +
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x + (other),
                self.y + (other),
            )
        else:
            # Component-wise vector +
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x + (other.x),
                self.y + (other.y),
            )

    def __sub__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar -
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x - (other),
                self.y - (other),
            )
        else:
            # Component-wise vector -
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x - (other.x),
                self.y - (other.y),
            )

    def __mul__(self, other):
        if hasattr(other, '_matrix_rows'):
            # row vector * matrix
            cols = other._cols
            assert other._matrix_rows == 2, 'Vector and matrix must have compatible size'
            if other._matrix_cols == 2:
                return vec2(_dot2(self, cols[0]),
                            _dot2(self, cols[1]))
            elif other._matrix_cols == 3:
                return vec3(_dot2(self, cols[0]),
                            _dot2(self, cols[1]),
                            _dot2(self, cols[2]))
            elif other._matrix_cols == 4:
                return vec4(_dot2(self, cols[0]),
                            _dot2(self, cols[1]),
                            _dot2(self, cols[2]),
                            _dot2(self, cols[3]))

        if not hasattr(other, '_vector_components'):
            # Component-wise scalar *
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x * (other),
                self.y * (other),
            )
        else:
            # Component-wise vector *
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x * (other.x),
                self.y * (other.y),
            )

    def __div__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar /
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x / (other),
                self.y / (other),
            )
        else:
            # Component-wise vector /
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x / (other.x),
                self.y / (other.y),
            )

    def __truediv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar .__truediv__
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x .__truediv__ (other),
                self.y .__truediv__ (other),
            )
        else:
            # Component-wise vector .__truediv__
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x .__truediv__ (other.x),
                self.y .__truediv__ (other.y),
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar //
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x // (other),
                self.y // (other),
            )
        else:
            # Component-wise vector //
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x // (other.x),
                self.y // (other.y),
            )

    def __radd__(self, other):
        # Component-wise scalar +
        return self._vector_upcast_scalar_rtype[type(other)](
            other + (self.x),
            other + (self.y),
        )

    def __rsub__(self, other):
        # Component-wise scalar -
        return self._vector_upcast_scalar_rtype[type(other)](
            other - (self.x),
            other - (self.y),
        )

    def __rmul__(self, other):
        # Component-wise scalar *
        return self._vector_upcast_scalar_rtype[type(other)](
            other * (self.x),
            other * (self.y),
        )

    def __rdiv__(self, other):
        # Component-wise scalar /
        return self._vector_upcast_scalar_rtype[type(other)](
            other / (self.x),
            other / (self.y),
        )

    def __rtruediv__(self, other):
        # Component-wise scalar .__truediv__
        return self._vector_upcast_scalar_rtype[type(other)](
            other .__truediv__ (self.x),
            other .__truediv__ (self.y),
        )

    def __rfloordiv__(self, other):
        # Component-wise scalar //
        return self._vector_upcast_scalar_rtype[type(other)](
            other // (self.x),
            other // (self.y),
        )

    def __neg__(self):
        # Component-wise scalar -
        return ivec2(
            - self.x,
            - self.y,
        )

    def __pos__(self):
        # Component-wise scalar +
        return ivec2(
            + self.x,
            + self.y,
        )

    def __eq__(self, other):
        if not hasattr(other, '_vector_components') or other._vector_components != self._vector_components:
            return False
        else:
            # Component-wise vector equality check
            return (self.x == other.x
                and self.y == other.y
            )

    def __ne__(self, other):
        if hasattr(other, '_vector_components') and other._vector_components == self._vector_components:
            # Component-wise vector equality check
            return (self.x != other.x
                 or self.y != other.y
            )
        else:
            return True

    def _outer_product(self, other):
        col = self[:]
        row = other[:]
        cols = len(row)
        if cols == 2:
            return mat2x2(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[1] * row[0],
                    col[1] * row[1],
            )
        elif cols == 3:
            return mat3x2(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[2] * row[0],
                    col[2] * row[1],
            )
        elif cols == 4:
            return mat4x2(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[2] * row[0],
                    col[2] * row[1],
                    col[3] * row[0],
                    col[3] * row[1],
            )

def _unwrapivec3args(args):
    if not args:
        # Identity constructor
        yield int(0)
        yield int(0)
        yield int(0)

    elif len(args) == 1:
        arg = args[0]
        if hasattr(arg, '_vector_components'):
            # Copy constructor with optional truncation
            yield arg.x
            yield arg.y
            yield arg.z
        else:
            # Unit scalar cast and replication
            yield int(arg)
            yield int(arg)
            yield int(arg)

    else:
        # Initialize components sequentially from all arguments.
        for arg in args:
            argtype = type(arg)
            if argtype is int:
                # Fast path for common case -- scalar component
                yield arg
            else:
                try:
                    components = arg._vector_components
                except AttributeError:
                    # Cast scalar component
                    yield int(arg)
                    continue

                # Component-wise cast components
                yield int(arg.x)
                yield int(arg.y)
                if components >= 3:
                    yield int(arg.z)
                    if components == 4:
                        yield int(arg.w)

class ivec3(object):
    _vector_components = 3
    __slots__ = tuple('xyz')

    _vector_base_type = 'ivec'

    def __init__(self, *args):
        self.x, self.y, self.z = _unwrapivec3args(args)

    def __repr__(self):
        return 'ivec3%r' % (self[:],)

    def __getitem__(self, index):
        return (
            self.x,
            self.y,
            self.z,
        )[index]

    def __setitem__(self, index, value):
        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value
        elif index == 2:
            self.z = value

    def __len__(self):
        return 3

    def __add__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar +
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x + (other),
                self.y + (other),
                self.z + (other),
            )
        else:
            # Component-wise vector +
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x + (other.x),
                self.y + (other.y),
                self.z + (other.z),
            )

    def __sub__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar -
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x - (other),
                self.y - (other),
                self.z - (other),
            )
        else:
            # Component-wise vector -
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x - (other.x),
                self.y - (other.y),
                self.z - (other.z),
            )

    def __mul__(self, other):
        if hasattr(other, '_matrix_rows'):
            # row vector * matrix
            cols = other._cols
            assert other._matrix_rows == 3, 'Vector and matrix must have compatible size'
            if other._matrix_cols == 2:
                return vec2(_dot3(self, cols[0]),
                            _dot3(self, cols[1]))
            elif other._matrix_cols == 3:
                return vec3(_dot3(self, cols[0]),
                            _dot3(self, cols[1]),
                            _dot3(self, cols[2]))
            elif other._matrix_cols == 4:
                return vec4(_dot3(self, cols[0]),
                            _dot3(self, cols[1]),
                            _dot3(self, cols[2]),
                            _dot3(self, cols[3]))

        if not hasattr(other, '_vector_components'):
            # Component-wise scalar *
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x * (other),
                self.y * (other),
                self.z * (other),
            )
        else:
            # Component-wise vector *
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x * (other.x),
                self.y * (other.y),
                self.z * (other.z),
            )

    def __div__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar /
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x / (other),
                self.y / (other),
                self.z / (other),
            )
        else:
            # Component-wise vector /
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x / (other.x),
                self.y / (other.y),
                self.z / (other.z),
            )

    def __truediv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar .__truediv__
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x .__truediv__ (other),
                self.y .__truediv__ (other),
                self.z .__truediv__ (other),
            )
        else:
            # Component-wise vector .__truediv__
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x .__truediv__ (other.x),
                self.y .__truediv__ (other.y),
                self.z .__truediv__ (other.z),
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar //
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x // (other),
                self.y // (other),
                self.z // (other),
            )
        else:
            # Component-wise vector //
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x // (other.x),
                self.y // (other.y),
                self.z // (other.z),
            )

    def __radd__(self, other):
        # Component-wise scalar +
        return self._vector_upcast_scalar_rtype[type(other)](
            other + (self.x),
            other + (self.y),
            other + (self.z),
        )

    def __rsub__(self, other):
        # Component-wise scalar -
        return self._vector_upcast_scalar_rtype[type(other)](
            other - (self.x),
            other - (self.y),
            other - (self.z),
        )

    def __rmul__(self, other):
        # Component-wise scalar *
        return self._vector_upcast_scalar_rtype[type(other)](
            other * (self.x),
            other * (self.y),
            other * (self.z),
        )

    def __rdiv__(self, other):
        # Component-wise scalar /
        return self._vector_upcast_scalar_rtype[type(other)](
            other / (self.x),
            other / (self.y),
            other / (self.z),
        )

    def __rtruediv__(self, other):
        # Component-wise scalar .__truediv__
        return self._vector_upcast_scalar_rtype[type(other)](
            other .__truediv__ (self.x),
            other .__truediv__ (self.y),
            other .__truediv__ (self.z),
        )

    def __rfloordiv__(self, other):
        # Component-wise scalar //
        return self._vector_upcast_scalar_rtype[type(other)](
            other // (self.x),
            other // (self.y),
            other // (self.z),
        )

    def __neg__(self):
        # Component-wise scalar -
        return ivec3(
            - self.x,
            - self.y,
            - self.z,
        )

    def __pos__(self):
        # Component-wise scalar +
        return ivec3(
            + self.x,
            + self.y,
            + self.z,
        )

    def __eq__(self, other):
        if not hasattr(other, '_vector_components') or other._vector_components != self._vector_components:
            return False
        else:
            # Component-wise vector equality check
            return (self.x == other.x
                and self.y == other.y
                and self.z == other.z
            )

    def __ne__(self, other):
        if hasattr(other, '_vector_components') and other._vector_components == self._vector_components:
            # Component-wise vector equality check
            return (self.x != other.x
                 or self.y != other.y
                 or self.z != other.z
            )
        else:
            return True

    def _outer_product(self, other):
        col = self[:]
        row = other[:]
        cols = len(row)
        if cols == 2:
            return mat2x3(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
            )
        elif cols == 3:
            return mat3x3(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
                    col[2] * row[0],
                    col[2] * row[1],
                    col[2] * row[2],
            )
        elif cols == 4:
            return mat4x3(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
                    col[2] * row[0],
                    col[2] * row[1],
                    col[2] * row[2],
                    col[3] * row[0],
                    col[3] * row[1],
                    col[3] * row[2],
            )

def _unwrapivec4args(args):
    if not args:
        # Identity constructor
        yield int(0)
        yield int(0)
        yield int(0)
        yield int(1)

    elif len(args) == 1:
        arg = args[0]
        if hasattr(arg, '_vector_components'):
            # Copy constructor with optional truncation
            yield arg.x
            yield arg.y
            yield arg.z
            yield arg.w
        else:
            # Unit scalar cast and replication
            yield int(arg)
            yield int(arg)
            yield int(arg)
            yield int(arg)

    else:
        # Initialize components sequentially from all arguments.
        for arg in args:
            argtype = type(arg)
            if argtype is int:
                # Fast path for common case -- scalar component
                yield arg
            else:
                try:
                    components = arg._vector_components
                except AttributeError:
                    # Cast scalar component
                    yield int(arg)
                    continue

                # Component-wise cast components
                yield int(arg.x)
                yield int(arg.y)
                if components >= 3:
                    yield int(arg.z)
                    if components == 4:
                        yield int(arg.w)

class ivec4(object):
    _vector_components = 4
    __slots__ = tuple('xyzw')

    _vector_base_type = 'ivec'

    def __init__(self, *args):
        self.x, self.y, self.z, self.w = _unwrapivec4args(args)

    def __repr__(self):
        return 'ivec4%r' % (self[:],)

    def __getitem__(self, index):
        return (
            self.x,
            self.y,
            self.z,
            self.w,
        )[index]

    def __setitem__(self, index, value):
        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value
        elif index == 2:
            self.z = value
        elif index == 3:
            self.w = value

    def __len__(self):
        return 4

    def __add__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar +
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x + (other),
                self.y + (other),
                self.z + (other),
                self.w + (other)
            )
        else:
            # Component-wise vector +
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x + (other.x),
                self.y + (other.y),
                self.z + (other.z),
                self.w + (other.w)
            )

    def __sub__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar -
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x - (other),
                self.y - (other),
                self.z - (other),
                self.w - (other)
            )
        else:
            # Component-wise vector -
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x - (other.x),
                self.y - (other.y),
                self.z - (other.z),
                self.w - (other.w)
            )

    def __mul__(self, other):
        if hasattr(other, '_matrix_rows'):
            # row vector * matrix
            cols = other._cols
            assert other._matrix_rows == 4, 'Vector and matrix must have compatible size'
            if other._matrix_cols == 2:
                return vec2(_dot4(self, cols[0]),
                            _dot4(self, cols[1]))
            elif other._matrix_cols == 3:
                return vec3(_dot4(self, cols[0]),
                            _dot4(self, cols[1]),
                            _dot4(self, cols[2]))
            elif other._matrix_cols == 4:
                return vec4(_dot4(self, cols[0]),
                            _dot4(self, cols[1]),
                            _dot4(self, cols[2]),
                            _dot4(self, cols[3]))

        if not hasattr(other, '_vector_components'):
            # Component-wise scalar *
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x * (other),
                self.y * (other),
                self.z * (other),
                self.w * (other)
            )
        else:
            # Component-wise vector *
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x * (other.x),
                self.y * (other.y),
                self.z * (other.z),
                self.w * (other.w)
            )

    def __div__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar /
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x / (other),
                self.y / (other),
                self.z / (other),
                self.w / (other)
            )
        else:
            # Component-wise vector /
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x / (other.x),
                self.y / (other.y),
                self.z / (other.z),
                self.w / (other.w)
            )

    def __truediv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar .__truediv__
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x .__truediv__ (other),
                self.y .__truediv__ (other),
                self.z .__truediv__ (other),
                self.w .__truediv__ (other)
            )
        else:
            # Component-wise vector .__truediv__
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x .__truediv__ (other.x),
                self.y .__truediv__ (other.y),
                self.z .__truediv__ (other.z),
                self.w .__truediv__ (other.w)
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar //
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x // (other),
                self.y // (other),
                self.z // (other),
                self.w // (other)
            )
        else:
            # Component-wise vector //
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x // (other.x),
                self.y // (other.y),
                self.z // (other.z),
                self.w // (other.w)
            )

    def __radd__(self, other):
        # Component-wise scalar +
        return self._vector_upcast_scalar_rtype[type(other)](
            other + (self.x),
            other + (self.y),
            other + (self.z),
            other + (self.w)
        )

    def __rsub__(self, other):
        # Component-wise scalar -
        return self._vector_upcast_scalar_rtype[type(other)](
            other - (self.x),
            other - (self.y),
            other - (self.z),
            other - (self.w)
        )

    def __rmul__(self, other):
        # Component-wise scalar *
        return self._vector_upcast_scalar_rtype[type(other)](
            other * (self.x),
            other * (self.y),
            other * (self.z),
            other * (self.w)
        )

    def __rdiv__(self, other):
        # Component-wise scalar /
        return self._vector_upcast_scalar_rtype[type(other)](
            other / (self.x),
            other / (self.y),
            other / (self.z),
            other / (self.w)
        )

    def __rtruediv__(self, other):
        # Component-wise scalar .__truediv__
        return self._vector_upcast_scalar_rtype[type(other)](
            other .__truediv__ (self.x),
            other .__truediv__ (self.y),
            other .__truediv__ (self.z),
            other .__truediv__ (self.w)
        )

    def __rfloordiv__(self, other):
        # Component-wise scalar //
        return self._vector_upcast_scalar_rtype[type(other)](
            other // (self.x),
            other // (self.y),
            other // (self.z),
            other // (self.w)
        )

    def __neg__(self):
        # Component-wise scalar -
        return ivec4(
            - self.x,
            - self.y,
            - self.z,
            - self.w
        )

    def __pos__(self):
        # Component-wise scalar +
        return ivec4(
            + self.x,
            + self.y,
            + self.z,
            + self.w
        )

    def __eq__(self, other):
        if not hasattr(other, '_vector_components') or other._vector_components != self._vector_components:
            return False
        else:
            # Component-wise vector equality check
            return (self.x == other.x
                and self.y == other.y
                and self.z == other.z
                and self.w == other.w
            )

    def __ne__(self, other):
        if hasattr(other, '_vector_components') and other._vector_components == self._vector_components:
            # Component-wise vector equality check
            return (self.x != other.x
                 or self.y != other.y
                 or self.z != other.z
                 or self.w != other.w
            )
        else:
            return True

    def _outer_product(self, other):
        col = self[:]
        row = other[:]
        cols = len(row)
        if cols == 2:
            return mat2x4(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[0] * row[3],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
                    col[1] * row[3],
            )
        elif cols == 3:
            return mat3x4(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[0] * row[3],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
                    col[1] * row[3],
                    col[2] * row[0],
                    col[2] * row[1],
                    col[2] * row[2],
                    col[2] * row[3],
            )
        elif cols == 4:
            return mat4x4(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[0] * row[3],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
                    col[1] * row[3],
                    col[2] * row[0],
                    col[2] * row[1],
                    col[2] * row[2],
                    col[2] * row[3],
                    col[3] * row[0],
                    col[3] * row[1],
                    col[3] * row[2],
                    col[3] * row[3],
            )

def _unwrapbvec2args(args):
    if not args:
        # Identity constructor
        yield bool(0)
        yield bool(0)

    elif len(args) == 1:
        arg = args[0]
        if hasattr(arg, '_vector_components'):
            # Copy constructor with optional truncation
            yield arg.x
            yield arg.y
        else:
            # Unit scalar cast and replication
            yield bool(arg)
            yield bool(arg)

    else:
        # Initialize components sequentially from all arguments.
        for arg in args:
            argtype = type(arg)
            if argtype is bool:
                # Fast path for common case -- scalar component
                yield arg
            else:
                try:
                    components = arg._vector_components
                except AttributeError:
                    # Cast scalar component
                    yield bool(arg)
                    continue

                # Component-wise cast components
                yield bool(arg.x)
                yield bool(arg.y)
                if components >= 3:
                    yield bool(arg.z)
                    if components == 4:
                        yield bool(arg.w)

class bvec2(object):
    _vector_components = 2
    __slots__ = tuple('xy')

    _vector_base_type = 'bvec'

    def __init__(self, *args):
        self.x, self.y = _unwrapbvec2args(args)

    def __repr__(self):
        return 'bvec2%r' % (self[:],)

    def __getitem__(self, index):
        return (
            self.x,
            self.y,
        )[index]

    def __setitem__(self, index, value):
        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value

    def __len__(self):
        return 2

    def __add__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar +
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x + (other),
                self.y + (other),
            )
        else:
            # Component-wise vector +
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x + (other.x),
                self.y + (other.y),
            )

    def __sub__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar -
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x - (other),
                self.y - (other),
            )
        else:
            # Component-wise vector -
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x - (other.x),
                self.y - (other.y),
            )

    def __mul__(self, other):
        if hasattr(other, '_matrix_rows'):
            # row vector * matrix
            cols = other._cols
            assert other._matrix_rows == 2, 'Vector and matrix must have compatible size'
            if other._matrix_cols == 2:
                return vec2(_dot2(self, cols[0]),
                            _dot2(self, cols[1]))
            elif other._matrix_cols == 3:
                return vec3(_dot2(self, cols[0]),
                            _dot2(self, cols[1]),
                            _dot2(self, cols[2]))
            elif other._matrix_cols == 4:
                return vec4(_dot2(self, cols[0]),
                            _dot2(self, cols[1]),
                            _dot2(self, cols[2]),
                            _dot2(self, cols[3]))

        if not hasattr(other, '_vector_components'):
            # Component-wise scalar *
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x * (other),
                self.y * (other),
            )
        else:
            # Component-wise vector *
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x * (other.x),
                self.y * (other.y),
            )

    def __div__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar /
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x / (other),
                self.y / (other),
            )
        else:
            # Component-wise vector /
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x / (other.x),
                self.y / (other.y),
            )

    def __truediv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar .__truediv__
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x .__truediv__ (other),
                self.y .__truediv__ (other),
            )
        else:
            # Component-wise vector .__truediv__
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x .__truediv__ (other.x),
                self.y .__truediv__ (other.y),
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar //
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x // (other),
                self.y // (other),
            )
        else:
            # Component-wise vector //
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x // (other.x),
                self.y // (other.y),
            )

    def __radd__(self, other):
        # Component-wise scalar +
        return self._vector_upcast_scalar_rtype[type(other)](
            other + (self.x),
            other + (self.y),
        )

    def __rsub__(self, other):
        # Component-wise scalar -
        return self._vector_upcast_scalar_rtype[type(other)](
            other - (self.x),
            other - (self.y),
        )

    def __rmul__(self, other):
        # Component-wise scalar *
        return self._vector_upcast_scalar_rtype[type(other)](
            other * (self.x),
            other * (self.y),
        )

    def __rdiv__(self, other):
        # Component-wise scalar /
        return self._vector_upcast_scalar_rtype[type(other)](
            other / (self.x),
            other / (self.y),
        )

    def __rtruediv__(self, other):
        # Component-wise scalar .__truediv__
        return self._vector_upcast_scalar_rtype[type(other)](
            other .__truediv__ (self.x),
            other .__truediv__ (self.y),
        )

    def __rfloordiv__(self, other):
        # Component-wise scalar //
        return self._vector_upcast_scalar_rtype[type(other)](
            other // (self.x),
            other // (self.y),
        )

    def __neg__(self):
        # Component-wise scalar -
        return bvec2(
            - self.x,
            - self.y,
        )

    def __pos__(self):
        # Component-wise scalar +
        return bvec2(
            + self.x,
            + self.y,
        )

    def __eq__(self, other):
        if not hasattr(other, '_vector_components') or other._vector_components != self._vector_components:
            return False
        else:
            # Component-wise vector equality check
            return (self.x == other.x
                and self.y == other.y
            )

    def __ne__(self, other):
        if hasattr(other, '_vector_components') and other._vector_components == self._vector_components:
            # Component-wise vector equality check
            return (self.x != other.x
                 or self.y != other.y
            )
        else:
            return True

    def _outer_product(self, other):
        col = self[:]
        row = other[:]
        cols = len(row)
        if cols == 2:
            return mat2x2(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[1] * row[0],
                    col[1] * row[1],
            )
        elif cols == 3:
            return mat3x2(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[2] * row[0],
                    col[2] * row[1],
            )
        elif cols == 4:
            return mat4x2(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[2] * row[0],
                    col[2] * row[1],
                    col[3] * row[0],
                    col[3] * row[1],
            )

def _unwrapbvec3args(args):
    if not args:
        # Identity constructor
        yield bool(0)
        yield bool(0)
        yield bool(0)

    elif len(args) == 1:
        arg = args[0]
        if hasattr(arg, '_vector_components'):
            # Copy constructor with optional truncation
            yield arg.x
            yield arg.y
            yield arg.z
        else:
            # Unit scalar cast and replication
            yield bool(arg)
            yield bool(arg)
            yield bool(arg)

    else:
        # Initialize components sequentially from all arguments.
        for arg in args:
            argtype = type(arg)
            if argtype is bool:
                # Fast path for common case -- scalar component
                yield arg
            else:
                try:
                    components = arg._vector_components
                except AttributeError:
                    # Cast scalar component
                    yield bool(arg)
                    continue

                # Component-wise cast components
                yield bool(arg.x)
                yield bool(arg.y)
                if components >= 3:
                    yield bool(arg.z)
                    if components == 4:
                        yield bool(arg.w)

class bvec3(object):
    _vector_components = 3
    __slots__ = tuple('xyz')

    _vector_base_type = 'bvec'

    def __init__(self, *args):
        self.x, self.y, self.z = _unwrapbvec3args(args)

    def __repr__(self):
        return 'bvec3%r' % (self[:],)

    def __getitem__(self, index):
        return (
            self.x,
            self.y,
            self.z,
        )[index]

    def __setitem__(self, index, value):
        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value
        elif index == 2:
            self.z = value

    def __len__(self):
        return 3

    def __add__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar +
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x + (other),
                self.y + (other),
                self.z + (other),
            )
        else:
            # Component-wise vector +
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x + (other.x),
                self.y + (other.y),
                self.z + (other.z),
            )

    def __sub__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar -
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x - (other),
                self.y - (other),
                self.z - (other),
            )
        else:
            # Component-wise vector -
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x - (other.x),
                self.y - (other.y),
                self.z - (other.z),
            )

    def __mul__(self, other):
        if hasattr(other, '_matrix_rows'):
            # row vector * matrix
            cols = other._cols
            assert other._matrix_rows == 3, 'Vector and matrix must have compatible size'
            if other._matrix_cols == 2:
                return vec2(_dot3(self, cols[0]),
                            _dot3(self, cols[1]))
            elif other._matrix_cols == 3:
                return vec3(_dot3(self, cols[0]),
                            _dot3(self, cols[1]),
                            _dot3(self, cols[2]))
            elif other._matrix_cols == 4:
                return vec4(_dot3(self, cols[0]),
                            _dot3(self, cols[1]),
                            _dot3(self, cols[2]),
                            _dot3(self, cols[3]))

        if not hasattr(other, '_vector_components'):
            # Component-wise scalar *
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x * (other),
                self.y * (other),
                self.z * (other),
            )
        else:
            # Component-wise vector *
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x * (other.x),
                self.y * (other.y),
                self.z * (other.z),
            )

    def __div__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar /
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x / (other),
                self.y / (other),
                self.z / (other),
            )
        else:
            # Component-wise vector /
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x / (other.x),
                self.y / (other.y),
                self.z / (other.z),
            )

    def __truediv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar .__truediv__
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x .__truediv__ (other),
                self.y .__truediv__ (other),
                self.z .__truediv__ (other),
            )
        else:
            # Component-wise vector .__truediv__
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x .__truediv__ (other.x),
                self.y .__truediv__ (other.y),
                self.z .__truediv__ (other.z),
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar //
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x // (other),
                self.y // (other),
                self.z // (other),
            )
        else:
            # Component-wise vector //
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x // (other.x),
                self.y // (other.y),
                self.z // (other.z),
            )

    def __radd__(self, other):
        # Component-wise scalar +
        return self._vector_upcast_scalar_rtype[type(other)](
            other + (self.x),
            other + (self.y),
            other + (self.z),
        )

    def __rsub__(self, other):
        # Component-wise scalar -
        return self._vector_upcast_scalar_rtype[type(other)](
            other - (self.x),
            other - (self.y),
            other - (self.z),
        )

    def __rmul__(self, other):
        # Component-wise scalar *
        return self._vector_upcast_scalar_rtype[type(other)](
            other * (self.x),
            other * (self.y),
            other * (self.z),
        )

    def __rdiv__(self, other):
        # Component-wise scalar /
        return self._vector_upcast_scalar_rtype[type(other)](
            other / (self.x),
            other / (self.y),
            other / (self.z),
        )

    def __rtruediv__(self, other):
        # Component-wise scalar .__truediv__
        return self._vector_upcast_scalar_rtype[type(other)](
            other .__truediv__ (self.x),
            other .__truediv__ (self.y),
            other .__truediv__ (self.z),
        )

    def __rfloordiv__(self, other):
        # Component-wise scalar //
        return self._vector_upcast_scalar_rtype[type(other)](
            other // (self.x),
            other // (self.y),
            other // (self.z),
        )

    def __neg__(self):
        # Component-wise scalar -
        return bvec3(
            - self.x,
            - self.y,
            - self.z,
        )

    def __pos__(self):
        # Component-wise scalar +
        return bvec3(
            + self.x,
            + self.y,
            + self.z,
        )

    def __eq__(self, other):
        if not hasattr(other, '_vector_components') or other._vector_components != self._vector_components:
            return False
        else:
            # Component-wise vector equality check
            return (self.x == other.x
                and self.y == other.y
                and self.z == other.z
            )

    def __ne__(self, other):
        if hasattr(other, '_vector_components') and other._vector_components == self._vector_components:
            # Component-wise vector equality check
            return (self.x != other.x
                 or self.y != other.y
                 or self.z != other.z
            )
        else:
            return True

    def _outer_product(self, other):
        col = self[:]
        row = other[:]
        cols = len(row)
        if cols == 2:
            return mat2x3(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
            )
        elif cols == 3:
            return mat3x3(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
                    col[2] * row[0],
                    col[2] * row[1],
                    col[2] * row[2],
            )
        elif cols == 4:
            return mat4x3(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
                    col[2] * row[0],
                    col[2] * row[1],
                    col[2] * row[2],
                    col[3] * row[0],
                    col[3] * row[1],
                    col[3] * row[2],
            )

def _unwrapbvec4args(args):
    if not args:
        # Identity constructor
        yield bool(0)
        yield bool(0)
        yield bool(0)
        yield bool(1)

    elif len(args) == 1:
        arg = args[0]
        if hasattr(arg, '_vector_components'):
            # Copy constructor with optional truncation
            yield arg.x
            yield arg.y
            yield arg.z
            yield arg.w
        else:
            # Unit scalar cast and replication
            yield bool(arg)
            yield bool(arg)
            yield bool(arg)
            yield bool(arg)

    else:
        # Initialize components sequentially from all arguments.
        for arg in args:
            argtype = type(arg)
            if argtype is bool:
                # Fast path for common case -- scalar component
                yield arg
            else:
                try:
                    components = arg._vector_components
                except AttributeError:
                    # Cast scalar component
                    yield bool(arg)
                    continue

                # Component-wise cast components
                yield bool(arg.x)
                yield bool(arg.y)
                if components >= 3:
                    yield bool(arg.z)
                    if components == 4:
                        yield bool(arg.w)

class bvec4(object):
    _vector_components = 4
    __slots__ = tuple('xyzw')

    _vector_base_type = 'bvec'

    def __init__(self, *args):
        self.x, self.y, self.z, self.w = _unwrapbvec4args(args)

    def __repr__(self):
        return 'bvec4%r' % (self[:],)

    def __getitem__(self, index):
        return (
            self.x,
            self.y,
            self.z,
            self.w,
        )[index]

    def __setitem__(self, index, value):
        if index == 0:
            self.x = value
        elif index == 1:
            self.y = value
        elif index == 2:
            self.z = value
        elif index == 3:
            self.w = value

    def __len__(self):
        return 4

    def __add__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar +
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x + (other),
                self.y + (other),
                self.z + (other),
                self.w + (other)
            )
        else:
            # Component-wise vector +
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x + (other.x),
                self.y + (other.y),
                self.z + (other.z),
                self.w + (other.w)
            )

    def __sub__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar -
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x - (other),
                self.y - (other),
                self.z - (other),
                self.w - (other)
            )
        else:
            # Component-wise vector -
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x - (other.x),
                self.y - (other.y),
                self.z - (other.z),
                self.w - (other.w)
            )

    def __mul__(self, other):
        if hasattr(other, '_matrix_rows'):
            # row vector * matrix
            cols = other._cols
            assert other._matrix_rows == 4, 'Vector and matrix must have compatible size'
            if other._matrix_cols == 2:
                return vec2(_dot4(self, cols[0]),
                            _dot4(self, cols[1]))
            elif other._matrix_cols == 3:
                return vec3(_dot4(self, cols[0]),
                            _dot4(self, cols[1]),
                            _dot4(self, cols[2]))
            elif other._matrix_cols == 4:
                return vec4(_dot4(self, cols[0]),
                            _dot4(self, cols[1]),
                            _dot4(self, cols[2]),
                            _dot4(self, cols[3]))

        if not hasattr(other, '_vector_components'):
            # Component-wise scalar *
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x * (other),
                self.y * (other),
                self.z * (other),
                self.w * (other)
            )
        else:
            # Component-wise vector *
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x * (other.x),
                self.y * (other.y),
                self.z * (other.z),
                self.w * (other.w)
            )

    def __div__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar /
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x / (other),
                self.y / (other),
                self.z / (other),
                self.w / (other)
            )
        else:
            # Component-wise vector /
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x / (other.x),
                self.y / (other.y),
                self.z / (other.z),
                self.w / (other.w)
            )

    def __truediv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar .__truediv__
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x .__truediv__ (other),
                self.y .__truediv__ (other),
                self.z .__truediv__ (other),
                self.w .__truediv__ (other)
            )
        else:
            # Component-wise vector .__truediv__
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x .__truediv__ (other.x),
                self.y .__truediv__ (other.y),
                self.z .__truediv__ (other.z),
                self.w .__truediv__ (other.w)
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_vector_components'):
            # Component-wise scalar //
            return self._vector_upcast_scalar_rtype[type(other)](
                self.x // (other),
                self.y // (other),
                self.z // (other),
                self.w // (other)
            )
        else:
            # Component-wise vector //
            return self._vector_upcast_vector_rtype[other._vector_base_type](
                self.x // (other.x),
                self.y // (other.y),
                self.z // (other.z),
                self.w // (other.w)
            )

    def __radd__(self, other):
        # Component-wise scalar +
        return self._vector_upcast_scalar_rtype[type(other)](
            other + (self.x),
            other + (self.y),
            other + (self.z),
            other + (self.w)
        )

    def __rsub__(self, other):
        # Component-wise scalar -
        return self._vector_upcast_scalar_rtype[type(other)](
            other - (self.x),
            other - (self.y),
            other - (self.z),
            other - (self.w)
        )

    def __rmul__(self, other):
        # Component-wise scalar *
        return self._vector_upcast_scalar_rtype[type(other)](
            other * (self.x),
            other * (self.y),
            other * (self.z),
            other * (self.w)
        )

    def __rdiv__(self, other):
        # Component-wise scalar /
        return self._vector_upcast_scalar_rtype[type(other)](
            other / (self.x),
            other / (self.y),
            other / (self.z),
            other / (self.w)
        )

    def __rtruediv__(self, other):
        # Component-wise scalar .__truediv__
        return self._vector_upcast_scalar_rtype[type(other)](
            other .__truediv__ (self.x),
            other .__truediv__ (self.y),
            other .__truediv__ (self.z),
            other .__truediv__ (self.w)
        )

    def __rfloordiv__(self, other):
        # Component-wise scalar //
        return self._vector_upcast_scalar_rtype[type(other)](
            other // (self.x),
            other // (self.y),
            other // (self.z),
            other // (self.w)
        )

    def __neg__(self):
        # Component-wise scalar -
        return bvec4(
            - self.x,
            - self.y,
            - self.z,
            - self.w
        )

    def __pos__(self):
        # Component-wise scalar +
        return bvec4(
            + self.x,
            + self.y,
            + self.z,
            + self.w
        )

    def __eq__(self, other):
        if not hasattr(other, '_vector_components') or other._vector_components != self._vector_components:
            return False
        else:
            # Component-wise vector equality check
            return (self.x == other.x
                and self.y == other.y
                and self.z == other.z
                and self.w == other.w
            )

    def __ne__(self, other):
        if hasattr(other, '_vector_components') and other._vector_components == self._vector_components:
            # Component-wise vector equality check
            return (self.x != other.x
                 or self.y != other.y
                 or self.z != other.z
                 or self.w != other.w
            )
        else:
            return True

    def _outer_product(self, other):
        col = self[:]
        row = other[:]
        cols = len(row)
        if cols == 2:
            return mat2x4(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[0] * row[3],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
                    col[1] * row[3],
            )
        elif cols == 3:
            return mat3x4(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[0] * row[3],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
                    col[1] * row[3],
                    col[2] * row[0],
                    col[2] * row[1],
                    col[2] * row[2],
                    col[2] * row[3],
            )
        elif cols == 4:
            return mat4x4(
                    col[0] * row[0],
                    col[0] * row[1],
                    col[0] * row[2],
                    col[0] * row[3],
                    col[1] * row[0],
                    col[1] * row[1],
                    col[1] * row[2],
                    col[1] * row[3],
                    col[2] * row[0],
                    col[2] * row[1],
                    col[2] * row[2],
                    col[2] * row[3],
                    col[3] * row[0],
                    col[3] * row[1],
                    col[3] * row[2],
                    col[3] * row[3],
            )


vec2._vector_upcast_scalar_rtype = {
    float: vec2,
    int:   vec2,
    bool:  vec2,
}
vec2._vector_upcast_vector_rtype = {
    'vec':   vec2,
    'ivec':  vec2,
    'bvec':  vec2,
}
vec3._vector_upcast_scalar_rtype = {
    float: vec3,
    int:   vec3,
    bool:  vec3,
}
vec3._vector_upcast_vector_rtype = {
    'vec':   vec3,
    'ivec':  vec3,
    'bvec':  vec3,
}
vec4._vector_upcast_scalar_rtype = {
    float: vec4,
    int:   vec4,
    bool:  vec4,
}
vec4._vector_upcast_vector_rtype = {
    'vec':   vec4,
    'ivec':  vec4,
    'bvec':  vec4,
}
ivec2._vector_upcast_scalar_rtype = {
    float: vec2,
    int:   ivec2,
    bool:  ivec2,
}
ivec2._vector_upcast_vector_rtype = {
    'vec':   vec2,
    'ivec':  ivec2,
    'bvec':  ivec2,
}
ivec3._vector_upcast_scalar_rtype = {
    float: vec3,
    int:   ivec3,
    bool:  ivec3,
}
ivec3._vector_upcast_vector_rtype = {
    'vec':   vec3,
    'ivec':  ivec3,
    'bvec':  ivec3,
}
ivec4._vector_upcast_scalar_rtype = {
    float: vec4,
    int:   ivec4,
    bool:  ivec4,
}
ivec4._vector_upcast_vector_rtype = {
    'vec':   vec4,
    'ivec':  ivec4,
    'bvec':  ivec4,
}
bvec2._vector_upcast_scalar_rtype = {
    float: vec2,
    int:   ivec2,
    bool:  bvec2,
}
bvec2._vector_upcast_vector_rtype = {
    'vec':   vec2,
    'ivec':  ivec2,
    'bvec':  bvec2,
}
bvec3._vector_upcast_scalar_rtype = {
    float: vec3,
    int:   ivec3,
    bool:  bvec3,
}
bvec3._vector_upcast_vector_rtype = {
    'vec':   vec3,
    'ivec':  ivec3,
    'bvec':  bvec3,
}
bvec4._vector_upcast_scalar_rtype = {
    float: vec4,
    int:   ivec4,
    bool:  bvec4,
}
bvec4._vector_upcast_vector_rtype = {
    'vec':   vec4,
    'ivec':  ivec4,
    'bvec':  bvec4,
}

def _unwrap_matrix_args(args):
    # Initialize components sequentially from all arguments.
    for arg in args:
        argtype = type(arg)
        if argtype is float:
            # Fast path for common case -- scalar component
            yield arg
        else:
            try:
                components = arg._vector_components
            except AttributeError:
                # Cast scalar component
                yield float(arg)
                continue

            # Component-wise cast components
            yield float(arg.x)
            yield float(arg.y)
            if components >= 3:
                yield float(arg.z)
                if components == 4:
                    yield float(arg.w)









class mat2x2(object):
    _matrix_cols = 2
    _matrix_rows = 2

    __slots__ = '_cols'

    def __init__(self, *args):
        if not args:
            self._init_diagonal(1.0)
        elif len(args) == 1:
            arg = args[0]
            if hasattr(arg, '_matrix_cols'):
                # Initialise from another matrix
                self._init_diagonal(1.0)
                for col in range(min(2, arg._matrix_cols)):
                    arg_col = arg._cols[col]
                    self_col = self._cols[col]
                    for row in range(min(2, arg._matrix_rows)):
                        self_col[row] = arg_col[row]
            else:
                self._init_diagonal(float(arg))
        else:
            components = list(_unwrap_matrix_args(args))
            self._cols = [
                vec2(*components[0:2]),
                vec2(*components[2:4]),
            ]

    def _init_diagonal(self, scalar):
        # Identity constructor
        self._cols = [
          vec2(
                    scalar,
                    0.0,
          ),
          vec2(
                    0.0,
                    scalar,
          ),
        ]

    def __repr__(self):
        return 'mat2x2%r' % (tuple(self._cols),)

    def pformat(self, indent=0):
        return '\n'.join([
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][0] +
                '%6.2f ' % self._cols[1][0] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][1] +
                '%6.2f ' % self._cols[1][1] +
            ']',
        ])

    def pprint(self, indent=0):
        print self.pformat(indent)

    def __getitem__(self, index):
        return self._cols[index]

    def __setitem__(self, index, value):
        self._cols[index] = value

    def __add__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar +
            return mat2x2(
                self._cols[0] + (other),
                self._cols[1] + (other),
            )
        else:
            # Component-wise matrix +
            return mat2x2(
                self._cols[0] + (other._cols[0]),
                self._cols[1] + (other._cols[1]),
            )

    def __sub__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar -
            return mat2x2(
                self._cols[0] - (other),
                self._cols[1] - (other),
            )
        else:
            # Component-wise matrix -
            return mat2x2(
                self._cols[0] - (other._cols[0]),
                self._cols[1] - (other._cols[1]),
            )

    def __mul__(self, other):
        if hasattr(other, '_vector_components'):
            # matrix * column vector
            assert other._vector_components == 2
            return vec2(
                  self._cols[0][0] * other.x
                + self._cols[1][0] * other.y
                ,
                  self._cols[0][1] * other.x
                + self._cols[1][1] * other.y
                ,
            )
        elif hasattr(other, '_matrix_rows'):
            # matrix * matrix
            assert other._matrix_rows == 2
            a = self._cols
            b = other._cols
            if other._matrix_cols == 2:
                return mat2x2(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                ,
                )
            elif other._matrix_cols == 3:
                return mat3x2(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                ,
                )
            elif other._matrix_cols == 4:
                return mat4x2(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                ,
                      a[0][0] * b[3][0]
                    + a[1][0] * b[3][1]
                ,
                      a[0][1] * b[3][0]
                    + a[1][1] * b[3][1]
                ,
                )

        # Component-wise scalar *
        return mat2x2(
            self._cols[0] * (other),
            self._cols[1] * (other),
        )

    def _comp_mul(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar *
            return mat2x2(
                self._cols[0] * (other),
                self._cols[1] * (other),
            )
        else:
            # Component-wise matrix *
            return mat2x2(
                self._cols[0] * (other._cols[0]),
                self._cols[1] * (other._cols[1]),
            )

    def __div__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar /
            return mat2x2(
                self._cols[0] / (other),
                self._cols[1] / (other),
            )
        else:
            # Component-wise matrix /
            return mat2x2(
                self._cols[0] / (other._cols[0]),
                self._cols[1] / (other._cols[1]),
            )

    def __truediv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar .__truediv__
            return mat2x2(
                self._cols[0] .__truediv__ (other),
                self._cols[1] .__truediv__ (other),
            )
        else:
            # Component-wise matrix .__truediv__
            return mat2x2(
                self._cols[0] .__truediv__ (other._cols[0]),
                self._cols[1] .__truediv__ (other._cols[1]),
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar //
            return mat2x2(
                self._cols[0] // (other),
                self._cols[1] // (other),
            )
        else:
            # Component-wise matrix //
            return mat2x2(
                self._cols[0] // (other._cols[0]),
                self._cols[1] // (other._cols[1]),
            )

    def __radd__(self, other):
        # Component-wise rev scalar +
        return mat2x2(
            other + (self._cols[0]),
            other + (self._cols[1]),
        )

    def __rsub__(self, other):
        # Component-wise rev scalar -
        return mat2x2(
            other - (self._cols[0]),
            other - (self._cols[1]),
        )

    def __rmul__(self, other):
        # Component-wise rev scalar *
        return mat2x2(
            other * (self._cols[0]),
            other * (self._cols[1]),
        )

    def __rdiv__(self, other):
        # Component-wise rev scalar /
        return mat2x2(
            other / (self._cols[0]),
            other / (self._cols[1]),
        )

    def __rtruediv__(self, other):
        # Component-wise rev scalar .__truediv__
        return mat2x2(
            other .__truediv__ (self._cols[0]),
            other .__truediv__ (self._cols[1]),
        )

    def __rfloordiv__(self, other):
        # Component-wise rev scalar //
        return mat2x2(
            other // (self._cols[0]),
            other // (self._cols[1]),
        )

    def __neg__(self):
        # Component-wise rev scalar -
        return mat2x2(
            - (self._cols[0]),
            - (self._cols[1]),
        )
        pass

    def __pos__(self):
        # Component-wise rev scalar +
        return mat2x2(
            + (self._cols[0]),
            + (self._cols[1]),
        )
        pass

    def __eq__(self, other):
        return type(other) is type(self) and self._cols == other._cols

    def __ne__(self, other):
        return type(other) is not type(self) or self._cols != other._cols

    def _transpose(self):
        cols = self._cols
        return mat2x2(
                   cols[0][0],
                   cols[1][0],
                   cols[0][1],
                   cols[1][1],
        )

mat2 = mat2x2

class mat2x3(object):
    _matrix_cols = 2
    _matrix_rows = 3

    __slots__ = '_cols'

    def __init__(self, *args):
        if not args:
            self._init_diagonal(1.0)
        elif len(args) == 1:
            arg = args[0]
            if hasattr(arg, '_matrix_cols'):
                # Initialise from another matrix
                self._init_diagonal(1.0)
                for col in range(min(2, arg._matrix_cols)):
                    arg_col = arg._cols[col]
                    self_col = self._cols[col]
                    for row in range(min(3, arg._matrix_rows)):
                        self_col[row] = arg_col[row]
            else:
                self._init_diagonal(float(arg))
        else:
            components = list(_unwrap_matrix_args(args))
            self._cols = [
                vec3(*components[0:3]),
                vec3(*components[3:6]),
            ]

    def _init_diagonal(self, scalar):
        # Identity constructor
        self._cols = [
          vec3(
                    scalar,
                    0.0,
                    0.0,
          ),
          vec3(
                    0.0,
                    scalar,
                    0.0,
          ),
        ]

    def __repr__(self):
        return 'mat2x3%r' % (tuple(self._cols),)

    def pformat(self, indent=0):
        return '\n'.join([
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][0] +
                '%6.2f ' % self._cols[1][0] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][1] +
                '%6.2f ' % self._cols[1][1] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][2] +
                '%6.2f ' % self._cols[1][2] +
            ']',
        ])

    def pprint(self, indent=0):
        print self.pformat(indent)

    def __getitem__(self, index):
        return self._cols[index]

    def __setitem__(self, index, value):
        self._cols[index] = value

    def __add__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar +
            return mat2x3(
                self._cols[0] + (other),
                self._cols[1] + (other),
            )
        else:
            # Component-wise matrix +
            return mat2x3(
                self._cols[0] + (other._cols[0]),
                self._cols[1] + (other._cols[1]),
            )

    def __sub__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar -
            return mat2x3(
                self._cols[0] - (other),
                self._cols[1] - (other),
            )
        else:
            # Component-wise matrix -
            return mat2x3(
                self._cols[0] - (other._cols[0]),
                self._cols[1] - (other._cols[1]),
            )

    def __mul__(self, other):
        if hasattr(other, '_vector_components'):
            # matrix * column vector
            assert other._vector_components == 2
            return vec3(
                  self._cols[0][0] * other.x
                + self._cols[1][0] * other.y
                ,
                  self._cols[0][1] * other.x
                + self._cols[1][1] * other.y
                ,
                  self._cols[0][2] * other.x
                + self._cols[1][2] * other.y
                ,
            )
        elif hasattr(other, '_matrix_rows'):
            # matrix * matrix
            assert other._matrix_rows == 2
            a = self._cols
            b = other._cols
            if other._matrix_cols == 2:
                return mat2x3(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                ,
                )
            elif other._matrix_cols == 3:
                return mat3x3(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                ,
                      a[0][2] * b[2][0]
                    + a[1][2] * b[2][1]
                ,
                )
            elif other._matrix_cols == 4:
                return mat4x3(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                ,
                      a[0][2] * b[2][0]
                    + a[1][2] * b[2][1]
                ,
                      a[0][0] * b[3][0]
                    + a[1][0] * b[3][1]
                ,
                      a[0][1] * b[3][0]
                    + a[1][1] * b[3][1]
                ,
                      a[0][2] * b[3][0]
                    + a[1][2] * b[3][1]
                ,
                )

        # Component-wise scalar *
        return mat2x3(
            self._cols[0] * (other),
            self._cols[1] * (other),
        )

    def _comp_mul(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar *
            return mat2x3(
                self._cols[0] * (other),
                self._cols[1] * (other),
            )
        else:
            # Component-wise matrix *
            return mat2x3(
                self._cols[0] * (other._cols[0]),
                self._cols[1] * (other._cols[1]),
            )

    def __div__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar /
            return mat2x3(
                self._cols[0] / (other),
                self._cols[1] / (other),
            )
        else:
            # Component-wise matrix /
            return mat2x3(
                self._cols[0] / (other._cols[0]),
                self._cols[1] / (other._cols[1]),
            )

    def __truediv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar .__truediv__
            return mat2x3(
                self._cols[0] .__truediv__ (other),
                self._cols[1] .__truediv__ (other),
            )
        else:
            # Component-wise matrix .__truediv__
            return mat2x3(
                self._cols[0] .__truediv__ (other._cols[0]),
                self._cols[1] .__truediv__ (other._cols[1]),
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar //
            return mat2x3(
                self._cols[0] // (other),
                self._cols[1] // (other),
            )
        else:
            # Component-wise matrix //
            return mat2x3(
                self._cols[0] // (other._cols[0]),
                self._cols[1] // (other._cols[1]),
            )

    def __radd__(self, other):
        # Component-wise rev scalar +
        return mat2x3(
            other + (self._cols[0]),
            other + (self._cols[1]),
        )

    def __rsub__(self, other):
        # Component-wise rev scalar -
        return mat2x3(
            other - (self._cols[0]),
            other - (self._cols[1]),
        )

    def __rmul__(self, other):
        # Component-wise rev scalar *
        return mat2x3(
            other * (self._cols[0]),
            other * (self._cols[1]),
        )

    def __rdiv__(self, other):
        # Component-wise rev scalar /
        return mat2x3(
            other / (self._cols[0]),
            other / (self._cols[1]),
        )

    def __rtruediv__(self, other):
        # Component-wise rev scalar .__truediv__
        return mat2x3(
            other .__truediv__ (self._cols[0]),
            other .__truediv__ (self._cols[1]),
        )

    def __rfloordiv__(self, other):
        # Component-wise rev scalar //
        return mat2x3(
            other // (self._cols[0]),
            other // (self._cols[1]),
        )

    def __neg__(self):
        # Component-wise rev scalar -
        return mat2x3(
            - (self._cols[0]),
            - (self._cols[1]),
        )
        pass

    def __pos__(self):
        # Component-wise rev scalar +
        return mat2x3(
            + (self._cols[0]),
            + (self._cols[1]),
        )
        pass

    def __eq__(self, other):
        return type(other) is type(self) and self._cols == other._cols

    def __ne__(self, other):
        return type(other) is not type(self) or self._cols != other._cols

    def _transpose(self):
        cols = self._cols
        return mat3x2(
                   cols[0][0],
                   cols[1][0],
                   cols[0][1],
                   cols[1][1],
                   cols[0][2],
                   cols[1][2],
        )


class mat3x3(object):
    _matrix_cols = 3
    _matrix_rows = 3

    __slots__ = '_cols'

    def __init__(self, *args):
        if not args:
            self._init_diagonal(1.0)
        elif len(args) == 1:
            arg = args[0]
            if hasattr(arg, '_matrix_cols'):
                # Initialise from another matrix
                self._init_diagonal(1.0)
                for col in range(min(3, arg._matrix_cols)):
                    arg_col = arg._cols[col]
                    self_col = self._cols[col]
                    for row in range(min(3, arg._matrix_rows)):
                        self_col[row] = arg_col[row]
            else:
                self._init_diagonal(float(arg))
        else:
            components = list(_unwrap_matrix_args(args))
            self._cols = [
                vec3(*components[0:3]),
                vec3(*components[3:6]),
                vec3(*components[6:9]),
            ]

    def _init_diagonal(self, scalar):
        # Identity constructor
        self._cols = [
          vec3(
                    scalar,
                    0.0,
                    0.0,
          ),
          vec3(
                    0.0,
                    scalar,
                    0.0,
          ),
          vec3(
                    0.0,
                    0.0,
                    scalar,
          ),
        ]

    def __repr__(self):
        return 'mat3x3%r' % (tuple(self._cols),)

    def pformat(self, indent=0):
        return '\n'.join([
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][0] +
                '%6.2f ' % self._cols[1][0] +
                '%6.2f ' % self._cols[2][0] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][1] +
                '%6.2f ' % self._cols[1][1] +
                '%6.2f ' % self._cols[2][1] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][2] +
                '%6.2f ' % self._cols[1][2] +
                '%6.2f ' % self._cols[2][2] +
            ']',
        ])

    def pprint(self, indent=0):
        print self.pformat(indent)

    def __getitem__(self, index):
        return self._cols[index]

    def __setitem__(self, index, value):
        self._cols[index] = value

    def __add__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar +
            return mat3x3(
                self._cols[0] + (other),
                self._cols[1] + (other),
                self._cols[2] + (other),
            )
        else:
            # Component-wise matrix +
            return mat3x3(
                self._cols[0] + (other._cols[0]),
                self._cols[1] + (other._cols[1]),
                self._cols[2] + (other._cols[2]),
            )

    def __sub__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar -
            return mat3x3(
                self._cols[0] - (other),
                self._cols[1] - (other),
                self._cols[2] - (other),
            )
        else:
            # Component-wise matrix -
            return mat3x3(
                self._cols[0] - (other._cols[0]),
                self._cols[1] - (other._cols[1]),
                self._cols[2] - (other._cols[2]),
            )

    def __mul__(self, other):
        if hasattr(other, '_vector_components'):
            # matrix * column vector
            assert other._vector_components == 3
            return vec3(
                  self._cols[0][0] * other.x
                + self._cols[1][0] * other.y
                + self._cols[2][0] * other.z
                ,
                  self._cols[0][1] * other.x
                + self._cols[1][1] * other.y
                + self._cols[2][1] * other.z
                ,
                  self._cols[0][2] * other.x
                + self._cols[1][2] * other.y
                + self._cols[2][2] * other.z
                ,
            )
        elif hasattr(other, '_matrix_rows'):
            # matrix * matrix
            assert other._matrix_rows == 3
            a = self._cols
            b = other._cols
            if other._matrix_cols == 2:
                return mat2x3(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                    + a[2][2] * b[0][2]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                    + a[2][2] * b[1][2]
                ,
                )
            elif other._matrix_cols == 3:
                return mat3x3(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                    + a[2][2] * b[0][2]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                    + a[2][2] * b[1][2]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                    + a[2][0] * b[2][2]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                    + a[2][1] * b[2][2]
                ,
                      a[0][2] * b[2][0]
                    + a[1][2] * b[2][1]
                    + a[2][2] * b[2][2]
                ,
                )
            elif other._matrix_cols == 4:
                return mat4x3(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                    + a[2][2] * b[0][2]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                    + a[2][2] * b[1][2]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                    + a[2][0] * b[2][2]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                    + a[2][1] * b[2][2]
                ,
                      a[0][2] * b[2][0]
                    + a[1][2] * b[2][1]
                    + a[2][2] * b[2][2]
                ,
                      a[0][0] * b[3][0]
                    + a[1][0] * b[3][1]
                    + a[2][0] * b[3][2]
                ,
                      a[0][1] * b[3][0]
                    + a[1][1] * b[3][1]
                    + a[2][1] * b[3][2]
                ,
                      a[0][2] * b[3][0]
                    + a[1][2] * b[3][1]
                    + a[2][2] * b[3][2]
                ,
                )

        # Component-wise scalar *
        return mat3x3(
            self._cols[0] * (other),
            self._cols[1] * (other),
            self._cols[2] * (other),
        )

    def _comp_mul(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar *
            return mat3x3(
                self._cols[0] * (other),
                self._cols[1] * (other),
                self._cols[2] * (other),
            )
        else:
            # Component-wise matrix *
            return mat3x3(
                self._cols[0] * (other._cols[0]),
                self._cols[1] * (other._cols[1]),
                self._cols[2] * (other._cols[2]),
            )

    def __div__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar /
            return mat3x3(
                self._cols[0] / (other),
                self._cols[1] / (other),
                self._cols[2] / (other),
            )
        else:
            # Component-wise matrix /
            return mat3x3(
                self._cols[0] / (other._cols[0]),
                self._cols[1] / (other._cols[1]),
                self._cols[2] / (other._cols[2]),
            )

    def __truediv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar .__truediv__
            return mat3x3(
                self._cols[0] .__truediv__ (other),
                self._cols[1] .__truediv__ (other),
                self._cols[2] .__truediv__ (other),
            )
        else:
            # Component-wise matrix .__truediv__
            return mat3x3(
                self._cols[0] .__truediv__ (other._cols[0]),
                self._cols[1] .__truediv__ (other._cols[1]),
                self._cols[2] .__truediv__ (other._cols[2]),
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar //
            return mat3x3(
                self._cols[0] // (other),
                self._cols[1] // (other),
                self._cols[2] // (other),
            )
        else:
            # Component-wise matrix //
            return mat3x3(
                self._cols[0] // (other._cols[0]),
                self._cols[1] // (other._cols[1]),
                self._cols[2] // (other._cols[2]),
            )

    def __radd__(self, other):
        # Component-wise rev scalar +
        return mat3x3(
            other + (self._cols[0]),
            other + (self._cols[1]),
            other + (self._cols[2]),
        )

    def __rsub__(self, other):
        # Component-wise rev scalar -
        return mat3x3(
            other - (self._cols[0]),
            other - (self._cols[1]),
            other - (self._cols[2]),
        )

    def __rmul__(self, other):
        # Component-wise rev scalar *
        return mat3x3(
            other * (self._cols[0]),
            other * (self._cols[1]),
            other * (self._cols[2]),
        )

    def __rdiv__(self, other):
        # Component-wise rev scalar /
        return mat3x3(
            other / (self._cols[0]),
            other / (self._cols[1]),
            other / (self._cols[2]),
        )

    def __rtruediv__(self, other):
        # Component-wise rev scalar .__truediv__
        return mat3x3(
            other .__truediv__ (self._cols[0]),
            other .__truediv__ (self._cols[1]),
            other .__truediv__ (self._cols[2]),
        )

    def __rfloordiv__(self, other):
        # Component-wise rev scalar //
        return mat3x3(
            other // (self._cols[0]),
            other // (self._cols[1]),
            other // (self._cols[2]),
        )

    def __neg__(self):
        # Component-wise rev scalar -
        return mat3x3(
            - (self._cols[0]),
            - (self._cols[1]),
            - (self._cols[2]),
        )
        pass

    def __pos__(self):
        # Component-wise rev scalar +
        return mat3x3(
            + (self._cols[0]),
            + (self._cols[1]),
            + (self._cols[2]),
        )
        pass

    def __eq__(self, other):
        return type(other) is type(self) and self._cols == other._cols

    def __ne__(self, other):
        return type(other) is not type(self) or self._cols != other._cols

    def _transpose(self):
        cols = self._cols
        return mat3x3(
                   cols[0][0],
                   cols[1][0],
                   cols[2][0],
                   cols[0][1],
                   cols[1][1],
                   cols[2][1],
                   cols[0][2],
                   cols[1][2],
                   cols[2][2],
        )


class mat3x2(object):
    _matrix_cols = 3
    _matrix_rows = 2

    __slots__ = '_cols'

    def __init__(self, *args):
        if not args:
            self._init_diagonal(1.0)
        elif len(args) == 1:
            arg = args[0]
            if hasattr(arg, '_matrix_cols'):
                # Initialise from another matrix
                self._init_diagonal(1.0)
                for col in range(min(3, arg._matrix_cols)):
                    arg_col = arg._cols[col]
                    self_col = self._cols[col]
                    for row in range(min(2, arg._matrix_rows)):
                        self_col[row] = arg_col[row]
            else:
                self._init_diagonal(float(arg))
        else:
            components = list(_unwrap_matrix_args(args))
            self._cols = [
                vec2(*components[0:2]),
                vec2(*components[2:4]),
                vec2(*components[4:6]),
            ]

    def _init_diagonal(self, scalar):
        # Identity constructor
        self._cols = [
          vec2(
                    scalar,
                    0.0,
          ),
          vec2(
                    0.0,
                    scalar,
          ),
          vec2(
                    0.0,
                    0.0,
          ),
        ]

    def __repr__(self):
        return 'mat3x2%r' % (tuple(self._cols),)

    def pformat(self, indent=0):
        return '\n'.join([
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][0] +
                '%6.2f ' % self._cols[1][0] +
                '%6.2f ' % self._cols[2][0] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][1] +
                '%6.2f ' % self._cols[1][1] +
                '%6.2f ' % self._cols[2][1] +
            ']',
        ])

    def pprint(self, indent=0):
        print self.pformat(indent)

    def __getitem__(self, index):
        return self._cols[index]

    def __setitem__(self, index, value):
        self._cols[index] = value

    def __add__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar +
            return mat3x2(
                self._cols[0] + (other),
                self._cols[1] + (other),
                self._cols[2] + (other),
            )
        else:
            # Component-wise matrix +
            return mat3x2(
                self._cols[0] + (other._cols[0]),
                self._cols[1] + (other._cols[1]),
                self._cols[2] + (other._cols[2]),
            )

    def __sub__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar -
            return mat3x2(
                self._cols[0] - (other),
                self._cols[1] - (other),
                self._cols[2] - (other),
            )
        else:
            # Component-wise matrix -
            return mat3x2(
                self._cols[0] - (other._cols[0]),
                self._cols[1] - (other._cols[1]),
                self._cols[2] - (other._cols[2]),
            )

    def __mul__(self, other):
        if hasattr(other, '_vector_components'):
            # matrix * column vector
            assert other._vector_components == 3
            return vec2(
                  self._cols[0][0] * other.x
                + self._cols[1][0] * other.y
                + self._cols[2][0] * other.z
                ,
                  self._cols[0][1] * other.x
                + self._cols[1][1] * other.y
                + self._cols[2][1] * other.z
                ,
            )
        elif hasattr(other, '_matrix_rows'):
            # matrix * matrix
            assert other._matrix_rows == 3
            a = self._cols
            b = other._cols
            if other._matrix_cols == 2:
                return mat2x2(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                ,
                )
            elif other._matrix_cols == 3:
                return mat3x2(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                    + a[2][0] * b[2][2]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                    + a[2][1] * b[2][2]
                ,
                )
            elif other._matrix_cols == 4:
                return mat4x2(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                    + a[2][0] * b[2][2]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                    + a[2][1] * b[2][2]
                ,
                      a[0][0] * b[3][0]
                    + a[1][0] * b[3][1]
                    + a[2][0] * b[3][2]
                ,
                      a[0][1] * b[3][0]
                    + a[1][1] * b[3][1]
                    + a[2][1] * b[3][2]
                ,
                )

        # Component-wise scalar *
        return mat3x2(
            self._cols[0] * (other),
            self._cols[1] * (other),
            self._cols[2] * (other),
        )

    def _comp_mul(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar *
            return mat3x2(
                self._cols[0] * (other),
                self._cols[1] * (other),
                self._cols[2] * (other),
            )
        else:
            # Component-wise matrix *
            return mat3x2(
                self._cols[0] * (other._cols[0]),
                self._cols[1] * (other._cols[1]),
                self._cols[2] * (other._cols[2]),
            )

    def __div__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar /
            return mat3x2(
                self._cols[0] / (other),
                self._cols[1] / (other),
                self._cols[2] / (other),
            )
        else:
            # Component-wise matrix /
            return mat3x2(
                self._cols[0] / (other._cols[0]),
                self._cols[1] / (other._cols[1]),
                self._cols[2] / (other._cols[2]),
            )

    def __truediv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar .__truediv__
            return mat3x2(
                self._cols[0] .__truediv__ (other),
                self._cols[1] .__truediv__ (other),
                self._cols[2] .__truediv__ (other),
            )
        else:
            # Component-wise matrix .__truediv__
            return mat3x2(
                self._cols[0] .__truediv__ (other._cols[0]),
                self._cols[1] .__truediv__ (other._cols[1]),
                self._cols[2] .__truediv__ (other._cols[2]),
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar //
            return mat3x2(
                self._cols[0] // (other),
                self._cols[1] // (other),
                self._cols[2] // (other),
            )
        else:
            # Component-wise matrix //
            return mat3x2(
                self._cols[0] // (other._cols[0]),
                self._cols[1] // (other._cols[1]),
                self._cols[2] // (other._cols[2]),
            )

    def __radd__(self, other):
        # Component-wise rev scalar +
        return mat3x2(
            other + (self._cols[0]),
            other + (self._cols[1]),
            other + (self._cols[2]),
        )

    def __rsub__(self, other):
        # Component-wise rev scalar -
        return mat3x2(
            other - (self._cols[0]),
            other - (self._cols[1]),
            other - (self._cols[2]),
        )

    def __rmul__(self, other):
        # Component-wise rev scalar *
        return mat3x2(
            other * (self._cols[0]),
            other * (self._cols[1]),
            other * (self._cols[2]),
        )

    def __rdiv__(self, other):
        # Component-wise rev scalar /
        return mat3x2(
            other / (self._cols[0]),
            other / (self._cols[1]),
            other / (self._cols[2]),
        )

    def __rtruediv__(self, other):
        # Component-wise rev scalar .__truediv__
        return mat3x2(
            other .__truediv__ (self._cols[0]),
            other .__truediv__ (self._cols[1]),
            other .__truediv__ (self._cols[2]),
        )

    def __rfloordiv__(self, other):
        # Component-wise rev scalar //
        return mat3x2(
            other // (self._cols[0]),
            other // (self._cols[1]),
            other // (self._cols[2]),
        )

    def __neg__(self):
        # Component-wise rev scalar -
        return mat3x2(
            - (self._cols[0]),
            - (self._cols[1]),
            - (self._cols[2]),
        )
        pass

    def __pos__(self):
        # Component-wise rev scalar +
        return mat3x2(
            + (self._cols[0]),
            + (self._cols[1]),
            + (self._cols[2]),
        )
        pass

    def __eq__(self, other):
        return type(other) is type(self) and self._cols == other._cols

    def __ne__(self, other):
        return type(other) is not type(self) or self._cols != other._cols

    def _transpose(self):
        cols = self._cols
        return mat2x3(
                   cols[0][0],
                   cols[1][0],
                   cols[2][0],
                   cols[0][1],
                   cols[1][1],
                   cols[2][1],
        )

mat3 = mat3x3

class mat2x4(object):
    _matrix_cols = 2
    _matrix_rows = 4

    __slots__ = '_cols'

    def __init__(self, *args):
        if not args:
            self._init_diagonal(1.0)
        elif len(args) == 1:
            arg = args[0]
            if hasattr(arg, '_matrix_cols'):
                # Initialise from another matrix
                self._init_diagonal(1.0)
                for col in range(min(2, arg._matrix_cols)):
                    arg_col = arg._cols[col]
                    self_col = self._cols[col]
                    for row in range(min(4, arg._matrix_rows)):
                        self_col[row] = arg_col[row]
            else:
                self._init_diagonal(float(arg))
        else:
            components = list(_unwrap_matrix_args(args))
            self._cols = [
                vec4(*components[0:4]),
                vec4(*components[4:8]),
            ]

    def _init_diagonal(self, scalar):
        # Identity constructor
        self._cols = [
          vec4(
                    scalar,
                    0.0,
                    0.0,
                    0.0,
          ),
          vec4(
                    0.0,
                    scalar,
                    0.0,
                    0.0,
          ),
        ]

    def __repr__(self):
        return 'mat2x4%r' % (tuple(self._cols),)

    def pformat(self, indent=0):
        return '\n'.join([
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][0] +
                '%6.2f ' % self._cols[1][0] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][1] +
                '%6.2f ' % self._cols[1][1] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][2] +
                '%6.2f ' % self._cols[1][2] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][3] +
                '%6.2f ' % self._cols[1][3] +
            ']',
        ])

    def pprint(self, indent=0):
        print self.pformat(indent)

    def __getitem__(self, index):
        return self._cols[index]

    def __setitem__(self, index, value):
        self._cols[index] = value

    def __add__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar +
            return mat2x4(
                self._cols[0] + (other),
                self._cols[1] + (other),
            )
        else:
            # Component-wise matrix +
            return mat2x4(
                self._cols[0] + (other._cols[0]),
                self._cols[1] + (other._cols[1]),
            )

    def __sub__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar -
            return mat2x4(
                self._cols[0] - (other),
                self._cols[1] - (other),
            )
        else:
            # Component-wise matrix -
            return mat2x4(
                self._cols[0] - (other._cols[0]),
                self._cols[1] - (other._cols[1]),
            )

    def __mul__(self, other):
        if hasattr(other, '_vector_components'):
            # matrix * column vector
            assert other._vector_components == 2
            return vec4(
                  self._cols[0][0] * other.x
                + self._cols[1][0] * other.y
                ,
                  self._cols[0][1] * other.x
                + self._cols[1][1] * other.y
                ,
                  self._cols[0][2] * other.x
                + self._cols[1][2] * other.y
                ,
                  self._cols[0][3] * other.x
                + self._cols[1][3] * other.y
                ,
            )
        elif hasattr(other, '_matrix_rows'):
            # matrix * matrix
            assert other._matrix_rows == 2
            a = self._cols
            b = other._cols
            if other._matrix_cols == 2:
                return mat2x4(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                ,
                      a[0][3] * b[0][0]
                    + a[1][3] * b[0][1]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                ,
                      a[0][3] * b[1][0]
                    + a[1][3] * b[1][1]
                ,
                )
            elif other._matrix_cols == 3:
                return mat3x4(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                ,
                      a[0][3] * b[0][0]
                    + a[1][3] * b[0][1]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                ,
                      a[0][3] * b[1][0]
                    + a[1][3] * b[1][1]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                ,
                      a[0][2] * b[2][0]
                    + a[1][2] * b[2][1]
                ,
                      a[0][3] * b[2][0]
                    + a[1][3] * b[2][1]
                ,
                )
            elif other._matrix_cols == 4:
                return mat4x4(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                ,
                      a[0][3] * b[0][0]
                    + a[1][3] * b[0][1]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                ,
                      a[0][3] * b[1][0]
                    + a[1][3] * b[1][1]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                ,
                      a[0][2] * b[2][0]
                    + a[1][2] * b[2][1]
                ,
                      a[0][3] * b[2][0]
                    + a[1][3] * b[2][1]
                ,
                      a[0][0] * b[3][0]
                    + a[1][0] * b[3][1]
                ,
                      a[0][1] * b[3][0]
                    + a[1][1] * b[3][1]
                ,
                      a[0][2] * b[3][0]
                    + a[1][2] * b[3][1]
                ,
                      a[0][3] * b[3][0]
                    + a[1][3] * b[3][1]
                ,
                )

        # Component-wise scalar *
        return mat2x4(
            self._cols[0] * (other),
            self._cols[1] * (other),
        )

    def _comp_mul(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar *
            return mat2x4(
                self._cols[0] * (other),
                self._cols[1] * (other),
            )
        else:
            # Component-wise matrix *
            return mat2x4(
                self._cols[0] * (other._cols[0]),
                self._cols[1] * (other._cols[1]),
            )

    def __div__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar /
            return mat2x4(
                self._cols[0] / (other),
                self._cols[1] / (other),
            )
        else:
            # Component-wise matrix /
            return mat2x4(
                self._cols[0] / (other._cols[0]),
                self._cols[1] / (other._cols[1]),
            )

    def __truediv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar .__truediv__
            return mat2x4(
                self._cols[0] .__truediv__ (other),
                self._cols[1] .__truediv__ (other),
            )
        else:
            # Component-wise matrix .__truediv__
            return mat2x4(
                self._cols[0] .__truediv__ (other._cols[0]),
                self._cols[1] .__truediv__ (other._cols[1]),
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar //
            return mat2x4(
                self._cols[0] // (other),
                self._cols[1] // (other),
            )
        else:
            # Component-wise matrix //
            return mat2x4(
                self._cols[0] // (other._cols[0]),
                self._cols[1] // (other._cols[1]),
            )

    def __radd__(self, other):
        # Component-wise rev scalar +
        return mat2x4(
            other + (self._cols[0]),
            other + (self._cols[1]),
        )

    def __rsub__(self, other):
        # Component-wise rev scalar -
        return mat2x4(
            other - (self._cols[0]),
            other - (self._cols[1]),
        )

    def __rmul__(self, other):
        # Component-wise rev scalar *
        return mat2x4(
            other * (self._cols[0]),
            other * (self._cols[1]),
        )

    def __rdiv__(self, other):
        # Component-wise rev scalar /
        return mat2x4(
            other / (self._cols[0]),
            other / (self._cols[1]),
        )

    def __rtruediv__(self, other):
        # Component-wise rev scalar .__truediv__
        return mat2x4(
            other .__truediv__ (self._cols[0]),
            other .__truediv__ (self._cols[1]),
        )

    def __rfloordiv__(self, other):
        # Component-wise rev scalar //
        return mat2x4(
            other // (self._cols[0]),
            other // (self._cols[1]),
        )

    def __neg__(self):
        # Component-wise rev scalar -
        return mat2x4(
            - (self._cols[0]),
            - (self._cols[1]),
        )
        pass

    def __pos__(self):
        # Component-wise rev scalar +
        return mat2x4(
            + (self._cols[0]),
            + (self._cols[1]),
        )
        pass

    def __eq__(self, other):
        return type(other) is type(self) and self._cols == other._cols

    def __ne__(self, other):
        return type(other) is not type(self) or self._cols != other._cols

    def _transpose(self):
        cols = self._cols
        return mat4x2(
                   cols[0][0],
                   cols[1][0],
                   cols[0][1],
                   cols[1][1],
                   cols[0][2],
                   cols[1][2],
                   cols[0][3],
                   cols[1][3],
        )


class mat3x4(object):
    _matrix_cols = 3
    _matrix_rows = 4

    __slots__ = '_cols'

    def __init__(self, *args):
        if not args:
            self._init_diagonal(1.0)
        elif len(args) == 1:
            arg = args[0]
            if hasattr(arg, '_matrix_cols'):
                # Initialise from another matrix
                self._init_diagonal(1.0)
                for col in range(min(3, arg._matrix_cols)):
                    arg_col = arg._cols[col]
                    self_col = self._cols[col]
                    for row in range(min(4, arg._matrix_rows)):
                        self_col[row] = arg_col[row]
            else:
                self._init_diagonal(float(arg))
        else:
            components = list(_unwrap_matrix_args(args))
            self._cols = [
                vec4(*components[0:4]),
                vec4(*components[4:8]),
                vec4(*components[8:12]),
            ]

    def _init_diagonal(self, scalar):
        # Identity constructor
        self._cols = [
          vec4(
                    scalar,
                    0.0,
                    0.0,
                    0.0,
          ),
          vec4(
                    0.0,
                    scalar,
                    0.0,
                    0.0,
          ),
          vec4(
                    0.0,
                    0.0,
                    scalar,
                    0.0,
          ),
        ]

    def __repr__(self):
        return 'mat3x4%r' % (tuple(self._cols),)

    def pformat(self, indent=0):
        return '\n'.join([
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][0] +
                '%6.2f ' % self._cols[1][0] +
                '%6.2f ' % self._cols[2][0] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][1] +
                '%6.2f ' % self._cols[1][1] +
                '%6.2f ' % self._cols[2][1] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][2] +
                '%6.2f ' % self._cols[1][2] +
                '%6.2f ' % self._cols[2][2] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][3] +
                '%6.2f ' % self._cols[1][3] +
                '%6.2f ' % self._cols[2][3] +
            ']',
        ])

    def pprint(self, indent=0):
        print self.pformat(indent)

    def __getitem__(self, index):
        return self._cols[index]

    def __setitem__(self, index, value):
        self._cols[index] = value

    def __add__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar +
            return mat3x4(
                self._cols[0] + (other),
                self._cols[1] + (other),
                self._cols[2] + (other),
            )
        else:
            # Component-wise matrix +
            return mat3x4(
                self._cols[0] + (other._cols[0]),
                self._cols[1] + (other._cols[1]),
                self._cols[2] + (other._cols[2]),
            )

    def __sub__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar -
            return mat3x4(
                self._cols[0] - (other),
                self._cols[1] - (other),
                self._cols[2] - (other),
            )
        else:
            # Component-wise matrix -
            return mat3x4(
                self._cols[0] - (other._cols[0]),
                self._cols[1] - (other._cols[1]),
                self._cols[2] - (other._cols[2]),
            )

    def __mul__(self, other):
        if hasattr(other, '_vector_components'):
            # matrix * column vector
            assert other._vector_components == 3
            return vec4(
                  self._cols[0][0] * other.x
                + self._cols[1][0] * other.y
                + self._cols[2][0] * other.z
                ,
                  self._cols[0][1] * other.x
                + self._cols[1][1] * other.y
                + self._cols[2][1] * other.z
                ,
                  self._cols[0][2] * other.x
                + self._cols[1][2] * other.y
                + self._cols[2][2] * other.z
                ,
                  self._cols[0][3] * other.x
                + self._cols[1][3] * other.y
                + self._cols[2][3] * other.z
                ,
            )
        elif hasattr(other, '_matrix_rows'):
            # matrix * matrix
            assert other._matrix_rows == 3
            a = self._cols
            b = other._cols
            if other._matrix_cols == 2:
                return mat2x4(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                    + a[2][2] * b[0][2]
                ,
                      a[0][3] * b[0][0]
                    + a[1][3] * b[0][1]
                    + a[2][3] * b[0][2]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                    + a[2][2] * b[1][2]
                ,
                      a[0][3] * b[1][0]
                    + a[1][3] * b[1][1]
                    + a[2][3] * b[1][2]
                ,
                )
            elif other._matrix_cols == 3:
                return mat3x4(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                    + a[2][2] * b[0][2]
                ,
                      a[0][3] * b[0][0]
                    + a[1][3] * b[0][1]
                    + a[2][3] * b[0][2]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                    + a[2][2] * b[1][2]
                ,
                      a[0][3] * b[1][0]
                    + a[1][3] * b[1][1]
                    + a[2][3] * b[1][2]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                    + a[2][0] * b[2][2]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                    + a[2][1] * b[2][2]
                ,
                      a[0][2] * b[2][0]
                    + a[1][2] * b[2][1]
                    + a[2][2] * b[2][2]
                ,
                      a[0][3] * b[2][0]
                    + a[1][3] * b[2][1]
                    + a[2][3] * b[2][2]
                ,
                )
            elif other._matrix_cols == 4:
                return mat4x4(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                    + a[2][2] * b[0][2]
                ,
                      a[0][3] * b[0][0]
                    + a[1][3] * b[0][1]
                    + a[2][3] * b[0][2]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                    + a[2][2] * b[1][2]
                ,
                      a[0][3] * b[1][0]
                    + a[1][3] * b[1][1]
                    + a[2][3] * b[1][2]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                    + a[2][0] * b[2][2]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                    + a[2][1] * b[2][2]
                ,
                      a[0][2] * b[2][0]
                    + a[1][2] * b[2][1]
                    + a[2][2] * b[2][2]
                ,
                      a[0][3] * b[2][0]
                    + a[1][3] * b[2][1]
                    + a[2][3] * b[2][2]
                ,
                      a[0][0] * b[3][0]
                    + a[1][0] * b[3][1]
                    + a[2][0] * b[3][2]
                ,
                      a[0][1] * b[3][0]
                    + a[1][1] * b[3][1]
                    + a[2][1] * b[3][2]
                ,
                      a[0][2] * b[3][0]
                    + a[1][2] * b[3][1]
                    + a[2][2] * b[3][2]
                ,
                      a[0][3] * b[3][0]
                    + a[1][3] * b[3][1]
                    + a[2][3] * b[3][2]
                ,
                )

        # Component-wise scalar *
        return mat3x4(
            self._cols[0] * (other),
            self._cols[1] * (other),
            self._cols[2] * (other),
        )

    def _comp_mul(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar *
            return mat3x4(
                self._cols[0] * (other),
                self._cols[1] * (other),
                self._cols[2] * (other),
            )
        else:
            # Component-wise matrix *
            return mat3x4(
                self._cols[0] * (other._cols[0]),
                self._cols[1] * (other._cols[1]),
                self._cols[2] * (other._cols[2]),
            )

    def __div__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar /
            return mat3x4(
                self._cols[0] / (other),
                self._cols[1] / (other),
                self._cols[2] / (other),
            )
        else:
            # Component-wise matrix /
            return mat3x4(
                self._cols[0] / (other._cols[0]),
                self._cols[1] / (other._cols[1]),
                self._cols[2] / (other._cols[2]),
            )

    def __truediv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar .__truediv__
            return mat3x4(
                self._cols[0] .__truediv__ (other),
                self._cols[1] .__truediv__ (other),
                self._cols[2] .__truediv__ (other),
            )
        else:
            # Component-wise matrix .__truediv__
            return mat3x4(
                self._cols[0] .__truediv__ (other._cols[0]),
                self._cols[1] .__truediv__ (other._cols[1]),
                self._cols[2] .__truediv__ (other._cols[2]),
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar //
            return mat3x4(
                self._cols[0] // (other),
                self._cols[1] // (other),
                self._cols[2] // (other),
            )
        else:
            # Component-wise matrix //
            return mat3x4(
                self._cols[0] // (other._cols[0]),
                self._cols[1] // (other._cols[1]),
                self._cols[2] // (other._cols[2]),
            )

    def __radd__(self, other):
        # Component-wise rev scalar +
        return mat3x4(
            other + (self._cols[0]),
            other + (self._cols[1]),
            other + (self._cols[2]),
        )

    def __rsub__(self, other):
        # Component-wise rev scalar -
        return mat3x4(
            other - (self._cols[0]),
            other - (self._cols[1]),
            other - (self._cols[2]),
        )

    def __rmul__(self, other):
        # Component-wise rev scalar *
        return mat3x4(
            other * (self._cols[0]),
            other * (self._cols[1]),
            other * (self._cols[2]),
        )

    def __rdiv__(self, other):
        # Component-wise rev scalar /
        return mat3x4(
            other / (self._cols[0]),
            other / (self._cols[1]),
            other / (self._cols[2]),
        )

    def __rtruediv__(self, other):
        # Component-wise rev scalar .__truediv__
        return mat3x4(
            other .__truediv__ (self._cols[0]),
            other .__truediv__ (self._cols[1]),
            other .__truediv__ (self._cols[2]),
        )

    def __rfloordiv__(self, other):
        # Component-wise rev scalar //
        return mat3x4(
            other // (self._cols[0]),
            other // (self._cols[1]),
            other // (self._cols[2]),
        )

    def __neg__(self):
        # Component-wise rev scalar -
        return mat3x4(
            - (self._cols[0]),
            - (self._cols[1]),
            - (self._cols[2]),
        )
        pass

    def __pos__(self):
        # Component-wise rev scalar +
        return mat3x4(
            + (self._cols[0]),
            + (self._cols[1]),
            + (self._cols[2]),
        )
        pass

    def __eq__(self, other):
        return type(other) is type(self) and self._cols == other._cols

    def __ne__(self, other):
        return type(other) is not type(self) or self._cols != other._cols

    def _transpose(self):
        cols = self._cols
        return mat4x3(
                   cols[0][0],
                   cols[1][0],
                   cols[2][0],
                   cols[0][1],
                   cols[1][1],
                   cols[2][1],
                   cols[0][2],
                   cols[1][2],
                   cols[2][2],
                   cols[0][3],
                   cols[1][3],
                   cols[2][3],
        )


class mat4x4(object):
    _matrix_cols = 4
    _matrix_rows = 4

    __slots__ = '_cols'

    def __init__(self, *args):
        if not args:
            self._init_diagonal(1.0)
        elif len(args) == 1:
            arg = args[0]
            if hasattr(arg, '_matrix_cols'):
                # Initialise from another matrix
                self._init_diagonal(1.0)
                for col in range(min(4, arg._matrix_cols)):
                    arg_col = arg._cols[col]
                    self_col = self._cols[col]
                    for row in range(min(4, arg._matrix_rows)):
                        self_col[row] = arg_col[row]
            else:
                self._init_diagonal(float(arg))
        else:
            components = list(_unwrap_matrix_args(args))
            self._cols = [
                vec4(*components[0:4]),
                vec4(*components[4:8]),
                vec4(*components[8:12]),
                vec4(*components[12:16]),
            ]

    def _init_diagonal(self, scalar):
        # Identity constructor
        self._cols = [
          vec4(
                    scalar,
                    0.0,
                    0.0,
                    0.0,
          ),
          vec4(
                    0.0,
                    scalar,
                    0.0,
                    0.0,
          ),
          vec4(
                    0.0,
                    0.0,
                    scalar,
                    0.0,
          ),
          vec4(
                    0.0,
                    0.0,
                    0.0,
                    scalar,
          ),
        ]

    def __repr__(self):
        return 'mat4x4%r' % (tuple(self._cols),)

    def pformat(self, indent=0):
        return '\n'.join([
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][0] +
                '%6.2f ' % self._cols[1][0] +
                '%6.2f ' % self._cols[2][0] +
                '%6.2f ' % self._cols[3][0] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][1] +
                '%6.2f ' % self._cols[1][1] +
                '%6.2f ' % self._cols[2][1] +
                '%6.2f ' % self._cols[3][1] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][2] +
                '%6.2f ' % self._cols[1][2] +
                '%6.2f ' % self._cols[2][2] +
                '%6.2f ' % self._cols[3][2] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][3] +
                '%6.2f ' % self._cols[1][3] +
                '%6.2f ' % self._cols[2][3] +
                '%6.2f ' % self._cols[3][3] +
            ']',
        ])

    def pprint(self, indent=0):
        print self.pformat(indent)

    def __getitem__(self, index):
        return self._cols[index]

    def __setitem__(self, index, value):
        self._cols[index] = value

    def __add__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar +
            return mat4x4(
                self._cols[0] + (other),
                self._cols[1] + (other),
                self._cols[2] + (other),
                self._cols[3] + (other),
            )
        else:
            # Component-wise matrix +
            return mat4x4(
                self._cols[0] + (other._cols[0]),
                self._cols[1] + (other._cols[1]),
                self._cols[2] + (other._cols[2]),
                self._cols[3] + (other._cols[3]),
            )

    def __sub__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar -
            return mat4x4(
                self._cols[0] - (other),
                self._cols[1] - (other),
                self._cols[2] - (other),
                self._cols[3] - (other),
            )
        else:
            # Component-wise matrix -
            return mat4x4(
                self._cols[0] - (other._cols[0]),
                self._cols[1] - (other._cols[1]),
                self._cols[2] - (other._cols[2]),
                self._cols[3] - (other._cols[3]),
            )

    def __mul__(self, other):
        if hasattr(other, '_vector_components'):
            # matrix * column vector
            assert other._vector_components == 4
            return vec4(
                  self._cols[0][0] * other.x
                + self._cols[1][0] * other.y
                + self._cols[2][0] * other.z
                + self._cols[3][0] * other.w
                ,
                  self._cols[0][1] * other.x
                + self._cols[1][1] * other.y
                + self._cols[2][1] * other.z
                + self._cols[3][1] * other.w
                ,
                  self._cols[0][2] * other.x
                + self._cols[1][2] * other.y
                + self._cols[2][2] * other.z
                + self._cols[3][2] * other.w
                ,
                  self._cols[0][3] * other.x
                + self._cols[1][3] * other.y
                + self._cols[2][3] * other.z
                + self._cols[3][3] * other.w
                ,
            )
        elif hasattr(other, '_matrix_rows'):
            # matrix * matrix
            assert other._matrix_rows == 4
            a = self._cols
            b = other._cols
            if other._matrix_cols == 2:
                return mat2x4(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                    + a[3][0] * b[0][3]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                    + a[3][1] * b[0][3]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                    + a[2][2] * b[0][2]
                    + a[3][2] * b[0][3]
                ,
                      a[0][3] * b[0][0]
                    + a[1][3] * b[0][1]
                    + a[2][3] * b[0][2]
                    + a[3][3] * b[0][3]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                    + a[3][0] * b[1][3]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                    + a[3][1] * b[1][3]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                    + a[2][2] * b[1][2]
                    + a[3][2] * b[1][3]
                ,
                      a[0][3] * b[1][0]
                    + a[1][3] * b[1][1]
                    + a[2][3] * b[1][2]
                    + a[3][3] * b[1][3]
                ,
                )
            elif other._matrix_cols == 3:
                return mat3x4(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                    + a[3][0] * b[0][3]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                    + a[3][1] * b[0][3]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                    + a[2][2] * b[0][2]
                    + a[3][2] * b[0][3]
                ,
                      a[0][3] * b[0][0]
                    + a[1][3] * b[0][1]
                    + a[2][3] * b[0][2]
                    + a[3][3] * b[0][3]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                    + a[3][0] * b[1][3]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                    + a[3][1] * b[1][3]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                    + a[2][2] * b[1][2]
                    + a[3][2] * b[1][3]
                ,
                      a[0][3] * b[1][0]
                    + a[1][3] * b[1][1]
                    + a[2][3] * b[1][2]
                    + a[3][3] * b[1][3]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                    + a[2][0] * b[2][2]
                    + a[3][0] * b[2][3]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                    + a[2][1] * b[2][2]
                    + a[3][1] * b[2][3]
                ,
                      a[0][2] * b[2][0]
                    + a[1][2] * b[2][1]
                    + a[2][2] * b[2][2]
                    + a[3][2] * b[2][3]
                ,
                      a[0][3] * b[2][0]
                    + a[1][3] * b[2][1]
                    + a[2][3] * b[2][2]
                    + a[3][3] * b[2][3]
                ,
                )
            elif other._matrix_cols == 4:
                return mat4x4(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                    + a[3][0] * b[0][3]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                    + a[3][1] * b[0][3]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                    + a[2][2] * b[0][2]
                    + a[3][2] * b[0][3]
                ,
                      a[0][3] * b[0][0]
                    + a[1][3] * b[0][1]
                    + a[2][3] * b[0][2]
                    + a[3][3] * b[0][3]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                    + a[3][0] * b[1][3]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                    + a[3][1] * b[1][3]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                    + a[2][2] * b[1][2]
                    + a[3][2] * b[1][3]
                ,
                      a[0][3] * b[1][0]
                    + a[1][3] * b[1][1]
                    + a[2][3] * b[1][2]
                    + a[3][3] * b[1][3]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                    + a[2][0] * b[2][2]
                    + a[3][0] * b[2][3]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                    + a[2][1] * b[2][2]
                    + a[3][1] * b[2][3]
                ,
                      a[0][2] * b[2][0]
                    + a[1][2] * b[2][1]
                    + a[2][2] * b[2][2]
                    + a[3][2] * b[2][3]
                ,
                      a[0][3] * b[2][0]
                    + a[1][3] * b[2][1]
                    + a[2][3] * b[2][2]
                    + a[3][3] * b[2][3]
                ,
                      a[0][0] * b[3][0]
                    + a[1][0] * b[3][1]
                    + a[2][0] * b[3][2]
                    + a[3][0] * b[3][3]
                ,
                      a[0][1] * b[3][0]
                    + a[1][1] * b[3][1]
                    + a[2][1] * b[3][2]
                    + a[3][1] * b[3][3]
                ,
                      a[0][2] * b[3][0]
                    + a[1][2] * b[3][1]
                    + a[2][2] * b[3][2]
                    + a[3][2] * b[3][3]
                ,
                      a[0][3] * b[3][0]
                    + a[1][3] * b[3][1]
                    + a[2][3] * b[3][2]
                    + a[3][3] * b[3][3]
                ,
                )

        # Component-wise scalar *
        return mat4x4(
            self._cols[0] * (other),
            self._cols[1] * (other),
            self._cols[2] * (other),
            self._cols[3] * (other),
        )

    def _comp_mul(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar *
            return mat4x4(
                self._cols[0] * (other),
                self._cols[1] * (other),
                self._cols[2] * (other),
                self._cols[3] * (other),
            )
        else:
            # Component-wise matrix *
            return mat4x4(
                self._cols[0] * (other._cols[0]),
                self._cols[1] * (other._cols[1]),
                self._cols[2] * (other._cols[2]),
                self._cols[3] * (other._cols[3]),
            )

    def __div__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar /
            return mat4x4(
                self._cols[0] / (other),
                self._cols[1] / (other),
                self._cols[2] / (other),
                self._cols[3] / (other),
            )
        else:
            # Component-wise matrix /
            return mat4x4(
                self._cols[0] / (other._cols[0]),
                self._cols[1] / (other._cols[1]),
                self._cols[2] / (other._cols[2]),
                self._cols[3] / (other._cols[3]),
            )

    def __truediv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar .__truediv__
            return mat4x4(
                self._cols[0] .__truediv__ (other),
                self._cols[1] .__truediv__ (other),
                self._cols[2] .__truediv__ (other),
                self._cols[3] .__truediv__ (other),
            )
        else:
            # Component-wise matrix .__truediv__
            return mat4x4(
                self._cols[0] .__truediv__ (other._cols[0]),
                self._cols[1] .__truediv__ (other._cols[1]),
                self._cols[2] .__truediv__ (other._cols[2]),
                self._cols[3] .__truediv__ (other._cols[3]),
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar //
            return mat4x4(
                self._cols[0] // (other),
                self._cols[1] // (other),
                self._cols[2] // (other),
                self._cols[3] // (other),
            )
        else:
            # Component-wise matrix //
            return mat4x4(
                self._cols[0] // (other._cols[0]),
                self._cols[1] // (other._cols[1]),
                self._cols[2] // (other._cols[2]),
                self._cols[3] // (other._cols[3]),
            )

    def __radd__(self, other):
        # Component-wise rev scalar +
        return mat4x4(
            other + (self._cols[0]),
            other + (self._cols[1]),
            other + (self._cols[2]),
            other + (self._cols[3]),
        )

    def __rsub__(self, other):
        # Component-wise rev scalar -
        return mat4x4(
            other - (self._cols[0]),
            other - (self._cols[1]),
            other - (self._cols[2]),
            other - (self._cols[3]),
        )

    def __rmul__(self, other):
        # Component-wise rev scalar *
        return mat4x4(
            other * (self._cols[0]),
            other * (self._cols[1]),
            other * (self._cols[2]),
            other * (self._cols[3]),
        )

    def __rdiv__(self, other):
        # Component-wise rev scalar /
        return mat4x4(
            other / (self._cols[0]),
            other / (self._cols[1]),
            other / (self._cols[2]),
            other / (self._cols[3]),
        )

    def __rtruediv__(self, other):
        # Component-wise rev scalar .__truediv__
        return mat4x4(
            other .__truediv__ (self._cols[0]),
            other .__truediv__ (self._cols[1]),
            other .__truediv__ (self._cols[2]),
            other .__truediv__ (self._cols[3]),
        )

    def __rfloordiv__(self, other):
        # Component-wise rev scalar //
        return mat4x4(
            other // (self._cols[0]),
            other // (self._cols[1]),
            other // (self._cols[2]),
            other // (self._cols[3]),
        )

    def __neg__(self):
        # Component-wise rev scalar -
        return mat4x4(
            - (self._cols[0]),
            - (self._cols[1]),
            - (self._cols[2]),
            - (self._cols[3]),
        )
        pass

    def __pos__(self):
        # Component-wise rev scalar +
        return mat4x4(
            + (self._cols[0]),
            + (self._cols[1]),
            + (self._cols[2]),
            + (self._cols[3]),
        )
        pass

    def __eq__(self, other):
        return type(other) is type(self) and self._cols == other._cols

    def __ne__(self, other):
        return type(other) is not type(self) or self._cols != other._cols

    def _transpose(self):
        cols = self._cols
        return mat4x4(
                   cols[0][0],
                   cols[1][0],
                   cols[2][0],
                   cols[3][0],
                   cols[0][1],
                   cols[1][1],
                   cols[2][1],
                   cols[3][1],
                   cols[0][2],
                   cols[1][2],
                   cols[2][2],
                   cols[3][2],
                   cols[0][3],
                   cols[1][3],
                   cols[2][3],
                   cols[3][3],
        )


class mat4x3(object):
    _matrix_cols = 4
    _matrix_rows = 3

    __slots__ = '_cols'

    def __init__(self, *args):
        if not args:
            self._init_diagonal(1.0)
        elif len(args) == 1:
            arg = args[0]
            if hasattr(arg, '_matrix_cols'):
                # Initialise from another matrix
                self._init_diagonal(1.0)
                for col in range(min(4, arg._matrix_cols)):
                    arg_col = arg._cols[col]
                    self_col = self._cols[col]
                    for row in range(min(3, arg._matrix_rows)):
                        self_col[row] = arg_col[row]
            else:
                self._init_diagonal(float(arg))
        else:
            components = list(_unwrap_matrix_args(args))
            self._cols = [
                vec3(*components[0:3]),
                vec3(*components[3:6]),
                vec3(*components[6:9]),
                vec3(*components[9:12]),
            ]

    def _init_diagonal(self, scalar):
        # Identity constructor
        self._cols = [
          vec3(
                    scalar,
                    0.0,
                    0.0,
          ),
          vec3(
                    0.0,
                    scalar,
                    0.0,
          ),
          vec3(
                    0.0,
                    0.0,
                    scalar,
          ),
          vec3(
                    0.0,
                    0.0,
                    0.0,
          ),
        ]

    def __repr__(self):
        return 'mat4x3%r' % (tuple(self._cols),)

    def pformat(self, indent=0):
        return '\n'.join([
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][0] +
                '%6.2f ' % self._cols[1][0] +
                '%6.2f ' % self._cols[2][0] +
                '%6.2f ' % self._cols[3][0] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][1] +
                '%6.2f ' % self._cols[1][1] +
                '%6.2f ' % self._cols[2][1] +
                '%6.2f ' % self._cols[3][1] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][2] +
                '%6.2f ' % self._cols[1][2] +
                '%6.2f ' % self._cols[2][2] +
                '%6.2f ' % self._cols[3][2] +
            ']',
        ])

    def pprint(self, indent=0):
        print self.pformat(indent)

    def __getitem__(self, index):
        return self._cols[index]

    def __setitem__(self, index, value):
        self._cols[index] = value

    def __add__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar +
            return mat4x3(
                self._cols[0] + (other),
                self._cols[1] + (other),
                self._cols[2] + (other),
                self._cols[3] + (other),
            )
        else:
            # Component-wise matrix +
            return mat4x3(
                self._cols[0] + (other._cols[0]),
                self._cols[1] + (other._cols[1]),
                self._cols[2] + (other._cols[2]),
                self._cols[3] + (other._cols[3]),
            )

    def __sub__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar -
            return mat4x3(
                self._cols[0] - (other),
                self._cols[1] - (other),
                self._cols[2] - (other),
                self._cols[3] - (other),
            )
        else:
            # Component-wise matrix -
            return mat4x3(
                self._cols[0] - (other._cols[0]),
                self._cols[1] - (other._cols[1]),
                self._cols[2] - (other._cols[2]),
                self._cols[3] - (other._cols[3]),
            )

    def __mul__(self, other):
        if hasattr(other, '_vector_components'):
            # matrix * column vector
            assert other._vector_components == 4
            return vec3(
                  self._cols[0][0] * other.x
                + self._cols[1][0] * other.y
                + self._cols[2][0] * other.z
                + self._cols[3][0] * other.w
                ,
                  self._cols[0][1] * other.x
                + self._cols[1][1] * other.y
                + self._cols[2][1] * other.z
                + self._cols[3][1] * other.w
                ,
                  self._cols[0][2] * other.x
                + self._cols[1][2] * other.y
                + self._cols[2][2] * other.z
                + self._cols[3][2] * other.w
                ,
            )
        elif hasattr(other, '_matrix_rows'):
            # matrix * matrix
            assert other._matrix_rows == 4
            a = self._cols
            b = other._cols
            if other._matrix_cols == 2:
                return mat2x3(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                    + a[3][0] * b[0][3]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                    + a[3][1] * b[0][3]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                    + a[2][2] * b[0][2]
                    + a[3][2] * b[0][3]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                    + a[3][0] * b[1][3]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                    + a[3][1] * b[1][3]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                    + a[2][2] * b[1][2]
                    + a[3][2] * b[1][3]
                ,
                )
            elif other._matrix_cols == 3:
                return mat3x3(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                    + a[3][0] * b[0][3]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                    + a[3][1] * b[0][3]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                    + a[2][2] * b[0][2]
                    + a[3][2] * b[0][3]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                    + a[3][0] * b[1][3]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                    + a[3][1] * b[1][3]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                    + a[2][2] * b[1][2]
                    + a[3][2] * b[1][3]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                    + a[2][0] * b[2][2]
                    + a[3][0] * b[2][3]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                    + a[2][1] * b[2][2]
                    + a[3][1] * b[2][3]
                ,
                      a[0][2] * b[2][0]
                    + a[1][2] * b[2][1]
                    + a[2][2] * b[2][2]
                    + a[3][2] * b[2][3]
                ,
                )
            elif other._matrix_cols == 4:
                return mat4x3(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                    + a[3][0] * b[0][3]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                    + a[3][1] * b[0][3]
                ,
                      a[0][2] * b[0][0]
                    + a[1][2] * b[0][1]
                    + a[2][2] * b[0][2]
                    + a[3][2] * b[0][3]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                    + a[3][0] * b[1][3]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                    + a[3][1] * b[1][3]
                ,
                      a[0][2] * b[1][0]
                    + a[1][2] * b[1][1]
                    + a[2][2] * b[1][2]
                    + a[3][2] * b[1][3]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                    + a[2][0] * b[2][2]
                    + a[3][0] * b[2][3]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                    + a[2][1] * b[2][2]
                    + a[3][1] * b[2][3]
                ,
                      a[0][2] * b[2][0]
                    + a[1][2] * b[2][1]
                    + a[2][2] * b[2][2]
                    + a[3][2] * b[2][3]
                ,
                      a[0][0] * b[3][0]
                    + a[1][0] * b[3][1]
                    + a[2][0] * b[3][2]
                    + a[3][0] * b[3][3]
                ,
                      a[0][1] * b[3][0]
                    + a[1][1] * b[3][1]
                    + a[2][1] * b[3][2]
                    + a[3][1] * b[3][3]
                ,
                      a[0][2] * b[3][0]
                    + a[1][2] * b[3][1]
                    + a[2][2] * b[3][2]
                    + a[3][2] * b[3][3]
                ,
                )

        # Component-wise scalar *
        return mat4x3(
            self._cols[0] * (other),
            self._cols[1] * (other),
            self._cols[2] * (other),
            self._cols[3] * (other),
        )

    def _comp_mul(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar *
            return mat4x3(
                self._cols[0] * (other),
                self._cols[1] * (other),
                self._cols[2] * (other),
                self._cols[3] * (other),
            )
        else:
            # Component-wise matrix *
            return mat4x3(
                self._cols[0] * (other._cols[0]),
                self._cols[1] * (other._cols[1]),
                self._cols[2] * (other._cols[2]),
                self._cols[3] * (other._cols[3]),
            )

    def __div__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar /
            return mat4x3(
                self._cols[0] / (other),
                self._cols[1] / (other),
                self._cols[2] / (other),
                self._cols[3] / (other),
            )
        else:
            # Component-wise matrix /
            return mat4x3(
                self._cols[0] / (other._cols[0]),
                self._cols[1] / (other._cols[1]),
                self._cols[2] / (other._cols[2]),
                self._cols[3] / (other._cols[3]),
            )

    def __truediv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar .__truediv__
            return mat4x3(
                self._cols[0] .__truediv__ (other),
                self._cols[1] .__truediv__ (other),
                self._cols[2] .__truediv__ (other),
                self._cols[3] .__truediv__ (other),
            )
        else:
            # Component-wise matrix .__truediv__
            return mat4x3(
                self._cols[0] .__truediv__ (other._cols[0]),
                self._cols[1] .__truediv__ (other._cols[1]),
                self._cols[2] .__truediv__ (other._cols[2]),
                self._cols[3] .__truediv__ (other._cols[3]),
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar //
            return mat4x3(
                self._cols[0] // (other),
                self._cols[1] // (other),
                self._cols[2] // (other),
                self._cols[3] // (other),
            )
        else:
            # Component-wise matrix //
            return mat4x3(
                self._cols[0] // (other._cols[0]),
                self._cols[1] // (other._cols[1]),
                self._cols[2] // (other._cols[2]),
                self._cols[3] // (other._cols[3]),
            )

    def __radd__(self, other):
        # Component-wise rev scalar +
        return mat4x3(
            other + (self._cols[0]),
            other + (self._cols[1]),
            other + (self._cols[2]),
            other + (self._cols[3]),
        )

    def __rsub__(self, other):
        # Component-wise rev scalar -
        return mat4x3(
            other - (self._cols[0]),
            other - (self._cols[1]),
            other - (self._cols[2]),
            other - (self._cols[3]),
        )

    def __rmul__(self, other):
        # Component-wise rev scalar *
        return mat4x3(
            other * (self._cols[0]),
            other * (self._cols[1]),
            other * (self._cols[2]),
            other * (self._cols[3]),
        )

    def __rdiv__(self, other):
        # Component-wise rev scalar /
        return mat4x3(
            other / (self._cols[0]),
            other / (self._cols[1]),
            other / (self._cols[2]),
            other / (self._cols[3]),
        )

    def __rtruediv__(self, other):
        # Component-wise rev scalar .__truediv__
        return mat4x3(
            other .__truediv__ (self._cols[0]),
            other .__truediv__ (self._cols[1]),
            other .__truediv__ (self._cols[2]),
            other .__truediv__ (self._cols[3]),
        )

    def __rfloordiv__(self, other):
        # Component-wise rev scalar //
        return mat4x3(
            other // (self._cols[0]),
            other // (self._cols[1]),
            other // (self._cols[2]),
            other // (self._cols[3]),
        )

    def __neg__(self):
        # Component-wise rev scalar -
        return mat4x3(
            - (self._cols[0]),
            - (self._cols[1]),
            - (self._cols[2]),
            - (self._cols[3]),
        )
        pass

    def __pos__(self):
        # Component-wise rev scalar +
        return mat4x3(
            + (self._cols[0]),
            + (self._cols[1]),
            + (self._cols[2]),
            + (self._cols[3]),
        )
        pass

    def __eq__(self, other):
        return type(other) is type(self) and self._cols == other._cols

    def __ne__(self, other):
        return type(other) is not type(self) or self._cols != other._cols

    def _transpose(self):
        cols = self._cols
        return mat3x4(
                   cols[0][0],
                   cols[1][0],
                   cols[2][0],
                   cols[3][0],
                   cols[0][1],
                   cols[1][1],
                   cols[2][1],
                   cols[3][1],
                   cols[0][2],
                   cols[1][2],
                   cols[2][2],
                   cols[3][2],
        )


class mat4x2(object):
    _matrix_cols = 4
    _matrix_rows = 2

    __slots__ = '_cols'

    def __init__(self, *args):
        if not args:
            self._init_diagonal(1.0)
        elif len(args) == 1:
            arg = args[0]
            if hasattr(arg, '_matrix_cols'):
                # Initialise from another matrix
                self._init_diagonal(1.0)
                for col in range(min(4, arg._matrix_cols)):
                    arg_col = arg._cols[col]
                    self_col = self._cols[col]
                    for row in range(min(2, arg._matrix_rows)):
                        self_col[row] = arg_col[row]
            else:
                self._init_diagonal(float(arg))
        else:
            components = list(_unwrap_matrix_args(args))
            self._cols = [
                vec2(*components[0:2]),
                vec2(*components[2:4]),
                vec2(*components[4:6]),
                vec2(*components[6:8]),
            ]

    def _init_diagonal(self, scalar):
        # Identity constructor
        self._cols = [
          vec2(
                    scalar,
                    0.0,
          ),
          vec2(
                    0.0,
                    scalar,
          ),
          vec2(
                    0.0,
                    0.0,
          ),
          vec2(
                    0.0,
                    0.0,
          ),
        ]

    def __repr__(self):
        return 'mat4x2%r' % (tuple(self._cols),)

    def pformat(self, indent=0):
        return '\n'.join([
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][0] +
                '%6.2f ' % self._cols[1][0] +
                '%6.2f ' % self._cols[2][0] +
                '%6.2f ' % self._cols[3][0] +
            ']',
            ' ' * indent +
            '[ ' +
                '%6.2f ' % self._cols[0][1] +
                '%6.2f ' % self._cols[1][1] +
                '%6.2f ' % self._cols[2][1] +
                '%6.2f ' % self._cols[3][1] +
            ']',
        ])

    def pprint(self, indent=0):
        print self.pformat(indent)

    def __getitem__(self, index):
        return self._cols[index]

    def __setitem__(self, index, value):
        self._cols[index] = value

    def __add__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar +
            return mat4x2(
                self._cols[0] + (other),
                self._cols[1] + (other),
                self._cols[2] + (other),
                self._cols[3] + (other),
            )
        else:
            # Component-wise matrix +
            return mat4x2(
                self._cols[0] + (other._cols[0]),
                self._cols[1] + (other._cols[1]),
                self._cols[2] + (other._cols[2]),
                self._cols[3] + (other._cols[3]),
            )

    def __sub__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar -
            return mat4x2(
                self._cols[0] - (other),
                self._cols[1] - (other),
                self._cols[2] - (other),
                self._cols[3] - (other),
            )
        else:
            # Component-wise matrix -
            return mat4x2(
                self._cols[0] - (other._cols[0]),
                self._cols[1] - (other._cols[1]),
                self._cols[2] - (other._cols[2]),
                self._cols[3] - (other._cols[3]),
            )

    def __mul__(self, other):
        if hasattr(other, '_vector_components'):
            # matrix * column vector
            assert other._vector_components == 4
            return vec2(
                  self._cols[0][0] * other.x
                + self._cols[1][0] * other.y
                + self._cols[2][0] * other.z
                + self._cols[3][0] * other.w
                ,
                  self._cols[0][1] * other.x
                + self._cols[1][1] * other.y
                + self._cols[2][1] * other.z
                + self._cols[3][1] * other.w
                ,
            )
        elif hasattr(other, '_matrix_rows'):
            # matrix * matrix
            assert other._matrix_rows == 4
            a = self._cols
            b = other._cols
            if other._matrix_cols == 2:
                return mat2x2(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                    + a[3][0] * b[0][3]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                    + a[3][1] * b[0][3]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                    + a[3][0] * b[1][3]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                    + a[3][1] * b[1][3]
                ,
                )
            elif other._matrix_cols == 3:
                return mat3x2(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                    + a[3][0] * b[0][3]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                    + a[3][1] * b[0][3]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                    + a[3][0] * b[1][3]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                    + a[3][1] * b[1][3]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                    + a[2][0] * b[2][2]
                    + a[3][0] * b[2][3]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                    + a[2][1] * b[2][2]
                    + a[3][1] * b[2][3]
                ,
                )
            elif other._matrix_cols == 4:
                return mat4x2(
                      a[0][0] * b[0][0]
                    + a[1][0] * b[0][1]
                    + a[2][0] * b[0][2]
                    + a[3][0] * b[0][3]
                ,
                      a[0][1] * b[0][0]
                    + a[1][1] * b[0][1]
                    + a[2][1] * b[0][2]
                    + a[3][1] * b[0][3]
                ,
                      a[0][0] * b[1][0]
                    + a[1][0] * b[1][1]
                    + a[2][0] * b[1][2]
                    + a[3][0] * b[1][3]
                ,
                      a[0][1] * b[1][0]
                    + a[1][1] * b[1][1]
                    + a[2][1] * b[1][2]
                    + a[3][1] * b[1][3]
                ,
                      a[0][0] * b[2][0]
                    + a[1][0] * b[2][1]
                    + a[2][0] * b[2][2]
                    + a[3][0] * b[2][3]
                ,
                      a[0][1] * b[2][0]
                    + a[1][1] * b[2][1]
                    + a[2][1] * b[2][2]
                    + a[3][1] * b[2][3]
                ,
                      a[0][0] * b[3][0]
                    + a[1][0] * b[3][1]
                    + a[2][0] * b[3][2]
                    + a[3][0] * b[3][3]
                ,
                      a[0][1] * b[3][0]
                    + a[1][1] * b[3][1]
                    + a[2][1] * b[3][2]
                    + a[3][1] * b[3][3]
                ,
                )

        # Component-wise scalar *
        return mat4x2(
            self._cols[0] * (other),
            self._cols[1] * (other),
            self._cols[2] * (other),
            self._cols[3] * (other),
        )

    def _comp_mul(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar *
            return mat4x2(
                self._cols[0] * (other),
                self._cols[1] * (other),
                self._cols[2] * (other),
                self._cols[3] * (other),
            )
        else:
            # Component-wise matrix *
            return mat4x2(
                self._cols[0] * (other._cols[0]),
                self._cols[1] * (other._cols[1]),
                self._cols[2] * (other._cols[2]),
                self._cols[3] * (other._cols[3]),
            )

    def __div__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar /
            return mat4x2(
                self._cols[0] / (other),
                self._cols[1] / (other),
                self._cols[2] / (other),
                self._cols[3] / (other),
            )
        else:
            # Component-wise matrix /
            return mat4x2(
                self._cols[0] / (other._cols[0]),
                self._cols[1] / (other._cols[1]),
                self._cols[2] / (other._cols[2]),
                self._cols[3] / (other._cols[3]),
            )

    def __truediv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar .__truediv__
            return mat4x2(
                self._cols[0] .__truediv__ (other),
                self._cols[1] .__truediv__ (other),
                self._cols[2] .__truediv__ (other),
                self._cols[3] .__truediv__ (other),
            )
        else:
            # Component-wise matrix .__truediv__
            return mat4x2(
                self._cols[0] .__truediv__ (other._cols[0]),
                self._cols[1] .__truediv__ (other._cols[1]),
                self._cols[2] .__truediv__ (other._cols[2]),
                self._cols[3] .__truediv__ (other._cols[3]),
            )

    def __floordiv__(self, other):
        if not hasattr(other, '_matrix_cols'):
            # Component-wise scalar //
            return mat4x2(
                self._cols[0] // (other),
                self._cols[1] // (other),
                self._cols[2] // (other),
                self._cols[3] // (other),
            )
        else:
            # Component-wise matrix //
            return mat4x2(
                self._cols[0] // (other._cols[0]),
                self._cols[1] // (other._cols[1]),
                self._cols[2] // (other._cols[2]),
                self._cols[3] // (other._cols[3]),
            )

    def __radd__(self, other):
        # Component-wise rev scalar +
        return mat4x2(
            other + (self._cols[0]),
            other + (self._cols[1]),
            other + (self._cols[2]),
            other + (self._cols[3]),
        )

    def __rsub__(self, other):
        # Component-wise rev scalar -
        return mat4x2(
            other - (self._cols[0]),
            other - (self._cols[1]),
            other - (self._cols[2]),
            other - (self._cols[3]),
        )

    def __rmul__(self, other):
        # Component-wise rev scalar *
        return mat4x2(
            other * (self._cols[0]),
            other * (self._cols[1]),
            other * (self._cols[2]),
            other * (self._cols[3]),
        )

    def __rdiv__(self, other):
        # Component-wise rev scalar /
        return mat4x2(
            other / (self._cols[0]),
            other / (self._cols[1]),
            other / (self._cols[2]),
            other / (self._cols[3]),
        )

    def __rtruediv__(self, other):
        # Component-wise rev scalar .__truediv__
        return mat4x2(
            other .__truediv__ (self._cols[0]),
            other .__truediv__ (self._cols[1]),
            other .__truediv__ (self._cols[2]),
            other .__truediv__ (self._cols[3]),
        )

    def __rfloordiv__(self, other):
        # Component-wise rev scalar //
        return mat4x2(
            other // (self._cols[0]),
            other // (self._cols[1]),
            other // (self._cols[2]),
            other // (self._cols[3]),
        )

    def __neg__(self):
        # Component-wise rev scalar -
        return mat4x2(
            - (self._cols[0]),
            - (self._cols[1]),
            - (self._cols[2]),
            - (self._cols[3]),
        )
        pass

    def __pos__(self):
        # Component-wise rev scalar +
        return mat4x2(
            + (self._cols[0]),
            + (self._cols[1]),
            + (self._cols[2]),
            + (self._cols[3]),
        )
        pass

    def __eq__(self, other):
        return type(other) is type(self) and self._cols == other._cols

    def __ne__(self, other):
        return type(other) is not type(self) or self._cols != other._cols

    def _transpose(self):
        cols = self._cols
        return mat2x4(
                   cols[0][0],
                   cols[1][0],
                   cols[2][0],
                   cols[3][0],
                   cols[0][1],
                   cols[1][1],
                   cols[2][1],
                   cols[3][1],
        )

mat4 = mat4x4

# Vector functions

def length(v):
    n = v._vector_components
    if n == 2:
        return _math.sqrt(v.x * v.x + v.y * v.y)
    elif n == 3:
        return _math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
    elif n == 4:
        return _math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z + v.w * v.w)

def distance(a, b):
    return length(a - b)

def dot(a, b):
    '''Dot product of vectors a and b'''
    assert a._vector_components == b._vector_components, 'Vectors must have equal size'
    n = a._vector_components
    if n == 2:
        return (a.x * b.x
              + a.y * b.y)
    elif n == 3:
        return (a.x * b.x
              + a.y * b.y
              + a.z * b.z)
    else:
        return (a.x * b.x
              + a.y * b.y
              + a.z * b.z
              + a.w * b.w)

def cross(a, b):
    return vec3(
        a.y * b.z - b.y * a.z,
        a.z * b.x - b.z * a.x,
        a.x * b.y - b.x * a.y)

def normalize(v):
    l = length(v)
    if l != 0:
        return v / length(v)
    else:
        return v

def faceforward(N, I, Nref):
    if dot(Nref, I) < 0:
        return N
    else:
        return -N

def reflect(I, N):
    return I - 2 * dot(N, I) * N

def refract(I, N, eta):
    d = dot(N, I)
    k = 1.0 - eta * eta * (1.0 - d * d)
    if k < 0.0:
        return I.__class__()
    else:
        return eta * I - (eta * d + _math.sqrt(k)) * N

# Matrix functions
def matrixCompMult(a, b):
    return a._comp_mul(b)

def outerProduct(c, r):
    return c._outer_product(r)

def transpose(m):
    return m._transpose()