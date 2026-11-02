--[[
* xiv1ui - Commands » Quests » Current Quests / Completed Quests, in place of FFXI's list (window "menu    quest01",
* used for both; which one comes from the row chosen in the Quests menu).
*
* The game keeps running its list, so Left / Right still change the area and Confirm / Esc work as before. From its
* class object: the area (+0x6C: 0 San d'Oria ... 10 Coalition), the quests listed (+0x20 -> 8-byte records, the
* quest's place in its area's file first; +0x40 of them) and the cursor (+0x30, 0-based). Quest names and their client / summary text come
* from FFXI's quest tables, one DAT per area (core/dmsg.lua).
--]]

local draw    = require('core.draw');
local text    = require('core.text');
local layout  = require('core.layout');
local ui      = require('core.ui');
local mem     = require('core.mem');
local store   = require('core.store');
local gamewin = require('core.gamewin');
local xi_now  = require('core.now');

local quests = {};

-- area index -> name and the DAT with its quests
local AREAS = {
    [0] = { "San d'Oria", 0xD99A }, { 'Bastok', 0xD99B }, { 'Windurst', 0xD99C }, { 'Jeuno', 0xD99D },
    { 'Other Areas', 0xD99E }, { 'Outlands', 0xD99F }, { 'Aht Urhgan', 0xD9A0 }, { 'Abyssea', 0xD9AA },
    { 'Crystal War', 0xD9A1 }, { 'Adoulin', 0xD9BB }, { 'Coalition', 0xD9BC },
};

