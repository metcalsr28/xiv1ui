--[[
* xiv1ui - names for entities the game only calls "NPC".
*
* An entity's name usually comes from its zone's NPC name list, a DAT file (id 6720 + zone; entries of 0x20 bytes:
* name[0x1C], u32 server id). Something the server spawns under an id that list doesn't name (e.g. a Treasure
* Casket on a private server) keeps the placeholder "NPC". For those, the list's neighbouring ids are asked: the
* server spawns such objects from a block of identical entries, so when the nearest named ids around it all agree
* (three Treasure Caskets), that's its name.
--]]

local bit = require('bit');

local npcnames = {};

local zone_loaded, by_id = nil, {};

local function read_at(path, off, n)
    local f = io.open(path, 'rb');
    if f == nil then return nil; end
    f:seek('set', off);
    local s = f:read(n);
    f:close();
    return s;
end

local function dat_file(fid)
    local d = require('core.paths').ffxi();
    for rom = 1, 10 do
        local sfx = rom == 1 and '' or tostring(rom);
        local dir = rom == 1 and '' or ('ROM' .. rom .. '\\');
        local v = read_at(d .. dir .. 'VTABLE' .. sfx .. '.DAT', fid, 1);
        if v and v:byte() == rom then
            local f = read_at(d .. dir .. 'FTABLE' .. sfx .. '.DAT', fid * 2, 2);
            if f == nil or #f < 2 then return nil; end
            local x = f:byte(1) + f:byte(2) * 256;
            return d .. 'ROM' .. sfx .. '\\' .. bit.rshift(x, 7) .. '\\' .. bit.band(x, 0x7F) .. '.DAT';
        end
    end
    return nil;
end

local function load(zone)
    zone_loaded, by_id = zone, {};
    if zone == nil or zone < 0 or zone > 255 then return; end
    local path = dat_file(6720 + zone);
    local f = path and io.open(path, 'rb');
    if f == nil then return; end
    local s = f:read('*a');
    f:close();
    for i = 0, math.floor(#s / 0x20) - 1 do
        local o = i * 0x20;
        local id = s:byte(o + 0x1D) + s:byte(o + 0x1E) * 256 + s:byte(o + 0x1F) * 65536 + s:byte(o + 0x20) * 16777216;
        local name = s:sub(o + 1, o + 0x1C):match('^[^%z]*');
        if name ~= '' then by_id[id] = name; end
    end
end

local guessed = {};          -- server id -> name or false

--- The name to show for an entity: its own, or for the placeholder "NPC" the name its zone's list gives it.
function npcnames.resolve(name, server_id)
    if name ~= 'NPC' or server_id == nil or server_id == 0 then return name; end
    local zone = bit.band(bit.rshift(server_id, 12), 0xFFF);
    if zone ~= zone_loaded then load(zone); guessed = {}; end
    if by_id[server_id] then return by_id[server_id]; end
    local g = guessed[server_id];
    if g == nil then
        -- the nearest named ids below and above (within a few), which must agree
        local below, above = nil, nil;
        for d = 1, 4 do
            below = below or by_id[server_id - d];
            above = above or by_id[server_id + d];
        end
        local pick = (below and above and below == above and below) or (below == nil and above) or (above == nil and below) or nil;
        g = pick or false;
        guessed[server_id] = g;
    end
    return g or name;
end

return npcnames;
