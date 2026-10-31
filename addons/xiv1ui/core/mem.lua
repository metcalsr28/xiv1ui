--[[
* xiv1ui - checked memory access for the few native UI tweaks xiv1ui makes (hiding the game's own target box and
* macro palettes). Every read and write is preceded by a VirtualQuery check, because a bad pointer would otherwise
* take the whole client down, which a Lua pcall cannot catch.
--]]

local ffi = require('ffi');
local bit = require('bit');

ffi.cdef[[
typedef struct {
    void* BaseAddress;
    void* AllocationBase;
    uint32_t AllocationProtect;
    size_t RegionSize;
    uint32_t State;
    uint32_t Protect;
    uint32_t Type;
} XIV1UI_MBI;
size_t __stdcall VirtualQuery(const void* address, void* buffer, size_t length);
]];

local kernel = ffi.load('kernel32');
local mbi = ffi.new('XIV1UI_MBI[1]');

local READ  = { [0x02] = true, [0x04] = true, [0x08] = true, [0x20] = true, [0x40] = true, [0x80] = true };
local WRITE = { [0x04] = true, [0x08] = true, [0x40] = true, [0x80] = true };

local mem = {};

--- True if [address, address + size) is committed memory with the needed access (and no guard page).
function mem.ok(address, size, writable)
    if type(address) ~= 'number' or address < 0x10000 or address + size > 0x100000000 then return false; end
    if kernel.VirtualQuery(ffi.cast('const void*', address), mbi, ffi.sizeof(mbi[0])) == 0 then return false; end
    local r = mbi[0];
    local base = tonumber(ffi.cast('uintptr_t', r.BaseAddress));
    if r.State ~= 0x1000 or bit.band(r.Protect, 0x100) ~= 0 or address + size > base + tonumber(r.RegionSize) then
        return false;
    end
    return (writable and WRITE or READ)[bit.band(r.Protect, 0xFF)] == true;
end

function mem.u8(a)  return mem.ok(a, 1) and ashita.memory.read_uint8(a) or nil; end
function mem.u16(a) return mem.ok(a, 2) and ashita.memory.read_uint16(a) or nil; end
function mem.u32(a) return mem.ok(a, 4) and ashita.memory.read_uint32(a) or nil; end

function mem.w8(a, v)
    if not mem.ok(a, 1, true) then return false; end
    ashita.memory.write_uint8(a, v);
    return true;
end

function mem.w16(a, v)
    if not mem.ok(a, 2, true) then return false; end
    ashita.memory.write_uint16(a, v);
    return true;
end

function mem.w32(a, v)
    if not mem.ok(a, 4, true) then return false; end
    ashita.memory.write_uint32(a, v);
    return true;
end

--- Follow a chain of pointers: mem.chain(a, 0, 8) reads [a + 0], then [that + 8]. Nil if any link is bad or null.
function mem.chain(a, ...)
    for _, off in ipairs({ ... }) do
        a = mem.u32(a + off);
        if a == nil or a == 0 then return nil; end
    end
    return a;
end

return mem;
