--[[
* xiv1ui - the game's own area maps, for the minimap: which map belongs to a zone, how world positions land on it,
* and its picture (from an XI-Pivot overlay when one has it, e.g. HorizonXI's Remapster or CatsEyeXI's combined HD
* maps, else FFXI's original map file).
*
* Everything comes from the game itself (see docs/MODDING-NOTES.md, "Area maps"):
*   - FFXiMain.dll holds the map table the game's Map screen uses: 14-byte entries
*       u16 zone, u8 floor key, u8 map number, u8 flags, u8 scale code, u8 region, u8 0, u16 map id, s16 ox, s16 oy
*     A world position (x east, y north) lands on the 512-pixel map at
*       px = x * s - ox,   py = -y * s - oy,   s = scale code * 0.2
*     (checked against the Map screen's grid square and its view rectangle at two positions in Bastok Markets).
*   - The map picture is DAT file  5312 + map id  (flags 0) or  53295 + map id  (flags & 16, later expansions),
*     found through the game's VTABLE / FTABLE files like any other DAT. Its image chunk is named
*     "m_<zone>_<floor key>"; the pixels are either 8-bit palettized (a BMP without the file header, bottom-up) or
*     DXT3 at offset 0x80 (0x75 in files tagged "3TXD"). XI-Pivot overlays mirror the ROM paths; config/pivot/pivot.ini names the overlay folder
*     (root_path) and the overlays in use ([overlays] 0=..., 1=...), later ones checked first.
--]]

local ffi = require('ffi');
local bit = require('bit');
local draw = require('core.draw');

local maps = {};

local entries = nil;         -- zone -> { { key, num, flags, s, ox, oy, id }, ... }

local function read_table()
    entries = {};
    -- the first entry (West Ronfaure: zone 100, key 0, map 1, flags 0, scale 1, region 1, id 1, -312, -248)
    local a = ashita.memory.find('FFXiMain.dll', 0, '6400000100010100' .. '0100C8FE08FF', 0, 0);
    if a == nil or a == 0 then return; end
    for i = 0, 1999 do
        local e = a + i * 14;
        local zone = ashita.memory.read_uint16(e);
        if zone == nil or zone > 1000 then break; end
        local list = entries[zone] or {};
        entries[zone] = list;
        list[#list + 1] = {
            key = ashita.memory.read_uint8(e + 2), num = ashita.memory.read_uint8(e + 3),
            flags = ashita.memory.read_uint8(e + 4), s = ashita.memory.read_uint8(e + 5) * 0.2,
            id = ashita.memory.read_uint16(e + 8),
            ox = ashita.memory.read_int16(e + 10), oy = ashita.memory.read_int16(e + 12),
        };
    end
end

--- The map entries of a zone (nil if the zone has no map).
function maps.of_zone(zone)
    if entries == nil then read_table(); end
    return entries[zone];
end

--- The zone's map when there is only one to choose from (all its entries share a floor key), else nil.
-- Entries flagged 0x10 belong to later expansions' copies of a zone; they're used only if there is nothing else.
function maps.single(zone)
    local list = maps.of_zone(zone);
    if list == nil then return nil; end
    local base = {};
    for _, m in ipairs(list) do if bit.band(m.flags, 0x10) == 0 then base[#base + 1] = m; end end
    if #base == 0 then base = list; end
    for _, m in ipairs(base) do if m.key ~= base[1].key then return nil; end end
    return base[1];
end

-- The floor the player stands on, in zones with several maps. The game keeps no "current floor": its Map screen
-- asks a function that casts a ray down (then up) from a position into the zone's collision mesh and returns the
-- floor key of the surface it hits (0 when it hits nothing). That function: FFXiMain.dll, signature below,
-- int __thiscall (collision object, x, height, north); the object pointer is a global read through the second
-- signature (+2). The Map screen then takes the zone's first entry with that key, else the one with key 0.
local floor_fn, floor_obj = nil, nil;
local floor_cache = { zone = nil, key = nil, t = 0 };

local function floor_key(x, z, y)
    if floor_fn == nil then
        floor_fn = false;
        local fn = ashita.memory.find('FFXiMain.dll', 0, '8B542408568D4424108BF18B4C2410508B44240C6800002041', 0, 0);
        local pp = ashita.memory.find('FFXiMain.dll', 0, '8B0D????????565057E8????????568D4C240C57', 2, 0);
        if fn and fn ~= 0 and pp and pp ~= 0 then
            floor_fn = ffi.cast('int32_t (__thiscall*)(uint32_t, float, float, float)', fn);
            floor_obj = ashita.memory.read_uint32(pp);
        end
    end
    if not floor_fn then return nil; end
    local obj = ashita.memory.read_uint32(floor_obj);
    if obj == nil or obj == 0 then return nil; end
    return floor_fn(obj, x, z, y);
end

--- The map for the player's position (x east, z height, y north) in a zone, or nil: the zone's only map, or in a
-- zone with several, the one for the floor under the player (asked a few times a second; a jump or a fall that
-- hits nothing keeps the last floor).
function maps.current(zone, x, z, y)
    local one = maps.single(zone);
    if one then return one; end
    local list = maps.of_zone(zone);
    if list == nil then return nil; end
    local fc = floor_cache;
    local now = require('core.now')();
    if fc.zone ~= zone then fc.zone, fc.key, fc.t = zone, nil, 0; end
    if now - fc.t > 0.25 then
        fc.t = now;
        local k = floor_key(x, z, y);
        if k and (k ~= 0 or fc.key == nil) then fc.key = k; end
    end
    if fc.key == nil then return nil; end
    for _, m in ipairs(list) do if m.key == fc.key then return m; end end
    for _, m in ipairs(list) do if m.key == 0 then return m; end end
    return nil;
end

--- World x, y -> pixel on the 512-pixel map.
function maps.to_map(m, x, y) return x * m.s - m.ox, -y * m.s - m.oy; end

-- DAT files ------------------------------------------------------------------------------------------------------

local game_dir = nil;
local function ffxi_dir()
    if game_dir == nil then
        local paths = require('core.paths');
        game_dir = { install = paths.install(), ffxi = paths.ffxi() };
    end
    return game_dir;
end

-- The XI-Pivot overlay folders in use, most important first (from config/pivot/pivot.ini), then FFXI's own folder.
local bases = nil;
local function dat_bases()
    if bases then return bases; end
    bases = {};
    local dirs = ffxi_dir();
    local f = io.open(dirs.install .. 'config\\pivot\\pivot.ini', 'r');
    if f then
        local root, list, section = nil, {}, '';
        for line in f:lines() do
            line = line:gsub('\r$', '');
            local sec = line:match('^%[(.-)%]');
            if sec then
                section = sec:lower();
            elseif section == 'settings' and line:match('^root_path=') then
                root = line:match('^root_path=(.*)$');
            elseif section == 'overlays' then
                local i, name = line:match('^(%d+)=(.+)$');
                if i then list[#list + 1] = { tonumber(i), name }; end
            end
        end
        f:close();
        if root and root ~= '' then
            root = root:gsub('[\\/]+$', '') .. '\\';
            table.sort(list, function (a, b) return a[1] > b[1]; end);
            for _, o in ipairs(list) do bases[#bases + 1] = root .. o[2] .. '\\'; end
        end
    end
    bases[#bases + 1] = dirs.ffxi;
    return bases;
end

local function read_at(path, off, n)
    local f = io.open(path, 'rb');
    if f == nil then return nil; end
    f:seek('set', off);
    local s = f:read(n);
    f:close();
    return s;
end

--- The ROM-relative path of a DAT file id ("ROM4/3/108.DAT"), through the VTABLE / FTABLE files.
local function dat_path(fid)
    local d = ffxi_dir().ffxi;
    for rom = 1, 10 do
        local sfx = rom == 1 and '' or tostring(rom);
        local dir = rom == 1 and '' or ('ROM' .. rom .. '\\');
        local v = read_at(d .. dir .. 'VTABLE' .. sfx .. '.DAT', fid, 1);
        if v and v:byte() == rom then
            local f = read_at(d .. dir .. 'FTABLE' .. sfx .. '.DAT', fid * 2, 2);
            if f == nil or #f < 2 then return nil; end
            local x = f:byte(1) + f:byte(2) * 256;
            return 'ROM' .. sfx .. '\\' .. bit.rshift(x, 7) .. '\\' .. bit.band(x, 0x7F) .. '.DAT';
        end
    end
    return nil;
end

local function dds_header(w, h)
    local hdr = ffi.new('uint32_t[32]');
    hdr[0] = 0x20534444;                 -- 'DDS '
    hdr[1] = 124;
    hdr[2] = bit.bor(0x1, 0x2, 0x4, 0x1000, 0x80000);
    hdr[3], hdr[4] = h, w;
    hdr[5] = w * h;                      -- DXT3: 1 byte per pixel
    hdr[19] = 32;                        -- pixel format
    hdr[20] = 0x4;                       -- FOURCC
    hdr[21] = 0x33545844;                -- 'DXT3'
    hdr[27] = 0x1000;                    -- caps: texture
    return ffi.string(hdr, 128);
end

--- The full path of a DAT file id (an XI-Pivot overlay's copy first), or nil.
function maps.dat_file(fid)
    local rel = dat_path(fid);
    if rel == nil then return nil; end
    for _, base in ipairs(dat_bases()) do
        local f = io.open(base .. rel, 'rb');
        if f then f:close(); return base .. rel; end
    end
    return nil;
end

--- Build an in-memory image file (BMP or DDS) from a map DAT's contents, or nil.
local function image_file(dat)
    if #dat < 0x80 then return nil; end
    local flag = dat:byte(0x31);
    local w = dat:byte(0x46) + dat:byte(0x47) * 256 + dat:byte(0x48) * 65536;
    local h = dat:byte(0x4A) + dat:byte(0x4B) * 256 + dat:byte(0x4C) * 65536;
    if w <= 0 or w > 4096 or h <= 0 or h > 4096 then return nil; end
    if flag == 0xB1 then
        -- 8-bit palettized: BITMAPINFOHEADER (40) + palette (1024) + pixels, i.e. a BMP minus its 14-byte file header
        local body = dat:sub(0x42, 0x42 + 40 + 1024 + w * h - 1);
        local total = 14 + #body;
        local fh = ffi.new('uint8_t[14]');
        fh[0], fh[1] = 0x42, 0x4D;
        ffi.cast('uint32_t*', fh + 2)[0] = total;
        ffi.cast('uint32_t*', fh + 10)[0] = 14 + 40 + 1024;
        return ffi.string(fh, 14) .. body;
    elseif flag == 0xA1 then
        -- DXT3. Files with the "3TXD" tag at 0x69 (FFXI's own newer maps, and HD packs made like them) have two
        -- more u32s after it and the blocks start at 0x75; the others start at 0x80.
        local tagged = dat:sub(0x6A, 0x6D) == '3TXD';
        local at = tagged and 0x75 or 0x80;
        local n = w * h;
        if #dat < at + n then return nil; end
        -- (the older layout stores the rows bottom-up like the BMPs; tagged files are top-down)
        return dds_header(w, h) .. dat:sub(at + 1, at + n), true, not tagged;
    end
    return nil;
end

--- Write a map entry's picture to a file (BMP, or DDS for DXT maps) for tools outside the game; returns the path
-- written or nil.
function maps.export(m, out_base)
    local fid = (bit.band(m.flags, 0x10) ~= 0 and 53295 or 5312) + m.id;
    local rel = dat_path(fid);
    if rel == nil then return nil; end
    local img, dxt = nil, nil;
    for _, base in ipairs(dat_bases()) do
        local f = io.open(base .. rel, 'rb');
        if f then
            local dat = f:read('*a');
            f:close();
            img, dxt = image_file(dat);
            if img then break; end
        end
    end
    if img == nil then return nil; end
    local path = out_base .. (dxt and '.dds' or '.bmp');
    local f = io.open(path, 'wb');
    if f == nil then return nil; end
    f:write(img);
    f:close();
    return path;
end

local textures = {};         -- map id .. flags -> cache entry or false

--- The texture of a map entry (cache entry { tex, w, h, flipped }) or nil. Loads once (a ~1 MB file read).
function maps.texture(m)
    local key = m.id .. ':' .. m.flags;
    local t = textures[key];
    if t ~= nil then return t or nil; end
    textures[key] = false;
    local fid = (bit.band(m.flags, 0x10) ~= 0 and 53295 or 5312) + m.id;
    local rel = dat_path(fid);
    if rel == nil then return nil; end
    local img, dxt, flipped = nil, nil, nil;
    for _, base in ipairs(dat_bases()) do
        local f = io.open(base .. rel, 'rb');
        if f then
            local dat = f:read('*a');
            f:close();
            img, dxt, flipped = image_file(dat);
            if img then break; end
        end
    end
    if img == nil then return nil; end
    local buf = ffi.new('uint8_t[?]', #img);
    ffi.copy(buf, img, #img);
    local e = draw.texture_mem('map:' .. key, buf, #img, true);
    if e then e.flipped = flipped == true; textures[key] = e; end
    return e;
end

return maps;
