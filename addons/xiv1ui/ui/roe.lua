--[[
* xiv1ui - Records of Eminence and the currencies the game shows with them (Sparks, Deeds, Unity Accolades),
* tracked from the server's packets (layouts as documented in Windower's packets/fields.lua):
*   0x113 currency info: Sparks of Eminence (int32 at 0x74), Unity Accolades (0xE4), Deeds (0xF8)
*   0x111 current records: 30 entries of 4 bytes from 0x04 (12-bit record id, 20-bit progress); id 0 = empty
--]]

local roe = { sparks = nil, accolades = nil, deeds = nil, current = nil };

local function i32(d, off)
    if #d < off + 4 then return nil; end
    local v = d:byte(off + 1) + d:byte(off + 2) * 256 + d:byte(off + 3) * 65536 + d:byte(off + 4) * 16777216;
    if v >= 2147483648 then v = v - 4294967296; end
    return v;
end

function roe.packet(e)
    local d = e.data;
    if d == nil then return; end
    if e.id == 0x113 then
        roe.sparks, roe.accolades, roe.deeds = i32(d, 0x74), i32(d, 0xE4), i32(d, 0xF8);
    elseif e.id == 0x111 then
        local n = 0;
        for k = 0, 29 do
            local v = i32(d, 0x04 + k * 4);
            if v and bit.band(v, 0xFFF) ~= 0 then n = n + 1; end
        end
        roe.current = n;
    end
end

--- One line for menus: what's known so far ('…' for values not received yet).
function roe.summary()
    local function v(x) return x and tostring(x) or '…'; end
    return string.format('Records: %s / 30     Sparks: %s     Deeds: %s     Unity Accolades: %s',
        v(roe.current), v(roe.sparks), v(roe.deeds), v(roe.accolades));
end

return roe;
