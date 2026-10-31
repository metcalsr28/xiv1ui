--[[
* xiv1ui - the Status panel. When the game shows its small status summary (Commands » Status: windows
* "menu    persona" and "menu    level", top left), xiv1ui hides them and draws a larger panel in the 1.0 window
* style: name, race / nation, main and support job with levels, HP / MP / TP tubes, the seven stats with gear
* bonuses, attack / defense, elemental resistances and EXP. The game keeps running its menu; this is presentation
* only, and the game's panels come back when the menu closes or xiv1ui unloads.
--]]

local mem    = require('core.mem');
local native = require('core.native');
local draw   = require('core.draw');
local text   = require('core.text');
local layout = require('core.layout');
local ui     = require('core.ui');
local store  = require('core.store');
local xi_now = require('core.now');

local panel = {};

local W, H = 520, 470;
local STATS = { 'STR', 'DEX', 'VIT', 'AGI', 'INT', 'MND', 'CHR' };
local ELEMENTS = { 'Fire', 'Ice', 'Wind', 'Earth', 'Lightning', 'Water', 'Light', 'Dark' };
local EL_COL = { 0xFFFF8A6A, 0xFF9ADCF0, 0xFF9BE08C, 0xFFE0C080, 0xFFC8A0F0, 0xFF8CB4FF, 0xFFFFF4C0, 0xFFC8B8E0 };
local RACES = { [1] = 'Hume', [2] = 'Hume', [3] = 'Elvaan', [4] = 'Elvaan', [5] = 'Tarutaru', [6] = 'Tarutaru',
                [7] = 'Mithra', [8] = 'Galka' };
