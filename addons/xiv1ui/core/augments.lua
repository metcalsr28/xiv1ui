--[[
* xiv1ui - an item's augments as the game words them ("HP+5 Accuracy+10", "DMG:+4" ...).
*
* The game's own parser turns an item's extra data into (string index, value) pairs: FFXiMain.dll, signature
* 8B54240481EC????????B95A00000033 (the same function and call as Ashita's libs/ffxi/itemdata.lua, GPL). Its input
* is the first 12 bytes of the extra data plus the item id, base damage / delay (weapons) and shield size; it fills
* up to 50 pairs and returns how many. Index 0 is a line break; the others are format strings in Ashita's
* "augments" string table ("HP%+d ", "{FIR}%+d " with an element's mark, "Vs. beasts: " carrying on into the next).
--]]

local ffi = require('ffi');

local augments = {};

pcall(ffi.cdef, [[
    typedef struct { uint8_t data[12]; uint16_t itemno; uint16_t damage; uint16_t attack_delay; uint16_t shield_size; } xiv1ui_augdata_t;
    typedef struct { int32_t index; int32_t value; } xiv1ui_aug_t;
    typedef struct { xiv1ui_aug_t augments[50]; } xiv1ui_augs_t;
    typedef uint32_t (__cdecl* xiv1ui_augparse_f)(xiv1ui_augdata_t*, xiv1ui_augs_t*);
]]);

local parse = nil;           -- the game's function (false if not found)
local cache = {};            -- item id .. extra data -> text ('' for none)
local cached = 0;

local ELEMENTS = { FIR = 'Fire', ICE = 'Ice', WND = 'Wind', ERT = 'Earth', LTG = 'Lightning', WTR = 'Water',
                   LIT = 'Light', DKN = 'Dark' };

local function word(fmt, value)
    local ok, s = pcall(string.format, fmt, value);
    if not ok then s = fmt; end
    return (s:gsub('{(%u%u%u)}', function (e) return ELEMENTS[e] and (ELEMENTS[e] .. ' ') or ''; end));
end

--- The augments of a container item (IItem from GetContainerItem) as text, one line per group, or nil.
function augments.text(item, res)
    if item == nil or res == nil or item.Id == 0 then return nil; end
    local extra = item.Extra;
    if type(extra) ~= 'string' or #extra < 12 or extra:sub(1, 12) == string.rep('\0', 12) then return nil; end
    local key = item.Id .. extra:sub(1, 12);
    local t = cache[key];
    if t ~= nil then return t ~= '' and t or nil; end
    if parse == nil then
        local p = ashita.memory.find('FFXiMain.dll', 0, '8B54240481EC????????B95A00000033', 0, 0);
        parse = (p and p ~= 0) and ffi.cast('xiv1ui_augparse_f', p) or false;
    end
    if not parse then return nil; end
    local d, a = ffi.new('xiv1ui_augdata_t'), ffi.new('xiv1ui_augs_t');
    ffi.copy(d.data, extra, 12);
    d.itemno = item.Id;
    d.damage = res.Type == 4 and (res.Damage or 0) or 0;
    d.attack_delay = res.Type == 4 and (res.Delay or 0) or 0;
    d.shield_size = res.Type == 5 and (res.ShieldSize or 0) or 0;
    local ok, n = pcall(parse, d, a);
    local rm = AshitaCore:GetResourceManager();
    local out = {};
    if ok and n then
        for i = 0, math.min(tonumber(n), 50) - 1 do
            local idx, v = a.augments[i].index, a.augments[i].value;
            if idx == 0 then
                out[#out + 1] = '\n';
            else
                out[#out + 1] = word(rm:GetString('augments', idx) or '', v);
            end
        end
    end
    t = table.concat(out):gsub('[\r ]*\n[\r\n ]*', '\n'):gsub(' +', ' '):gsub('^%s+', ''):gsub('%s+$', '');
    if cached > 500 then cache, cached = {}, 0; end
    cache[key], cached = t, cached + 1;
    return t ~= '' and t or nil;
end

return augments;
