"""Read extracted HW2 Classic Lua 4 data without loading the game or Lua VM.

Supports only straight-line table construction, numeric expressions and passive
API call records. Unknown opcodes, control flow and executable closures fail.
Format references: https://www.lua.org/source/4.0/lundump.c.html and lopcodes.h.html.
"""

from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path

OPS = """END RETURN CALL TAILCALL PUSHNIL POP PUSHINT PUSHSTRING PUSHNUM
PUSHNEGNUM PUSHUPVALUE GETLOCAL GETGLOBAL GETTABLE GETDOTTED GETINDEXED
PUSHSELF CREATETABLE SETLOCAL SETGLOBAL SETTABLE SETLIST SETMAP ADD ADDI SUB
MULT DIV POW CONCAT MINUS NOT JMPNE JMPEQ JMPLT JMPLE JMPGT JMPGE JMPT JMPF
JMPONT JMPONF JMP PUSHNILJMP FORPREP FORLOOP LFORPREP LFORLOOP CLOSURE""".split()


class Chunk:
    def __init__(self, path: Path):
        self.data = path.read_bytes()
        # Supported original 32-bit little-endian Lua 4 bytecode, double numbers.
        assert self.data[:13] == bytes.fromhex("1b4c7561400104040420060908"), path
        self.pos = 21
        self.proto = self.function()
        assert self.pos == len(self.data), (path, self.pos, len(self.data))

    def integer(self):
        n = struct.unpack_from("<I", self.data, self.pos)[0]
        self.pos += 4
        return n

    def string(self):
        size = self.integer()
        value = self.data[self.pos : self.pos + size - 1].decode("cp1252") if size else None
        if size:
            assert self.data[self.pos + size - 1] == 0
        self.pos += size
        return value

    def function(self):
        source = self.string()
        self.integer()  # definition line
        params = self.integer()
        vararg = self.data[self.pos]
        self.pos += 1
        self.integer()  # maximum stack
        for _ in range(self.integer()):
            self.string()
            self.integer()
            self.integer()
        line_count = self.integer()
        self.pos += line_count * 4  # debug line map
        strings = [self.string() for _ in range(self.integer())]
        numbers = []
        for _ in range(self.integer()):
            numbers.append(struct.unpack_from("<d", self.data, self.pos)[0])
            self.pos += 8
        children = [self.function() for _ in range(self.integer())]
        count = self.integer()
        code = struct.unpack_from("<" + "I" * count, self.data, self.pos)
        self.pos += count * 4
        assert code and code[-1] == 0
        return dict(
            source=source,
            strings=strings,
            numbers=numbers,
            code=code,
            children=children,
            params=params,
            vararg=vararg,
        )


@dataclass(frozen=True)
class GlobalName:
    name: str


def tables(path: Path):
    chunk = Chunk(path)
    p = chunk.proto
    assert not p["params"] and not p["vararg"] and not p["children"], path
    stack, globals_, calls = [], {}, []
    for pc, word in enumerate(p["code"]):
        op = OPS[word & 63]
        u = word >> 6
        signed = u - ((1 << 25) - 1)
        aa, bb = word >> 15, (word >> 6) & 511
        if op == "END":
            assert not stack, (path, "nonempty final stack", stack)
            break
        if op == "PUSHINT":
            stack.append(signed)
        elif op == "PUSHSTRING":
            stack.append(p["strings"][u])
        elif op in ("PUSHNUM", "PUSHNEGNUM"):
            stack.append(p["numbers"][u] * (-1 if op == "PUSHNEGNUM" else 1))
        elif op == "PUSHNIL":
            stack.extend([None] * u)
        elif op == "POP":
            del stack[-u:]
        elif op == "GETGLOBAL":
            key = p["strings"][u]
            stack.append(globals_.get(key, GlobalName(key)))
        elif op == "SETGLOBAL":
            globals_[p["strings"][u]] = stack.pop()
        elif op == "CREATETABLE":
            stack.append({})
        elif op == "GETDOTTED":
            stack[-1] = stack[-1][p["strings"][u]]
        elif op == "GETTABLE":
            key = stack.pop()
            stack[-1] = stack[-1][key]
        elif op == "SETTABLE":
            stack[-aa][stack[-aa + 1]] = stack[-1]
            if bb:
                del stack[-bb:]
        elif op == "SETMAP":
            items = stack[-2 * u :]
            target = stack[-2 * u - 1]
            target.update(zip(items[::2], items[1::2]))
            del stack[-2 * u :]
        elif op == "SETLIST":
            target = stack[-bb - 1]
            for number, value in enumerate(stack[-bb:], aa * 64 + 1):
                target[number] = value
            del stack[-bb:]
        elif op in ("ADD", "SUB", "MULT", "DIV", "POW"):
            right, left = stack.pop(), stack.pop()
            assert isinstance(left, (int, float)) and isinstance(right, (int, float))
            stack.append(
                {
                    "ADD": lambda: left + right,
                    "SUB": lambda: left - right,
                    "MULT": lambda: left * right,
                    "DIV": lambda: left / right,
                    "POW": lambda: left**right,
                }[op]()
            )
        elif op == "ADDI":
            stack[-1] += signed
        elif op == "MINUS":
            stack[-1] = -stack[-1]
        elif op == "CALL":
            fn, args = stack[aa], stack[aa + 1 :]
            assert isinstance(fn, GlobalName), (path, pc, fn)
            assert bb in (0, 1), (path, pc, bb)
            # Nothing dispatches to Lua, OS functions or a game API.
            calls.append(dict(name=fn.name, args=args))
            result = {} if fn.name in ("StartShipConfig", "StartSubSystemConfig") else None
            del stack[aa:]
            if bb:
                assert result is not None, (path, pc, "unsupported call result", fn)
                stack.append(result)
        else:
            raise ValueError((str(path), pc, "unsupported data opcode", op))
    return globals_, calls
