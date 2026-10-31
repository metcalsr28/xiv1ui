--[[
* xiv1ui - the game's ability and spell lists (Commands » Abilities » Job Abilities / Weapon Skills, Commands »
* Magic » White Magic ...) in xiv1ui's style. The game keeps running its list window ("menu    ability" /
* "menu    magic"): moving, using and targeting work as before.
*
* The list rows carry no text, so xiv1ui builds the list from game data (what the player has learned, from the
* resource manager) and finds the entry under the game's cursor from the help bar: the help window's class object
* points to the current help line at +0x68, which is the entry's description. Matching it against the resources'
* descriptions names the lit entry exactly, whatever order the game lists things in.
--]]

local mem     = require('core.mem');
local draw    = require('core.draw');
local text    = require('core.text');
local layout  = require('core.layout');
local ui      = require('core.ui');
local store   = require('core.store');
local native  = require('core.native');
local gamewin = require('core.gamewin');

local panel = {};

local hider = gamewin.new();
local WINDOWS = { ability = true, magic = true };

local help_slot = nil;
--- The game's current help line (the description of whatever its cursor is on), or ''.
function panel.help_line()
    help_slot = require('core.gamewin').slot('helpwind') or false;
    if not help_slot then return ''; end
    local cls = mem.u32(help_slot);
    local p = cls and mem.u32(cls + 0x68);
    if not p or not mem.ok(p, 4) then return ''; end
    return (ashita.memory.read_string(p, 240) or ''):match('^[^%z]*') or '';
end

local ACTION = { playermo = true, battlemo = true };

local function norm(s) return ((s or ''):gsub('%s+', ' '):gsub('^ ', ''):gsub(' $', '')); end

local SPELL_TYPES = { ['White Magic'] = 1, ['Black Magic'] = 2, ['Summoning'] = 3, ['Ninjutsu'] = 4, ['Songs'] = 5,
                      ['Blue Magic'] = 6, ['Geomancy'] = 7, ['Trust'] = 8 };

local cache = { key = nil, list = nil, t = 0 };
-- Commands » Abilities lists built from the ability resource (category label -> id range and type)
local ABILITY_LISTS = {
    ['Weapon Skills'] = { from = 1, to = 255 },
    ['Job Abilities'] = { from = 512, to = 1023, type = 1 },
    ['Pet Command']   = { from = 512, to = 1023, type = 2 },
    ['Pet Commands']  = { from = 512, to = 1023, type = 2 },
    ['Job Traits']    = { from = 1536, to = 2047, type = 4 },
};
local type_cache = {};       -- help line -> spell type name (or false)

