--[[
* xiv1ui - minimap and clock cluster (top right), after FFXIV 1.0 (reference §26).
* Minimap: a parchment disc that fades into the scene with no hard frame; your gold arrow in the centre with a
* translucent field-of-view wedge (warm yellow, red while engaged), party members as cyan dots, NPCs as orange-yellow
* dots, enemies in their claim colours, and an orange "N" tab on the rim. North is up.
* Where the game has a map for the area, the disc shows it (the Remapster HD map HorizonXI ships, or FFXI's own),
* centred on you and north up; the view covers the same stretch of map in every zone, so towns show closer than
* fields, as on the game's Map screen. Zones with several floors fall back to the parchment until xiv1ui knows the
* floor (core/maps.lua). Configuration » "Area map in the minimap" turns the map off.
* Clock: day and moon orbs with the Vana'diel weekday and time.
* Replaces the game's compass and clock (through HXIUIBegone).
--]]

local xi_now = require('core.now');
local draw   = require('core.draw');
local text   = require('core.text');
local layout = require('core.layout');
local world  = require('core.world');
local maps   = require('core.maps');
local store  = require('core.store');

local minimap = { replaces = { 'compass', 'clock', 'connection' } };

local RANGE = 50;          -- yalms from the centre to the disc's edge
local DISC  = 180;

local clock_obj, day_obj, moon_obj, n_obj, zone_obj;

local DAYS = { 'Firesday', 'Earthsday', 'Watersday', 'Windsday', 'Iceday', 'Lightningday', 'Lightsday', 'Darksday' };
local DAY_COLORS = { 0xFFFF7A5A, 0xFFE8C860, 0xFF6AA8FF, 0xFF8CE07A, 0xFFB8F0FF, 0xFFD8A0FF, 0xFFFFFFF0, 0xFF9A80C0 };

function minimap.init()
    clock_obj = text.new('label', { font_height = 17, font_color = 0xFFF4F0E6, font_alignment = text.align.Right });
    day_obj   = text.new('small', { font_height = 14, font_color = 0xFFE8E4D8, font_alignment = text.align.Right });
    moon_obj  = text.new('small', { font_height = 13, font_color = 0xFFC8D4F0 });
    n_obj     = text.new('slotkey', { fixed = true, font_height = 13, font_alignment = text.align.Center, font_color = 0xFFFFFFFF });
    zone_obj  = text.new('label', { font_height = 15, font_color = 0xFFF0DCA0, font_alignment = text.align.Center });
end

local function vana_time() return require('core.clock').vana(); end

local function moon_percent(day)
    -- 84-day lunar cycle; 0% (new moon) at phase 0, 100% (full) at phase 42. Offset calibrated against the game's own
    -- zone-in message ("Waning Crescent (43%)" on Vana'diel day 226618).
    local phase = (day + 80) % 84;
    local pct = phase <= 42 and phase / 42 or (84 - phase) / 42;
    return math.floor(pct * 100 + 0.5);
end

function minimap.render()
    local mm = AshitaCore:GetMemoryManager();
    local ent = mm:GetEntity();
    local me = mm:GetParty():GetMemberTargetIndex(0);
    if me == 0 then return; end

    local sw = layout.screen();
    local ox, oy = layout.offset('minimap');
    local cx, cy = sw - DISC / 2 - 22 + ox, 52 + DISC / 2 + oy;
    layout.bounds('minimap', cx - DISC / 2, cy - DISC / 2 - 44, DISC, DISC + 44);
    local scale = (DISC / 2 - 14) / RANGE;

    -- clock cluster above the map
    local wd, hh, mi, day = vana_time();
    draw.image('orb_day', cx + 90 - 240 + 22, cy - DISC / 2 - 36, { color = DAY_COLORS[wd + 1] });
    draw.image('orb_moon', cx + 90 - 218 + 22, cy - DISC / 2 - 36);
    text.draw(moon_obj, moon_percent(day) .. '%', cx + 90 - 196 + 22, cy - DISC / 2 - 22, 'baseline');
    text.draw(clock_obj, string.format('%02d:%02d', hh, mi), cx + 90, cy - DISC / 2 - 21, 'baseline');
    text.draw(day_obj, DAYS[wd + 1], cx + 90 - 52, cy - DISC / 2 - 22, 'baseline');

    -- map body
    draw.image('minimap_disc', cx - DISC / 2, cy - DISC / 2);
    local px, py = ent:GetLocalPositionX(me), ent:GetLocalPositionY(me);
    local zone_id = mm:GetParty():GetMemberZone(0);
    local m = store.data.minimap_hd ~= false and maps.single(zone_id) or nil;
    local tex = m and maps.texture(m);
    local range = RANGE;
    if tex then
        -- R_TEX map pixels (of the 512-pixel map) from the centre to the edge, in every zone
        local R_MAP, r = 56, DISC / 2 - 8;
        local k = tex.w / 512;                       -- texture pixels per map pixel
        local z = r / (R_MAP * k);                   -- HUD units per texture pixel
        scale = z * k * m.s;                         -- HUD units per yalm
        range = r / scale;
        local mx, my = maps.to_map(m, px, py);
        local tx, ty = mx * k, my * k;
        -- the disc as horizontal strips, each cut to the circle and to the texture
        local STEP = 2;
        for sy = -r, r - STEP, STEP do
            local yc = sy + STEP / 2;
            local hw = math.sqrt(math.max(0, r * r - yc * yc));
            local x0, x1 = -hw, hw;
            local srcx0, srcx1 = tx + x0 / z, tx + x1 / z;
            if srcx0 < 0 then x0 = x0 - srcx0 * z; srcx0 = 0; end
            if srcx1 > tex.w then x1 = x1 - (srcx1 - tex.w) * z; srcx1 = tex.w; end
            local srcy = ty + sy / z;
            if x1 > x0 and srcy >= 0 and srcy + STEP / z <= tex.h then
                -- a little taller than the step, so rounding at the UI scale never leaves a seam between strips
                draw.entry_rect(tex, srcx0, srcy, srcx1 - srcx0, (STEP + 0.75) / z, cx + x0, cy + sy, x1 - x0,
                                STEP + 0.75, 0xFFFFFFFF, tex.flipped);
            end
        end
        draw.image('minimap_rim', cx - DISC / 2, cy - DISC / 2);
    end
    minimap.range = range;
    local heading = ent:GetHeading(me) or 0;
    -- FFXI heading: 0 = east, clockwise (north = -pi/2, +Y is north); D3DX rotates counter-clockwise; sprite points up
    local rot = -(heading + math.pi / 2);
    local _, engaged = nil, ent:GetStatus(me) == 1;
    draw.image(engaged and 'fov_active' or 'fov_passive', cx - DISC / 2, cy - DISC / 2, { rot = rot });

    -- Entity scan is the expensive part (2,300 slots), so refresh the dot list 5 times a second.
    local now = xi_now();
    if now - (minimap.scan_t or 0) > 0.2 then
        minimap.scan_t = now;
        local dots = {};
        local party = world.party_ids();
        for i = 1, 2303 do
            if i ~= me then
                local flags = ent:GetRenderFlags0(i) or 0;
                if bit.band(flags, 0x200) ~= 0 and bit.band(flags, 0x4000) == 0 then
                    local ex, ey = ent:GetLocalPositionX(i), ent:GetLocalPositionY(i);
                    local rg = minimap.range or RANGE;
                    if math.abs(ex - px) < rg and math.abs(ey - py) < rg then
                        local kind = world.kind(i);
                        local col;
                        if party[ent:GetServerId(i)] then col = 0xFF6CE0F0;
                        elseif kind == 'npc' then col = 0xFFF0B040;
                        elseif kind == 'mob' then col = world.name_color(i);
                        else col = 0xFFF4F0E6; end
                        if kind ~= 'npc' or (ent:GetName(i) or '') ~= '' then dots[#dots + 1] = { ex, ey, col }; end
                    end
                end
            end
        end
        minimap.dots = dots;
    end
    for _, d in ipairs(minimap.dots or {}) do
        local dx, dy = (d[1] - px) * scale, (d[2] - py) * scale;
        if dx * dx + dy * dy < (DISC / 2 - 12) ^ 2 then
            draw.image('map_dot', cx + dx - 4, cy - dy - 4, { color = d[3] });
        end
    end
    draw.image('map_arrow', cx - 8, cy - 9, { rot = rot });

    -- "N" tab on the rim
    draw.image('map_ntab', cx - 9, cy - DISC / 2 + 2);
    text.draw(n_obj, 'N', cx, cy - DISC / 2 + 15, 'baseline');

    -- zone name under the map
    local zone = AshitaCore:GetResourceManager():GetString('zones.names', zone_id) or '';
    text.draw(zone_obj, zone, cx, cy + DISC / 2 - 4, 'baseline');
end

return minimap;
