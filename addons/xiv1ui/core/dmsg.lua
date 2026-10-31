--[[
* xiv1ui - FFXI's "d_msg" text tables (quest names and descriptions, key items ...), read from the game's DATs.
*
* Layout: "d_msg" at 0; u32 entry size at 0x20, entry count at 0x28; entries from 0x40, every byte XOR 0xFF. An
* entry starts with its field count, then (offset, type) u32 pairs: type 1 a u32 at that offset, type 0 a text
* (0x1C bytes of header, then the text up to a 0).
--]]

local bit  = require('bit');
local maps = require('core.maps');

local dmsg = {};
local cache = {};

-- FFXI's own characters in these texts (Shift-JIS) -> plain ones; anything else non-ASCII is dropped
local SJIS = { ['\129\070'] = ':', ['\129\069'] = '-', ['\129\065'] = ',', ['\129\066'] = '.', ['\129\073'] = '!',
               ['\129\072'] = '?', ['\129\064'] = ' ' };

local function clean(s)
    s = s:gsub('[\129-\159\224-\239].', function (c) return SJIS[c] or ''; end);
    return (s:gsub('[\128-\255]', ''));
end

--- The entries of DAT file `fid`: { { ints = { ... }, texts = { ... } }, ... } (1-based), or nil.
function dmsg.read(fid)
    if cache[fid] ~= nil then return cache[fid] or nil; end
    cache[fid] = false;
    local path = maps.dat_file(fid);
    local f = path and io.open(path, 'rb');
    if not f then return nil; end
    local d = f:read('*a');
    f:close();
    if #d < 0x40 or d:sub(1, 5) ~= 'd_msg' then return nil; end
    local function raw32(at)
        local a, b, c, e = d:byte(at + 1, at + 4);
        return a + b * 256 + c * 65536 + e * 16777216;
    end
    local function u32(at) return bit.bxor(raw32(at), 0xFFFFFFFF) % 4294967296; end
    local size, count = raw32(0x20), raw32(0x28);
    if size < 8 or count < 1 or 0x40 + size * count > #d then return nil; end
    local out = {};
    for k = 0, count - 1 do
        local e = 0x40 + k * size;
        local n = u32(e);
        local ent = { ints = {}, texts = {} };
        for i = 0, math.min(n, 16) - 1 do
            local off, ty = u32(e + 4 + 8 * i), u32(e + 8 + 8 * i);
            if off < size then
                if ty == 1 then
                    ent.ints[#ent.ints + 1] = u32(e + off);
                elseif ty == 0 and off + 0x1C < size then
                    local chars = {};
                    for at = e + off + 0x1C, e + size - 1 do
                        local c = bit.bxor(d:byte(at + 1), 0xFF);
                        if c == 0 then break; end
                        chars[#chars + 1] = string.char(c);
                    end
                    ent.texts[#ent.texts + 1] = clean(table.concat(chars));
                end
            end
        end
        out[#out + 1] = ent;
    end
    cache[fid] = out;
    return out;
end

return dmsg;
