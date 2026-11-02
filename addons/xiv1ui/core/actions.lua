--[[
* xiv1ui - actions: what an action-bar slot is bound to, and everything the bar needs to know about it.
*
* A binding is a small table saved in the settings: { kind = 'ma'|'ja'|'ws'|'item'|'cmd', name = '...', [target],
* [label], [command] }. resolve() turns it into display/state info; use() runs it through the game's own commands.
--]]

local actions = {};

-- painted icons for spells / abilities / weapon skills / commands (tools/make_action_icons.py)
local ok_icons, ICONS = pcall(require, 'core.action_icons');
if not ok_icons then ICONS = {}; end

ICONS.ma, ICONS.ja, ICONS.cmd = ICONS.ma or {}, ICONS.ja or {}, ICONS.cmd or {};
-- signature icons (tools/make_signature_icons.py): round paintings drawn in place of the disc and emblem
local ok_sig, SIGNATURE = pcall(require, 'core.signature_icons');
if not ok_sig or type(SIGNATURE) ~= 'table' then SIGNATURE = {}; end
SIGNATURE.ma, SIGNATURE.ja = SIGNATURE.ma or {}, SIGNATURE.ja or {};
-- a spell's family name (Cure II -> Cure, Utsusemi: Ni -> Utsusemi)
local function family(name)
    return (name:gsub('%s+[IVX]+$', ''):gsub(':%s*%a+$', ''));
end

--- The painted icon for an action name (a spell, ability, weapon skill or command), or nil. kind ('ma', 'ja',
-- 'cmd') picks between a spell and an ability of the same name; without it, spells first.
function actions.icon_for(name, kind)
    if kind then return ICONS[kind][name]; end
    if ICONS.ma[name] or ICONS.ja[name] or ICONS.cmd[name] then return ICONS.ma[name] or ICONS.ja[name] or ICONS.cmd[name]; end
    local s = AshitaCore:GetResourceManager():GetSpellByName(name or '', 0);
    if s and s.Type == 8 then return ICONS.ma['*Trust']; end
    return nil;
end

local ELEMENT = { [0] = 'fire', 'ice', 'wind', 'earth', 'thunder', 'water', 'light', 'dark' };

-- Ability ids in Ashita's resource table: weapon skills below 512, job abilities from 512.
local JA_BASE = 512;

local function res() return AshitaCore:GetResourceManager(); end
local function mm() return AshitaCore:GetMemoryManager(); end

--- Default target for a spell/ability from its Targets bitmask (1 = self, 32 = enemy).
local function default_target(targets)
    if targets and bit.band(targets, 32) ~= 0 then return '<t>'; end
    if targets and bit.band(targets, 1) ~= 0 and bit.band(targets, 0x3E) == 0 then return '<me>'; end
    return '<t>';
end

--- Recast timer for an ability's RecastTimerId (1/60 s ticks).
local function ability_timer(timer_id)
    local r = mm():GetRecast();
    if timer_id == 0 then return r:GetAbilityTimer(0); end
    for i = 1, 31 do
        if r:GetAbilityTimerId(i) == timer_id then return r:GetAbilityTimer(i); end
    end
    return 0;
end

