from collections import defaultdict
import json
import re
from lupa.lua51 import LuaRuntime
def plain(value):
    if hasattr(value, 'items'):
        return {k: plain(v) for k, v in value.items()}
    return value

def record_config(text, override=None):
    vm = LuaRuntime(unpack_returned_tuples=True, register_eval=False, register_builtins=False)
    g = vm.globals()
    for name in ['python', 'os', 'io', 'package', 'require', 'dofile', 'loadfile', 'debug']:
        g[name] = None
    vm.execute('setmetatable(_G,{__index=function(t,k) return function(...) end end})')
    config, calls = vm.table(), []
    for name in set(re.findall(r'^\s*([A-Za-z_]\w*)\s*\(', text, re.M)):
        def capture(*args, name=name):
            # First argument is the shared config table, not a new object per call.
            calls.append((name, [plain(v) for v in args[1:]]))
        g[name] = capture
    g.StartShipConfig = lambda: config
    g.NewWeaponType = config
    g.getShipNum = lambda obj, key, default: (override or {}).get(key, default)
    g.getShipStr = lambda obj, key, default: (override or {}).get(key, default)
    vm.execute(text)
    return plain(config), calls
def call_spans(text):
    """Top-level engine calls; multiline tables/quoted parentheses are retained."""
    result = []
    for match in re.finditer(r'^\s*([A-Za-z_]\w*)\(', text, re.M):
        start = match.start()
        while text[start].isspace():
            start += 1
        pos = text.index('(', start)
        depth, quote, escaped = 0, None, False
        for end in range(pos, len(text)):
            char = text[end]
            if quote:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == quote:
                    quote = None
            elif char in ('"', "'"):
                quote = char
            elif char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    end += 1
                    if end < len(text) and text[end] == ';':
                        end += 1
                    result.append((match[1], start, end, text[start:end]))
                    break
        else:
            raise ValueError('Unclosed engine call: ' + match[1])
    return result

def key(name, args):
    if name in ('addAbility', 'StartShipHardPointConfig'):
        return name + ':' + str(args[0])
    if name == 'StartShipWeaponConfig':
        return name + ':' + str(args[1])
    if name == 'AddShipMultiplier':
        return name + ':' + repr(args[:3])
    # Supply/concurrency and callback groups are replaced as complete groups
    # when the project deliberately changed them, including removed entries.
    return name

def groups(text):
    config, records = record_config(text)
    spans = call_spans(text)
    assert [n for n, _ in records] == [n for n, *_ in spans], ('Call recorder/parser disagree', [n for n, _ in records], [n for n, *_ in spans])
    result = defaultdict(list)
    for (name, args), (_, start, end, raw) in zip(records, spans):
        result[key(name, args)].append({'name': name, 'args': args, 'start': start, 'end': end, 'raw': raw})
    return config, result

def values(group):
    return [(row['name'], row['args']) for row in group]

def lua_literal(value):
    if isinstance(value, dict):
        return '{' + ','.join('[' + lua_literal(k) + ']=' + lua_literal(v) for k, v in sorted(value.items(), key=lambda row: (str(type(row[0])), str(row[0])))) + '}'
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if value is None:
        return 'nil'
    return repr(value)

def family_tables(path):
    from lupa.lua51 import LuaRuntime
    vm = LuaRuntime(register_eval=False, register_builtins=False)
    vm.execute('getn=nil; table=nil; string=nil; math=nil')
    text = path.read_text(encoding='utf-8-sig')
    vm.execute(text)
    return {name: plain(vm.globals()[name]) for name in re.findall(r'^(\w+)\s*=', text, re.M)}