-- Commands » Missions » (a storyline): window "miss00", laid out the same way, with two headings among the records
-- (id 0xFFFF "Current", 0xFFFE "Completed"); +0x6C picks the storyline (11, The Voracious Resurgence, isn't listed)
local MISSION_AREAS = {
    [0] = { "San d'Oria", 0xD9A3 }, { 'Bastok', 0xD9A4 }, { 'Windurst', 0xD9A5 }, { 'Rise of the Zilart', 0xD9A6 },
    { 'Chains of Promathia', 0xD9A7 }, { 'Assault', 0xD9A8 }, { 'Treasures of Aht Urhgan', 0xD9A9 },
    { 'Campaign', 0xD9AC }, { 'Wings of the Goddess', 0xD9AB }, { 'Seekers of Adoulin', 0xD9BA },
    { "Rhapsodies of Vana'diel", 0xD9BD }, { 'The Voracious Resurgence', 0xD9BE }, { 'A Crystalline Prophecy', 0xD9B7 },
    { "A Moogle Kupo d'Etat", 0xD9B8 }, { 'A Shantotto Ascension', 0xD9B9 },
};
local HEADINGS = { [0xFFFF] = 'Current', [0xFFFE] = 'Completed' };

-- quest (or mission) id -> { name, text } for an area; a mission's id is its record's place in the DAT
local by_area = {};
local function quest_table(area, missions)
    local key = (missions and 'm' or 'q') .. area;
    if by_area[key] ~= nil then return by_area[key] or nil; end
    by_area[key] = false;
    local a = (missions and MISSION_AREAS or AREAS)[area];
    local entries = a and require('core.dmsg').read(a[2]);
    if entries == nil then return nil; end
    local t = {};
    -- (the game's lists name a quest or mission by its record's place in the file, not by the number in the record,
    -- which is the quest's id: in Jeuno the Gobbiebag quests are places 28-37 but ids 27-30, 74, 75 ...; the number
    -- is kept too, as a fallback for the "To commence ..." mission records numbered 1000)
    for i, e in ipairs(entries) do
        -- ("__" in front of a name marks a chapter's later steps; FFXI indents them)
        local q = { name = (e.texts[1] or '?'):gsub('^_+', '  '), text = e.texts[2] or '' };
        t[i - 1] = q;
        if e.ints[1] and t[e.ints[1]] == nil then t[e.ints[1]] = q; end
    end
    by_area[key] = t;
    return t;
end

local function which()
    local cm = require('ui.cmdmenu');
    if store.data.cmd_menu == false then return nil; end
    local _, f = require('core.native').focused();
    local mode;
    if f == 'quest01' then
        mode = (cm.last_choice or {}).quest00;
        if mode ~= 'Current Quests' and mode ~= 'Completed Quests' then return nil; end
    elseif f == 'miss00' then
        mode = 'missions';
    else
        return nil;
    end
    local slot = gamewin.slot(f);
    local cls = slot and mem.u32(slot);
    if cls == nil then return nil; end
    return mode, cls, f;
end

local hider = gamewin.new({ frame_only = true });   -- (see gamewin.new)
local opened = nil;
function quests.release() hider:restore(); end

--- At each scene start, before the game draws: a list that just opened is hidden at once (render() draws ours).
function quests.early()
    -- (only when render() will draw it: the same checks)
    local mode, cls, win = which();
    local area = cls and mem.u32(cls + 0x6C);
    local n, list = cls and mem.u32(cls + 0x40), cls and mem.u32(cls + 0x20);
    if mode and area and quest_table(area, mode == 'missions') and n and list and n <= 512
       and (n == 0 or mem.ok(list, n * 8)) then
        hider:hide({ win });
    end
end

local ROW_H, SHOWN, W = 28, 10, 520;
local view_first = 0;

function quests.render()
    local mode, cls, win = which();
    local missions = (mode == 'missions');
    local area = cls and mem.u32(cls + 0x6C);
    local qt = area and quest_table(area, missions);
    local n, cur, list = cls and mem.u32(cls + 0x40), cls and mem.u32(cls + 0x30), cls and mem.u32(cls + 0x20);
    if mode == nil or qt == nil or n == nil or n > 512 or list == nil or (n > 0 and not mem.ok(list, n * 8)) then
        -- (a list backed out of stays on screen a frame or more while the game closes it: hidden until then)
        if hider:active() then hider:release_except({ 'quest01', 'miss00' }); end
        opened = nil;
        return;
    end
    hider:hide({ win });
    if opened == nil then opened, view_first = xi_now(), 0; end
    local a = math.min(1, (xi_now() - opened) / 0.15);
    local rows = {};
    for i = 0, n - 1 do
        local id = mem.u16(list + i * 8);
        -- (0xFFFC: no current missions, 0xFFFB: an empty section)
        rows[#rows + 1] = HEADINGS[id] and { name = HEADINGS[id] .. ':', heading = true }
                          or id == 0xFFFC and { name = 'No current missions.', heading = true, none = true }
                          or id == 0xFFFB and { name = missions and 'No completed missions.' or 'None.', heading = true,
                                                none = true }
                          or qt[id] or { name = '?', text = '' };
    end
    if cur and cur < n then
        if cur < view_first then view_first = cur; end
        if cur >= view_first + SHOWN then view_first = cur - SHOWN + 1; end
    else
        cur = nil;
    end
    view_first = math.max(0, math.min(view_first, math.max(0, n - SHOWN)));

    local shown = math.min(SHOWN, n);
    local sel = cur and rows[cur + 1];
    if sel and sel.heading then sel = nil; end
    local desc = ui.label('qst_desc', 'small', { font_height = 16, font_color = 0xFFE8E4D8, box_width = W - 48 });
    -- (FFXI wraps the text for its own box: lines that carry on start with a space)
    local dtext = sel and (sel.text:gsub('\n ', ' '):gsub('^%s+', '')) or '';
    if desc.settings.text ~= dtext then text.set(desc, dtext); end
    local _, dh = text.size(desc);
    -- Confirm on a quest: the game turns the same window into that quest's page (class +0x64 = 1) until Back
    if not missions and sel and mem.u32(cls + 0x64) == 1 then
        local body = ui.label('qst_page', 'small', { font_height = 18, font_color = 0xFFE8E4D8, box_width = W - 56 });
        if body.settings.text ~= dtext then text.set(body, dtext); end
        local _, bh2 = text.size(body);
        local PH = 52 + 18 + bh2 + 40;
        local px, py = layout.anchor('topleft', W, PH, 40, 60, 'quests');
        local pc = draw.alpha(0xFFFFFFFF, a);
        local bw, bh = layout.size('win_body');
        draw.nine('win_body', px, py, W, PH, 12, bw, bh, pc);
        local tw, th = layout.size('win_title');
        draw.nine('win_title', px + 4, py + 4, W - 8, 30, 10, tw, th, pc);
        draw.image('title_swash', px + 8, py + 4, { color = pc });
        local title = ui.label('qst_title', 'name', { font_height = 22 });
        title:set_opacity(a);
        text.draw(title, sel.name:gsub('^%s+', ''), px + 40, py + 27, 'baseline');
        local area_l = ui.label('qst_range', 'small', { font_height = 14, font_color = 0xFFC8C4B8,
                                                         font_alignment = text.align.Right });
        area_l:set_opacity(a);
        text.draw(area_l, AREAS[area][1] .. ': ' .. mode, px + W - 20, py + 25, 'baseline');
        body:set_opacity(a);
        text.draw(body, dtext, px + 28, py + 52);
        local hint = ui.label('qst_hint', 'small', { font_height = 14, font_color = 0xFFB8C0D8 });
        hint:set_opacity(a);
        text.draw(hint, 'Back: the list', px + 24, py + PH - 12, 'baseline');
        return;
    end
    local H = 52 + math.max(1, shown) * ROW_H + (sel and dh + 30 or 20) + 26;
    local x, y = layout.anchor('topleft', W, H, 40, 60, 'quests');
    local col = draw.alpha(0xFFFFFFFF, a);
    local bw, bh = layout.size('win_body');
    draw.nine('win_body', x, y, W, H, 12, bw, bh, col);
    local tw, th = layout.size('win_title');
    draw.nine('win_title', x + 4, y + 4, W - 8, 30, 10, tw, th, col);
    draw.image('title_swash', x + 8, y + 4, { color = col });
    local title = ui.label('qst_title', 'name', { font_height = 22 });
    title:set_opacity(a);
    text.draw(title, missions and MISSION_AREAS[area][1] or (AREAS[area][1] .. ': ' .. mode), x + 40, y + 27,
              'baseline');
    -- Left / Right: the other areas
    draw.image('dlg_arrow', x + W - 74, y + 12, { rot = -math.pi / 2, color = col });
    draw.image('dlg_arrow', x + W - 30, y + 12, { rot = math.pi / 2, color = col });

    if n == 0 then
        local none = ui.label('qst_none', 'small', { font_height = 17, font_color = 0xFFB8C0D8 });
        none:set_opacity(a);
        text.draw(none, missions and 'No missions.' or mode == 'Current Quests' and 'No current quests.'
                  or 'No completed quests.', x + 34,
                  y + 72, 'baseline');
    end
    local sw, sh = layout.size('row_sel');
    for r = 1, shown do
        local i = view_first + r;
        local q = rows[i];
        local ry = y + 44 + (r - 1) * ROW_H;
        local on = (cur and i - 1 == cur);
        if on then
            draw.nine('row_sel', x + 22, ry, W - 44, ROW_H - 2, 6, sw, sh, col);
            draw.image('cursor_gold', x + 2, ry + 1, { color = col });
        end
        local o = ui.label('qst_row' .. r, 'small', { font_height = 18 });
        local c = q.none and 0xFF8C887C or q.heading and 0xFFC8A860 or on and 0xFFFFFFFF or 0xFFD8D4C8;
        if o.settings.font_color ~= c then o:set_font_color(c); end
        o:set_opacity(a);
        text.draw(o, q.name, x + ((q.heading and not q.none) and 28 or 40), ry + ROW_H - 8, 'baseline');
    end
    if n > SHOWN then
        local rg = ui.label('qst_range', 'small', { font_height = 14, font_color = 0xFFC8C4B8,
                                                     font_alignment = text.align.Right });
        rg:set_opacity(a);
        text.draw(rg, string.format('%d-%d / %d', view_first + 1, view_first + shown, n), x + W - 90, y + 25,
                  'baseline');
    end
    local dy = y + 52 + math.max(1, shown) * ROW_H;
    if sel then
        draw.rect(x + 20, dy - 2, W - 40, 1, draw.alpha(0x60C8A860, a));
        desc:set_opacity(a);
        text.draw(desc, dtext, x + 24, dy + 10);
    end
    local hint = ui.label('qst_hint', 'small', { font_height = 14, font_color = 0xFFB8C0D8 });
    hint:set_opacity(a);
    text.draw(hint, missions and 'Left / Right: other storylines' or 'Left / Right: other areas', x + 24, y + H - 12,
              'baseline');
end

return quests;