local NATIONS = { [0] = "San d'Oria", 'Bastok', 'Windurst' };
local OWN = { 'persona', 'level' };
-- Status sub-screens: when one is open, the panel shows that list instead (and the game's window is hidden too)
local SUBS = { profile = 'Profile', joblevel = 'Job Levels', btlskill = 'Combat Skills', mgcskill = 'Magic Skills', trdskill = 'Craft Skills' };
local COMBAT = { { 1, 'Hand-to-Hand' }, { 2, 'Dagger' }, { 3, 'Sword' }, { 4, 'Great Sword' }, { 5, 'Axe' },
    { 6, 'Great Axe' }, { 7, 'Scythe' }, { 8, 'Polearm' }, { 9, 'Katana' }, { 10, 'Great Katana' }, { 11, 'Club' },
    { 12, 'Staff' }, { 25, 'Archery' }, { 26, 'Marksmanship' }, { 27, 'Throwing' }, { 28, 'Guard' }, { 29, 'Evasion' },
    { 30, 'Shield' }, { 31, 'Parrying' } };
local MAGIC = { { 32, 'Divine Magic' }, { 33, 'Healing Magic' }, { 34, 'Enhancing Magic' }, { 35, 'Enfeebling Magic' },
    { 36, 'Elemental Magic' }, { 37, 'Dark Magic' }, { 38, 'Summoning Magic' }, { 39, 'Ninjutsu' }, { 40, 'Singing' },
    { 41, 'String Instrument' }, { 42, 'Wind Instrument' }, { 43, 'Blue Magic' }, { 44, 'Geomancy' }, { 45, 'Handbell' } };
local CRAFTS = { { 0, 'Fishing' }, { 1, 'Woodworking' }, { 2, 'Smithing' }, { 3, 'Goldsmithing' }, { 4, 'Clothcraft' },
    { 5, 'Leathercraft' }, { 6, 'Bonecraft' }, { 7, 'Alchemy' }, { 8, 'Cooking' }, { 9, 'Synergy' } };

local slots = {};
local hidden = {};       -- name -> { obj, b69, b6a }
local scaled = {};       -- row -> window obj: row objects (panel pieces) we set to scale 0
local ffi = require('ffi');

-- A window's row objects (its separately drawn pieces), from its row list at obj+0x14 (see ui/cmdmenu.lua).
local function rows_of(obj)
    local out, n = {}, mem.u32(obj + 0x14);
    while n and n ~= 0 and #out < 120 and mem.ok(n, 0x14) do
        local r = mem.u32(n + 0x10);
        if r and mem.ok(r, 0x70) and mem.u32(r + 0x58) == r and mem.u32(r + 0x5C) == obj then out[#out + 1] = r; end
        n = mem.u32(n);
    end
    return out;
end
local shown_at = nil;

local function window(name)
    slots[name] = require('core.gamewin').slot(name) or false;
    return slots[name] and mem.chain(slots[name], 0, 8) or nil;
end

local function hide(name, obj)
    for _, r in ipairs(rows_of(obj)) do
        if scaled[r] ~= obj then
            local sc = ffi.cast('float*', r + 0x1C);
            if sc[0] == 1 and sc[1] == 1 then sc[0], sc[1] = 0, 0; scaled[r] = obj; end
        end
    end
    local h = hidden[name];
    if h and h[1] == obj then
        if mem.u8(obj + 0x69) ~= 0 then mem.w8(obj + 0x69, 0); end
        if mem.u8(obj + 0x6A) ~= 0 then mem.w8(obj + 0x6A, 0); end
        return;
    end
    local a, b = mem.u8(obj + 0x69), mem.u8(obj + 0x6A);
    if a == nil or a > 1 or b == nil or b > 1 then return; end
    hidden[name] = { obj, a, b };
    mem.w8(obj + 0x69, 0); mem.w8(obj + 0x6A, 0);
end

local function restore()
    for r, obj in pairs(scaled) do
        if mem.ok(r, 0x70) and mem.u32(r + 0x58) == r and mem.u32(r + 0x5C) == obj then
            local sc = ffi.cast('float*', r + 0x1C);
            if sc[0] == 0 and sc[1] == 0 then sc[0], sc[1] = 1, 1; end
        end
    end
    scaled = {};
    for name, h in pairs(hidden) do
        if window(name) == h[1] then
            if mem.u8(h[1] + 0x69) == 0 then mem.w8(h[1] + 0x69, h[2]); end
            if mem.u8(h[1] + 0x6A) == 0 then mem.w8(h[1] + 0x6A, h[3]); end
        end
    end
    hidden = {};
end

function panel.release() restore(); end

local function tube(name, x, y, w, frac, color)
    local tw, th = layout.size('tube_track_party');
    draw.image('tube_track_party', x, y, { scale = { w / tw, 1 } });
    local fw, fh = layout.size(name);
    local f = math.max(0, math.min(1, frac));
    if f > 0 then draw.image(name, x, y, { sw = math.floor(fw * f + 0.5), scale = { w / tw, 1 } }); end
end

local function row(key, label, value, x, y, w, lcol, vcol)
    local l = ui.label('sp_l' .. key, 'small', { font_height = 17 });
    lcol, vcol = lcol or 0xFFF0DCA0, vcol or 0xFFF4F0E6;
    if l.settings.font_color ~= lcol then l:set_font_color(lcol); end      -- labels are reused between views
    text.draw(l, label, x, y, 'baseline');
    local v = ui.label('sp_v' .. key, 'small', { font_height = 17, font_alignment = text.align.Right });
    if v.settings.font_color ~= vcol then v:set_font_color(vcol); end
    text.draw(v, tostring(value), x + w, y, 'baseline');
end

function panel.render()
    if store.data.status_panel == false then if next(hidden) then restore(); end return; end
    local persona = window('persona');
    if persona == nil then
        if next(hidden) then restore(); end
        shown_at = nil;
        return;
    end
    hide('persona', persona);
    local lv = window('level');
    if lv then hide('level', lv); end
    -- the Equipment screen has the summary open too: there xiv1ui's Equipment panel takes the space
    local eq = window('equip');
    if eq then return; end
    -- a Status screen xiv1ui doesn't draw (Currencies, Unity ...) opens where the panel is: let it show
    local _, fname = require('core.native').focused();
    if fname ~= nil and fname ~= 'statcom2' and fname ~= 'menuwind' and fname ~= 'persona' then return; end
    shown_at = shown_at or xi_now();
    local t = math.min(1, (xi_now() - shown_at) / 0.15);

    local mm = AshitaCore:GetMemoryManager();
    local p, party, r = mm:GetPlayer(), mm:GetParty(), AshitaCore:GetResourceManager();
    local x, y = layout.anchor('topleft', W, H, 24, 40, 'statuspanel');
    layout.bounds('statuspanel', x, y, W, H);
    local col = draw.alpha(0xFFFFFFFF, t);
    local bw, bh = layout.size('win_body');
    draw.nine('win_body', x, y, W, H, 12, bw, bh, col);
    local tw, th = layout.size('win_title');
    draw.nine('win_title', x + 4, y + 4, W - 8, 30, 10, tw, th, col);
    draw.image('title_swash', x + 8, y + 4, { color = col });
    local title = ui.label('sp_title', 'name', { font_height = 22 });
    text.draw(title, 'Status', x + 40, y + 27, 'baseline');

    -- who
    local name = party:GetMemberName(0) or '';
    local nm = ui.label('sp_name', 'name', { font_height = 28 });
    text.draw(nm, name, x + 24, y + 74, 'baseline');
    local ent = mm:GetEntity();
    local idx = party:GetMemberTargetIndex(0);
    local race = RACES[ent:GetRace(idx) or 0] or '';
    local sub = ui.label('sp_sub', 'small', { font_height = 16, font_color = 0xFFB8C0D8 });
    text.draw(sub, string.format('%s  ·  %s', race, NATIONS[p:GetNation()] or ''), x + 26, y + 96, 'baseline');

    local function job(id) return (r:GetString('jobs.names', id) or ''); end
    local main, mlv = p:GetMainJob(), p:GetMainJobLevel();
    local sj, slv = p:GetSubJob(), p:GetSubJobLevel();
    local jl = ui.label('sp_job', 'label', { font_height = 20, font_color = 0xFF9BE08C, font_alignment = text.align.Right });
    text.draw(jl, string.format('%s  Lv. %d', job(main), mlv), x + W - 24, y + 70, 'baseline');
    if sj and sj > 0 then
        local sl = ui.label('sp_sj', 'small', { font_height = 16, font_color = 0xFFC8D4F0, font_alignment = text.align.Right });
        text.draw(sl, string.format('Support: %s  Lv. %d', job(sj), slv), x + W - 24, y + 94, 'baseline');
    end

    -- HP / MP / TP
    local hp, mhp = party:GetMemberHP(0), p:GetHPMax();
    local mp, mmp = party:GetMemberMP(0), p:GetMPMax();
    local tp = party:GetMemberTP(0);
    local gy = y + 122;
    local function gauge(i, label, v, maxv, fill, frac)
        local gx = x + 24 + (i - 1) * 160;
        row('g' .. i, label, maxv and string.format('%d / %d', v, maxv) or v, gx, gy, 146);
        tube(fill, gx, gy + 8, 146, frac);
    end
    gauge(1, 'HP', hp, mhp, 'tube_fill_party_hp', mhp > 0 and hp / mhp or 0);
    gauge(2, 'MP', mp, mmp, 'tube_fill_party_mp', mmp > 0 and mp / mmp or 0);
    gauge(3, 'TP', tp, nil, 'tube_fill_party_tp', tp / 3000);

    -- a Status sub-screen open? show its list here instead of attributes / resistances
    for wname, label in pairs(SUBS) do
        local o = window(wname);
        if o then hide(wname, o); return panel.sub(wname, label, x, y, p, r); end
    end

    -- stats and resistances
    ui.header('sp_hst', 'Attributes', x + 24, y + 176, 220);
    for i, n in ipairs(STATS) do
        local base, mod = p:GetStat(i - 1) or 0, p:GetStatModifier(i - 1) or 0;
        local v = mod ~= 0 and string.format('%d  %s%d', base, mod > 0 and '+' or '', mod) or tostring(base);
        row('st' .. i, n, v, x + 34, y + 204 + (i - 1) * 24, 196);
    end
    row('atk', 'Attack', p:GetAttack() or 0, x + 34, y + 204 + 7 * 24 + 6, 196, 0xFFFFC890);
    row('def', 'Defense', p:GetDefense() or 0, x + 34, y + 204 + 8 * 24 + 6, 196, 0xFFFFC890);
    ui.header('sp_hel', 'Resistances', x + 276, y + 176, 220);
    for i, n in ipairs(ELEMENTS) do
        row('el' .. i, n, p:GetResist(i - 1) or 0, x + 286, y + 204 + (i - 1) * 24, 206, EL_COL[i]);
    end

    -- EXP
    local cur, need = p:GetExpCurrent() or 0, p:GetExpNeeded() or 0;
    row('exp', 'EXP', string.format('%d / %d', cur, need), x + 24, y + H - 34, W - 48);
    local ew, eh = layout.size('exp_track');
    draw.image('exp_track', x + 24, y + H - 26, { scale = { (W - 48) / ew, 1 } });
    if need > 0 and cur > 0 then
        local fw = layout.size('exp_fill');
        draw.image('exp_fill', x + 24, y + H - 26, { sw = math.floor(fw * math.min(1, cur / need)), scale = { (W - 48) / ew, 1 } });
    end
end

local function skill_value(v)
    if v == nil then return 0; end
    if type(v) == 'number' then return v; end
    local ok, n = pcall(function () return v:GetSkill(); end);
    return ok and n or 0;
end

--- The body of the panel for a Status sub-screen: two columns of name / value rows.
function panel.sub(wname, label, x, y, p, r)
    ui.header('sp_hsub', label, x + 24, y + 176, W - 60);
    local items = {};
    if wname == 'profile' then
        local function zone(id) return (id and id > 0) and (r:GetString('zones.names', id) or tostring(id)) or '—'; end
        local title = r:GetString('titles', p:GetTitle() or 0) or '';
        local list = {
            { 'Nation', NATIONS[p:GetNation()] or '—' }, { 'Rank', p:GetRank() or 0 },
            { 'Rank Points', p:GetRankPoints() or 0 }, { 'Title', title ~= '' and title or '—' },
            { 'Residence', zone(p:GetResidence()) }, { 'Home Point', zone(p:GetHomepoint()) },
            { 'Merit Points', string.format('%d / %d', p:GetMeritPoints() or 0, p:GetMeritPointsMax() or 0) },
            { 'Limit Points', p:GetLimitPoints() or 0 }, { 'Unity Points', p:GetUnityPoints() or 0 },
        };
        local step = 28;
        for i, it in ipairs(list) do
            row('pf' .. i, it[1], it[2], x + 34, y + 210 + (i - 1) * step, W - 80);
        end
        return;
    elseif wname == 'joblevel' then
        local main, sj = p:GetMainJob(), p:GetSubJob();
        for j = 1, 22 do
            local lv = p:GetJobLevel(j) or 0;
            local col = (j == main) and 0xFF9BE08C or (j == sj and 0xFFC8D4F0) or (lv > 0 and 0xFFF4F0E6 or 0xFF7C8090);
            items[#items + 1] = { r:GetString('jobs.names', j) or ('Job ' .. j), lv > 0 and lv or '—', col };
        end
    else
        local list = (wname == 'btlskill' and COMBAT) or (wname == 'mgcskill' and MAGIC) or CRAFTS;
        for _, e in ipairs(list) do
            local v = (wname == 'trdskill') and skill_value(p:GetCraftSkill(e[1])) or skill_value(p:GetCombatSkill(e[1]));
            if v > 999 then v = 0; end
            items[#items + 1] = { e[2], v > 0 and v or '—', v > 0 and 0xFFF4F0E6 or 0xFF7C8090 };
        end
    end
    local per = math.ceil(#items / 2);
    local step = math.min(24, math.floor((H - 250) / per));
    for i, it in ipairs(items) do
        local c, rr = math.floor((i - 1) / per), (i - 1) % per;
        row('sub' .. i, it[1], it[2], x + 34 + c * 250, y + 204 + rr * step, 206, it[3], it[3]);
    end
end

return panel;
