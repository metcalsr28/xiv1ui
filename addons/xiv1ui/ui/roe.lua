--[[
* xiv1ui - Records of Eminence and the currencies the game shows with them (Sparks, Deeds, Unity Accolades),
* tracked from the server's packets (layouts as documented in Windower's packets/fields.lua):
*   0x110 Sparks update: the Sparks total (int32 at 0x04); sent when the Quests menu opens
*   0x113 currency info: Sparks of Eminence (int32 at 0x74), Unity Accolades (0xE4), Deeds (0xF8)
*   0x111 current records: 30 entries of 4 bytes from 0x04, and the limited-time challenge's at 0x100 (12-bit record
*         id, 20-bit progress); id 0 = empty
*   0x112 completed records: a 1024-bit field (128 bytes from 0x04) for part <u32 at 0x84> (0-3) of the 4096 ids;
*         sent at login
--]]

local roe = { sparks = nil, accolades = nil, deeds = nil, current = nil };

-- The last figures are kept per character (store.data.roe), so a reload of xiv1ui doesn't blank them until the
-- server next sends them.
local function me()
    local ok, n = pcall(function () return AshitaCore:GetMemoryManager():GetParty():GetMemberName(0); end);
    return ok and n ~= nil and n ~= '' and n or nil;
end
local function save()
    local name = me();
    if name == nil then return; end
    local store = require('core.store');
    store.data.roe = store.data.roe or {};
    store.data.roe[name] = { sparks = roe.sparks, accolades = roe.accolades, deeds = roe.deeds, current = roe.current,
                             records = roe.records, done = roe.done };
    store.save();
end
--- Fill in what hasn't arrived this session from the saved figures (once a character is known).
function roe.restore()
    if roe.restored then return; end
    local name = me();
    if name == nil then return; end
    roe.restored = true;
    local saved = (require('core.store').data.roe or {})[name];
    if saved == nil then return; end
    for _, k in ipairs({ 'sparks', 'accolades', 'deeds', 'current', 'records', 'done' }) do
        if roe[k] == nil then roe[k] = saved[k]; end
    end
end

local function i32(d, off)
    if #d < off + 4 then return nil; end
    local v = d:byte(off + 1) + d:byte(off + 2) * 256 + d:byte(off + 3) * 65536 + d:byte(off + 4) * 16777216;
    if v >= 2147483648 then v = v - 4294967296; end
    return v;
end

function roe.packet(e)
    local d = e.data;
    if d == nil then return; end
    if e.id == 0x110 then
        roe.sparks = i32(d, 0x04);
        save();
    elseif e.id == 0x113 then
        roe.sparks, roe.accolades, roe.deeds = i32(d, 0x74), i32(d, 0xE4), i32(d, 0xF8);
        save();
    elseif e.id == 0x112 then
        -- (kept as hex text, part -> 256 hex digits, so it saves with the settings)
        local part = i32(d, 0x84);
        if part and part >= 0 and part <= 3 and #d >= 0x84 then
            roe.done = roe.done or {};
            roe.done[part + 1] = (d:sub(5, 0x84):gsub('.', function (c) return string.format('%02x', c:byte()); end));
            save();
        end
    elseif e.id == 0x111 then
        local n, list = 0, {};
        for k = 0, 30 do
            local v = i32(d, k < 30 and 0x04 + k * 4 or 0x100);
            if v and bit.band(v, 0xFFF) ~= 0 then
                n = n + 1;
                list[#list + 1] = { id = bit.band(v, 0xFFF), progress = bit.rshift(bit.band(v, 0xFFFFFFFF), 12) };
            end
        end
        roe.current, roe.records = n, list;
        save();
    end
end

--- Has the record been completed? nil while unknown (no 0x112 since the character was first seen).
function roe.completed(id)
    roe.restore();
    local part = roe.done and roe.done[math.floor(id / 1024) + 1];
    if part == nil then return nil; end
    local b = id % 1024;
    local byte = tonumber(part:sub(math.floor(b / 8) * 2 + 1, math.floor(b / 8) * 2 + 2), 16) or 0;
    return bit.band(byte, bit.lshift(1, b % 8)) ~= 0;
end

--- One line for menus: what's known so far ('…' for values not received yet).
function roe.summary()
    roe.restore();
    local function v(x) return x and tostring(x) or '…'; end
    return string.format('Records: %s / 30     Sparks: %s     Deeds: %s     Unity Accolades: %s',
        v(roe.current), v(roe.sparks), v(roe.deeds), v(roe.accolades));
end

return roe;