--- The entries the game lists for a category: { name, desc, sub (right-hand text), dim }.
local function entries(category)
    local now = os.time();
    if cache.key == category and cache.list and now - cache.t < 2 then return cache.list; end
    local rm = AshitaCore:GetResourceManager();
    local pl = AshitaCore:GetMemoryManager():GetPlayer();
    local job, lvl = pl:GetMainJob(), pl:GetMainJobLevel();
    local sjob, slvl = pl:GetSubJob(), pl:GetSubJobLevel();
    local out = {};
    if ABILITY_LISTS[category] then
        -- the ability resource: weapon skills 1-255, job abilities (type 1) and pet commands (type 2) 512-1023,
        -- job traits (type 4) from 1536
        local ws = (category == 'Weapon Skills');
        local want = ABILITY_LISTS[category];
        for id = want.from, want.to do
            local ok, has = pcall(function () if ws then return pl:HasWeaponSkill(id); end return pl:HasAbility(id); end);
            if ok and has then
                local a = rm:GetAbilityById(id);
                if a and a.Name and (a.Name[1] or '') ~= '' and (want.type == nil or a.Type == want.type) then
                    out[#out + 1] = { name = a.Name[1], desc = a.Description and a.Description[1] or '' };
                end
            end
        end
    else
        local ty = SPELL_TYPES[category];
        for id = 1, 1023 do
            local ok, has = pcall(function () return pl:HasSpell(id); end);
            if ok and has then
                local sp = rm:GetSpellById(id);
                if sp and (ty == nil or sp.Type == ty) and sp.Name and (sp.Name[1] or '') ~= '' then
                    local need = nil;
                    pcall(function ()
                        local a, b = sp.LevelRequired[job + 1], sp.LevelRequired[sjob + 1];
                        need = (a and a > 0 and a <= lvl) or (b and b > 0 and b <= slvl);
                    end);
                    out[#out + 1] = { name = sp.Name[1], desc = sp.Description and sp.Description[1] or '',
                                      sub = (sp.ManaCost or 0) > 0 and (sp.ManaCost .. ' MP') or nil,
                                      dim = (need == false) };
                end
            end
        end
    end
    cache.key, cache.list, cache.t = category, out, now;
    return out;
end

function panel.release() hider:restore(); end

local W, ROWS, ROW_H = 440, 12, 32;
local view = { key = nil, first = 0 };      -- scroll position of the list shown
local desc_obj = nil;
local ring_since = nil;     -- when the ring form appeared (slide-in)
local last_ring = nil;      -- the ring last drawn { key, items, cursor, since }

function panel.render()
    if store.data.cmd_menu == false then if hider:active() then hider:restore(); end return; end
    local _, fname = native.focused();
    if not WINDOWS[fname] then
        -- a spell or ability chosen from the ring: the game hides its list while you choose the target; the ring
        -- stays, dimmed, with the target hint
        local cmdm = require('ui.cmdmenu');
        if last_ring and fname == nil and cmdm.choosing() then
            cmdm.ring(last_ring[1], last_ring[2], last_ring[3], last_ring[4], true);
            return;
        end
        -- just confirmed: the game may reopen the list in a moment (e.g. out of range); keep things as they are
        if last_ring and cmdm.grace() then
            cmdm.ring(last_ring[1], last_ring[2], last_ring[3], last_ring[4], false);
            return;
        end
        ring_since, last_ring = nil, nil;
        if hider:active() then hider:release_except({ 'magic', 'ability' }); end
        return;
    end
    local last = require('ui.cmdmenu').last_choice;
    -- which list: the entry chosen in the menu it was opened from (Commands » Abilities / Magic, or the action menu)
    local cmdm = require('ui.cmdmenu');
    local from = cmdm.last_menu == 'abiselec' and last.abiselec or last.abimenu;
    local category = fname == 'ability' and (from or 'Job Abilities') or ((cmdm.last_menu == 'magselec' and last.magselec) or (ACTION[cmdm.last_menu] and (last[cmdm.last_menu] == 'Trust' and 'Trust' or 'White Magic')) or last.mgcmenu or 'White Magic');
    if fname == 'ability' and not ABILITY_LISTS[category] then
        -- other lists in the ability window (Ranged Attack ...) aren't built yet: the game draws its own
        if hider:active() then hider:restore(); end
        return;
    end
    hider:hide({ fname, 'helpwind', 'titlewin', 'abisortw', 'mgcsortw', 'subwindo' });

    local help = norm(panel.help_line());
    -- a spell list: the type of the spell under the cursor wins (the action menu's Magic has no type choice before it)
    if fname == 'magic' and help ~= '' then
        if type_cache[help] == nil then
            type_cache[help] = false;
            local rm = AshitaCore:GetResourceManager();
            local pl = AshitaCore:GetMemoryManager():GetPlayer();
            for id = 1, 1023 do
                local sp = rm:GetSpellById(id);
                if sp and sp.Description and norm(sp.Description[1]) == help and pl:HasSpell(id) then
                    for k, v in pairs(SPELL_TYPES) do if v == sp.Type then type_cache[help] = k; end end
                    break;
                end
            end
        end
        category = type_cache[help] or category;
    end
    local list = entries(category);
    local at = nil;
    for i, e in ipairs(list) do if norm(e.desc) == help then at = i; break; end end

    -- opened from the action menu: the same ring as the menu, in its place
    local cmdm_ = require('ui.cmdmenu');
    if cmdm_.action_spot() then
        if not ring_since then ring_since = require('core.now')(); end
        local items = {};
        for i, e in ipairs(list) do items[i] = { label = e.name, sub = e.sub, dim = e.dim }; end
        if #items == 0 then items[1] = { label = fname == 'magic' and 'No spells learned' or 'None available', dim = true }; end
        local d = at and list[at].desc or help;
        last_ring = { 'list:' .. category, items, at, ring_since };
        cmdm_.ring('list:' .. category, items, at, ring_since, require('ui.cmdmenu').choosing(), ((d or ''):gsub('\n', ' ')));
        return;
    end
    ring_since, last_ring = nil, nil;
    local H = 50 + ROWS * ROW_H + 110;
    local x, y = layout.anchor('topleft', W, H, 24, 40, 'listpanel');
    -- opened from the action menu: in the menu's place, beside the character
    local ax, ay = require('ui.cmdmenu').action_spot();
    if ax then
        local sw, sh = layout.screen();
        x, y = math.min(ax, sw - W - 10), math.max(10, math.min(ay, sh - H - 10));
    end
    layout.bounds('listpanel', x, y, W, H);
    local bw, bh = layout.size('win_body');
    draw.nine('win_body', x, y, W, H, 12, bw, bh);
    local tw, th = layout.size('win_title');
    draw.nine('win_title', x + 4, y + 4, W - 8, 30, 10, tw, th);
    draw.image('title_swash', x + 8, y + 4);
    local title = ui.label('lsp_title', 'name', { font_height = 22 });
    text.draw(title, category == 'Trust' and 'Trust' or category, x + 40, y + 27, 'baseline');

    if #list == 0 then
        local none = ui.label('lsp_none', 'small', { font_height = 17, font_color = 0xFFB8C0D8 });
        text.draw(none, fname == 'magic' and 'No spells learned.' or 'None available.', x + 34, y + 76, 'baseline');
    end
    local sw, sh = layout.size('row_sel');
    -- the view only scrolls when the cursor leaves it (as the game's lists do)
    local first = (view.key == category) and view.first or 0;
    if at then
        if at <= first then first = at - 1; elseif at > first + ROWS then first = at - ROWS; end
    end
    first = math.max(0, math.min(first, math.max(0, #list - ROWS)));
    view.key, view.first = category, first;
    for r = 1, math.min(ROWS, #list - first) do
        local i = r + first;
        local e = list[i];
        local ry = y + 46 + (r - 1) * ROW_H;
        local sel = (i == at);
        if sel then
            draw.nine('row_sel', x + 22, ry, W - 34, ROW_H - 4, 6, sw, sh);
            draw.image('cursor_gold', x + 2, ry + (ROW_H - 26) / 2);
        end
        local o = ui.label('lsp_r' .. r, 'small', { font_height = 18 });
        local col = e.dim and 0xFF9098A0 or (sel and 0xFFFFFFFF or 0xFFE8E4D8);
        if o.settings.font_color ~= col then o:set_font_color(col); end
        text.draw(o, e.name, x + 36, ry + 21, 'baseline');
        if e.sub then
            local q = ui.label('lsp_q' .. r, 'small', { font_height = 15, font_color = 0xFFC8C4B8, font_alignment = text.align.Right });
            text.draw(q, e.sub, x + W - 22, ry + 21, 'baseline');
        end
    end

    local dy = y + 46 + ROWS * ROW_H + 4;
    draw.image('name_rule', x + 16, dy, { scale = { (W - 32) / 300, 1 } });
    local d = at and list[at].desc or help;
    if d ~= '' then
        desc_obj = desc_obj or text.new('small', { font_height = 16, font_color = 0xFFE8E4D8, box_width = W - 44 });
        d = d:gsub('\n', ' ');
        if desc_obj.settings.text ~= d then text.set(desc_obj, d); end
        text.render(desc_obj, x + 22, dy + 10);
    end
end

return panel;