--- Short glyph text for a disc: initials of the first word(s) and a trailing tier numeral.
local NIN_TIER = { Ichi = 'I', Ni = 'II', San = 'III' };
function actions.glyph(name)
    local tier = name:match('%s([IVX]+)$') or NIN_TIER[name:match(':%s*(%a+)$') or ''] or '';
    local base = name:gsub('%s[IVX]+$', ''):gsub(':%s*%a+$', '');
    local words = {};
    for w in base:gmatch('[%a\']+') do words[#words + 1] = w; end
    local g;
    if #words >= 2 then
        g = words[1]:sub(1, 1):upper() .. words[2]:sub(1, 1):lower();
    else
        g = (words[1] or '?'):sub(1, 2);
    end
    return g, tier;
end

--- Resolve a binding into what the bar shows. Returns a table or nil for an empty slot.
-- Fields: label, disc (texture), glyph, tier, item_id, cost, cost_kind ('MP'|'TP'), usable, timer (ticks), command
function actions.resolve(b)
    if b == nil then return nil; end
    local info = { label = b.label or b.name, cost = nil, usable = true, timer = 0 };
    local player = mm():GetPlayer();
    local party = mm():GetParty();

    if b.kind == 'ma' then
        local s = res():GetSpellByName(b.name, 0);
        if s == nil then info.disc = 'disc_command'; info.glyph = '?'; info.tier = ''; return info; end
        info.disc = 'disc_' .. (ELEMENT[s.Element] or 'light');
        info.motif = 'motif_wand';
        info.kind_label = 'Spell';
        info.cast = s.CastTime / 4;           -- resource times are in quarter seconds
        info.recast = s.RecastDelay / 4;
        info.glyph, info.tier = actions.glyph(b.name);
        info.icon = ICONS.ma[b.name] or (s.Type == 8 and ICONS.ma['*Trust']) or nil;
        local sig = SIGNATURE.ma[b.name] or SIGNATURE.ma[family(b.name)];
        if sig then info.disc, info.icon, info.sig = sig, nil, true; end
        info.cost, info.cost_kind = s.ManaCost, 'MP';
        info.usable = party:GetMemberMP(0) >= s.ManaCost;
        info.timer = mm():GetRecast():GetSpellTimer(s.Index);
        info.command = string.format('/ma "%s" %s', b.name, b.target or default_target(s.Targets));
    elseif b.kind == 'ja' or b.kind == 'ws' then
        local a = res():GetAbilityByName(b.name, 0);
        if a == nil then info.disc = 'disc_command'; info.glyph = '?'; info.tier = ''; return info; end
        local is_ws = a.Id < JA_BASE;
        info.disc = is_ws and 'disc_weaponskill' or 'disc_ability';
        info.motif = 'motif_sword';
        info.kind_label = is_ws and 'Weapon Skill' or 'Ability';
        info.glyph, info.tier = actions.glyph(b.name);
        info.icon = ICONS.ja[b.name];
        local sig = SIGNATURE.ja[b.name];
        if sig then info.disc, info.icon, info.sig = sig, nil, true; end
        if is_ws then
            info.cost, info.cost_kind = 1000, 'TP';
            info.usable = party:GetMemberTP(0) >= 1000;
            info.ready = info.usable;              -- "use condition met": blue ring
            info.command = string.format('/ws "%s" %s', b.name, b.target or '<t>');
        else
            if a.TPCost and a.TPCost > 0 then info.cost, info.cost_kind = a.TPCost, 'TP'; end
            if a.ManaCost and a.ManaCost > 0 then info.cost, info.cost_kind = a.ManaCost, 'MP'; end
            info.timer = ability_timer(a.RecastTimerId);
            info.command = string.format('/ja "%s" %s', b.name, b.target or default_target(a.Targets));
        end
    elseif b.kind == 'item' then
        local it = res():GetItemByName(b.name, 0);
        info.item_id = it and it.Id or nil;
        info.disc = 'disc_command';
        info.motif = 'motif_sword';
        info.kind_label = 'Item';
        info.glyph, info.tier = actions.glyph(b.name);
        info.command = string.format('/item "%s" %s', b.name, b.target or '<me>');
    elseif b.kind == 'macro' then
        -- a macro: { kind='macro', ref = id } (xiv1ui's Macros window; the macro itself lives in the settings), or an
        -- inline one { kind='macro', name, lines, icon, show_name } (e.g. imported from FFXI's macro files)
        if b.ref then
            local m = require('ui.win_macros').get(b.ref);
            if m == nil then return nil; end                     -- deleted: the slot shows empty
            local tex = m.icon and (m.icon:match('^ai_') and m.icon or ('mi_' .. m.icon));
            b = { kind = 'macro', name = m.name, lines = m.lines, icon = tex, show_name = m.show_name };
            info.label = m.name;
        end
        info.disc = 'disc_command';
        info.icon = b.icon;
        info.motif = 'motif_wand';
        info.kind_label = 'Macro';
        info.glyph, info.tier = actions.glyph(b.name or '?');
        info.show_name = b.show_name ~= false;
        info.lines = b.lines or {};
        info.usable = #info.lines > 0;
    else -- 'cmd': any text command, e.g. { kind='cmd', name='Attack', command='/attack <t>' }
        info.disc = 'disc_command';
        info.motif = 'motif_sword';
        info.kind_label = 'Command';
        info.glyph, info.tier = actions.glyph(b.name);
        info.icon = ICONS.cmd[b.name];
        info.command = b.command or b.name;
    end
    return info;
end

function actions.use(b)
    local info = actions.resolve(b);
    if info and info.lines then
        if #info.lines == 0 then return false; end
        require('core.macros').run({ lines = info.lines, title_utf8 = info.label });
        return true;
    end
    if info and info.command then
        AshitaCore:GetChatManager():QueueCommand(1, info.command);
        return true;
    end
    return false;
end

--- A starting bar for the current job. all = true: every known action, not just the first ten slots' worth.
function actions.defaults(all)
    local cap = all and 200 or 10;
    local out = {
        { kind = 'cmd', name = 'Attack', command = '/attack <t>' },
        { kind = 'cmd', name = 'Check', command = '/check <t>' },
    };
    local player = mm():GetPlayer();
    local r = res();
    local function add(b) if #out < cap then out[#out + 1] = b; end end
    for id = JA_BASE, JA_BASE + 400 do
        if #out >= cap then break; end
        local a = r:GetAbilityById(id);
        if a and player:HasAbility(id) and a.Name[1] ~= '' then add({ kind = 'ja', name = a.Name[1] }); end
    end
    for id = 1, 255 do
        if #out >= cap then break; end
        local a = r:GetAbilityById(id);
        if a and player:HasWeaponSkill(id) and a.Name[1] ~= '' then add({ kind = 'ws', name = a.Name[1] }); end
    end
    for id = 1, 1024 do
        if #out >= cap then break; end
        local s = r:GetSpellById(id);
        if s and player:HasSpell(s.Index) and s.Name[1] ~= '' then
            local lv = s.LevelRequired and s.LevelRequired[player:GetMainJob() + 1];
            if lv and lv > 0 and lv ~= 255 and lv <= player:GetMainJobLevel() then add({ kind = 'ma', name = s.Name[1] }); end
        end
    end
    return out;
end

local SPELL_CATS = { 'White Magic', 'Black Magic', 'Summoning', 'Ninjutsu', 'Songs', 'Blue Magic', 'Geomancy', 'Trust' };
local ABILITY_CATS = { [6] = 'Blood Pacts', [10] = 'Blood Pacts', [18] = 'Ready', [20] = 'Ready', [2] = 'Pet Commands' };
actions.CATEGORIES = { 'Job Abilities', 'Pet Commands', 'Blood Pacts', 'Ready', 'Weapon Skills', 'White Magic',
                       'Black Magic', 'Summoning', 'Ninjutsu', 'Songs', 'Blue Magic', 'Geomancy', 'Trust' };

--- Everything the character can use now, by category: { [category] = { { kind, name, cost }, ... } } in the game's
-- order. Spells count when the main or support job is high enough for them; traits (passive) are left out.
function actions.learned()
    local player, r = mm():GetPlayer(), res();
    local out = {};
    local function add(cat, b) out[cat] = out[cat] or {}; table.insert(out[cat], b); end
    local seen = {};
    for id = JA_BASE, 2047 do
        local a = r:GetAbilityById(id);
        if a and a.Name and (a.Name[1] or '') ~= '' and a.Type ~= 4 and player:HasAbility(id) and not seen[a.Name[1]] then
            seen[a.Name[1]] = true;
            add(ABILITY_CATS[a.Type] or 'Job Abilities', { kind = 'ja', name = a.Name[1] });
        end
    end
    for id = 1, 255 do
        local a = r:GetAbilityById(id);
        if a and a.Name and (a.Name[1] or '') ~= '' and player:HasWeaponSkill(id) then
            add('Weapon Skills', { kind = 'ws', name = a.Name[1] });
        end
    end
    local mj, ml = player:GetMainJob(), player:GetMainJobLevel();
    local sj, sl = player:GetSubJob(), player:GetSubJobLevel();
    for id = 1, 1023 do
        local sp = r:GetSpellById(id);
        if sp and sp.Name and (sp.Name[1] or '') ~= '' and player:HasSpell(sp.Index) then
            local a = sp.LevelRequired and sp.LevelRequired[mj + 1];
            local b = sp.LevelRequired and sp.LevelRequired[sj + 1];
            local ok = (a and a > 0 and a ~= 255 and a <= ml) or (b and b > 0 and b ~= 255 and b <= sl);
            if ok then add(SPELL_CATS[sp.Type] or 'White Magic', { kind = 'ma', name = sp.Name[1], cost = sp.ManaCost }); end
        end
    end
    return out;
end

-- Action icons named ai_gen_* are a category's emblem, not the action's own: the bar keeps its letters over it.
do
    local resolve = actions.resolve;
    function actions.resolve(b)
        local info = resolve(b);
        if info and info.icon and info.icon:sub(1, 7) == 'ai_gen_' then info.generic = true; end
        return info;
    end
end

return actions;
