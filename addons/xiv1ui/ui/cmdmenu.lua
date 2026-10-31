--[[
* xiv1ui - the game's own menus, presented in xiv1ui's style. The game still runs each menu; xiv1ui reads its rows and
* cursor, hides the game's drawing and draws its own:
*   - the action menu (left click / Enter: Chat, Magic, Abilities, Items ...; Attack etc. in combat) as an FF-style
*     stack of slanted panels beside your character, with a crystal shard on the selected command;
*   - the Commands menu (Status, Equipment, ... Map) as a 1.0-style window below the minimap. The game still runs the menu: Up/Down move, confirm selects, cancel goes
* back, exactly as before. xiv1ui reads the rows and the cursor each frame, hides the game's box and finger, and
* draws its own. (How the menu was found: docs/MODDING-NOTES.md, "The command menu".)
*
* The game draws this menu's labels as pictures, so the label for each row is taken from its help text (the line the
* game shows in the help bar), e.g. "Use magic." -> Magic. Unknown commands show the start of their help text.
--]]

local mem    = require('core.mem');
local draw   = require('core.draw');
local text   = require('core.text');
local layout = require('core.layout');
local xi_now = require('core.now');
local store  = require('core.store');
local native = require('core.native');

local cmd = {};

-- windows handled here (by their 8-character menu names)
-- The action menu (playermo; battlemo in combat): its row objects are a fixed template (10 rows, in a different
-- order), not what the game shows. What it shows is the list of command ids in its class object ([slot] + 0x1C,
-- u16s up to a 0), and the cursor is the window's +0x4C (1-based). Labels come from ACTION_IDS, and ids not in that
-- table are learned from the game's help line the first time the cursor is on them (store.data.action_ids).
local MENUS = {};
local ACTION_MENUS = { playermo = true, battlemo = true };
local ACTION_IDS = { [1] = 'Attack', [3] = 'Disengage', [5] = 'Chat', [7] = 'Abilities', [8] = 'Magic', [9] = 'Items',
                     [10] = 'Check', [11] = 'Check', [18] = 'Switch Target', [19] = 'Trade', [25] = 'Trust',
                     [27] = 'Request' };
local TITLES = {
    menuwind = 'Commands', socialme = 'Commands', commenu = 'Communication', statcom2 = 'Status',
    mgcmenu = 'Magic Spells', cmbmenu = 'Synthesis', abimenu = 'Abilities', prty1 = 'Party', searchma = 'Search',
    region = 'Region Info', map0 = 'Map', mogcont = 'Mog House', mcrmenu = 'Macro', configwi = 'Config',
    mnstorag = 'Show Gear From', iuse = 'Item', itmsort2 = 'Sort', missionm = 'Missions',
    ut_menu = 'Unity', mapv3 = 'Markers', quest00 = 'Quests', shopmain = 'Shop', shopsell = 'Sell?', shopbuy = 'Buy?',
};
-- menus whose buttons have no help text (labelled from ORDER by position only)
local NOHELP = { missionm = true, shopmain = true, shopsell = true, shopbuy = true };
-- help lines for menus whose own are missing or misleading (by slot)
local HELPS = { shopmain = { 'See what the shopkeeper has for sale.', 'Offer your things to the shopkeeper.' },
                shopsell = { 'Sell it.', 'Keep it after all.' }, shopbuy = { 'Buy it.', 'Not today.' } };
-- FFXI's own button labels, in on-screen order (read from the game's menus; several rows share one help text, so
-- labels can't always come from it). Used when the row count matches; otherwise labels come from the help text.
local ORDER = {
    menuwind = { 'Status', 'Equipment', 'Magic', 'Items', 'Synthesis', 'Abilities', 'Party', 'Trade', 'Search',
                 'Linkshell', 'Region Info', 'Map' },
    socialme = { 'Missions', 'Quests', 'Key Items', 'View House', 'Bazaar', 'Macros', 'Config', 'Help Desk',
                 'Current Time', 'Communication', 'Shut Down', 'Log Out' },
    commenu  = { 'Friend List', 'Emote List' },
    statcom2 = { 'Profile', 'Job Levels', 'Master Levels', 'Combat Skills', 'Magic Skills', 'Craft Skills',
                 'Currencies', 'Currencies 2', 'Unity', 'Play Time', 'Merit Points', 'Job Points' },
    mgcmenu  = { 'White Magic', 'Black Magic', 'Songs', 'Ninjutsu', 'Summoning', 'Blue Magic', 'Geomancy', 'Trust' },
    cmbmenu  = { 'Crystal Synthesis', 'History' },
    abimenu  = { 'Job Traits', 'Job Abilities', 'Weapon Skills', 'Ranged Attack', 'Mount', 'Pet Command' },
    prty1    = { 'Seek Party', 'Find Member', 'Request', 'View Requests', 'Autogroup', 'Languages', 'Alarm Type' },
    searchma = { 'Area', 'Name', 'Job', 'Country', 'Race', 'Level', 'Master Level', 'Rank', 'Request', 'Unity',
                 'Friend', 'Linkshell', 'Linkshell 2', 'Ballista', 'Monstrosity', 'Comment', 'Edit Comment' },
    region   = { 'Conquest', 'Besieged', 'Campaign', 'Colonization' },
    map0     = { 'Markers', 'Wide Scan', 'Change Map' },
    mogcont  = { 'Mog Safe', 'Mog Safe 2', 'Storage', 'Mog Locker', 'Mog Satchel', 'Mog Sack', 'Mog Case',
                 'Mog Wardrobe', 'Mog Wardrobe 2', 'Mog Wardrobe 3', 'Mog Wardrobe 4', 'Mog Wardrobe 5',
                 'Mog Wardrobe 6', 'Mog Wardrobe 7', 'Mog Wardrobe 8' },
    mcrmenu  = { 'Edit Macros', 'Edit Equip Sets' },
    iuse     = { 'Use', 'Drop' },
    shopmain = { 'Buy', 'Sell' },
    shopsell = { 'Sell', 'Cancel' },
    shopbuy  = { 'Buy', 'Cancel' },
    ut_menu  = { 'Unity Info', 'Ranking Info', 'Members' },
    itmsort2 = { 'Auto Sort', 'Manual Sort', 'Recycle Bin' },
    missionm = { 'Nations', 'Rise of the Zilart', 'Chains of Promathia', 'Treasures of Aht Urhgan',
                 'Wings of the Goddess', 'Seekers of Adoulin', 'Add-on Scenarios' },
    mnstorag = { 'Inventory', 'Mog Wardrobe', 'Mog Wardrobe 2', 'Mog Wardrobe 3', 'Mog Wardrobe 4', 'Mog Wardrobe 5',
                 'Mog Wardrobe 6', 'Mog Wardrobe 7', 'Mog Wardrobe 8' },
    configwi = { 'Gameplay', 'Chat Filters', 'Font Colors', 'Windows', 'Log', 'Misc.', 'Misc. 2', 'Misc. 3',
                 'Misc. 4', 'Effects', 'Mouse / Camera', 'Global', 'Gamepad' },
};
-- Menus whose rows carry no help text and whose labels are text drawn by the game: labels in the game's order, and
-- the absolute cursor (0-based) and scroll offset read from the menu's class object ([window slot]).
local INDEXED = {
    evitem = { title = 'Key Items', cursor = 0x30, labels = { 'Temporary Key Items', 'Permanent Key Items', 'Abyssea',
               'Voidwatch', 'Geas Fete', 'Mounts', 'Mog Garden', 'Magical Maps', 'Claim Slips', 'Active Effects' } },
};
for name, d in pairs(INDEXED) do TITLES[name] = d.title; end
for name in pairs(TITLES) do MENUS[name] = 'list'; end
for name in pairs(ACTION_MENUS) do MENUS[name] = 'stack'; end
-- the action menu's own sub-menus (their rows are ordinary: labels from the help texts)
for _, name in ipairs({ 'abiselec', 'mgcselec', 'magselec' }) do MENUS[name] = 'stack'; end
-- menus whose first button sits below a heading line: slots to skip
local SLOT_SKIP = { itmsort2 = 1 };
-- the Commands menu's two pages (Left / Right switch between them in the game)
local PAGES = { menuwind = 1, socialme = 2 };

-- help text (start) -> label
local LABELS = {
    { 'Open input window', 'Chat' },        { 'Use magic', 'Magic' },           { 'Use an ability', 'Abilities' },
    { 'Use an item', 'Items' },             { 'Trade with', 'Trade' },          { 'Invite selected', 'Invite' },
    { 'Distribute currently pooled', 'Treasure' }, { 'Examine target', 'Check' }, { 'Estimate target', 'Check' },
    { 'Display a list of Trust', 'Trust' }, { 'Express desire to join', 'Request' }, { 'Dismount and attack', 'Attack' },
    { 'Dismount', 'Dismount' },             { 'Make your chocobo dig', 'Dig' }, { 'Attack', 'Attack' },
    { 'Disengage', 'Disengage' },           { 'Use a weapon skill', 'Weapon Skill' }, { 'Ranged attack', 'Ranged Attack' },
    { 'Assist', 'Assist' },                 { 'Mark map', 'Mark' },
    -- (the action menu's texts in combat, as the game has them)
    { 'Start auto-attack', 'Attack' },      { 'Cancel auto-attack', 'Disengage' }, { 'Call for help', 'Call for Help' },
    { 'Select a target to auto-attack', 'Switch Target' }, { 'Select target to attack with ranged', 'Ranged Attack' },
    { 'Select target to trade with', 'Trade' }, { 'Cast a fishing line', 'Fish' },
    { 'Acquire currently pooled', 'Treasure' }, { 'Chat in', 'Chat' }, { 'Display abilities and skills', 'Abilities' },
    { 'Purchase merchandise', 'Buy' },      { 'Sell merchandise', 'Sell' },
    -- Commands menu
    { 'View status', 'Status' },            { 'Equip weapons', 'Equipment' },   { 'View spell and song', 'Magic' },
    { 'View current inventory', 'Items' },  { 'View job abilities', 'Abilities' }, { 'Organize party', 'Party' },
    { 'Trade items or money', 'Trade' },    { 'Search for other players', 'Search' },
    { 'Set up and equip linkshell', 'Linkshell' }, { 'View the list of synthesis', 'Synthesis' },
    { 'View the balance of power', 'Region Info' }, { 'View map of current', 'Map' },
    -- Commands menu, page 2
    { 'View list of current mission', 'Missions' }, { 'View list of current quests', 'Quests' },
    { 'View list of key items', 'Key Items' }, { 'View contents of Mog House', 'Mog House' },
    { 'Select merchandise from your', 'Bazaar' }, { 'Edit equipment sets', 'Equip Sets' },
    { "Change the game's options", 'Config' }, { 'Search for solutions', 'Help Desk' },
    { 'Display the Friend List', 'Friend List' }, { 'Display current time', 'Vana\'diel Time' },
    -- (the game's help texts for these two read the other way round from their labels)
    { 'Log out from', 'Shut Down' }, { 'Quit FINAL FANTASY', 'Log Out' },
    -- action menu » Abilities
    { 'Activate special abilities', 'Job Abilities' }, { 'Use TP to perform', 'Weapon Skills' },
    { 'Attack current target with ranged', 'Ranged Attack' }, { 'Call forth your mount', 'Mount' },
    { 'Issue command to pet', 'Pet Commands' },
    -- action menu » Magic (Right)
    { 'View list of white magic', 'White Magic' }, { 'View list of black magic', 'Black Magic' },
    { 'View list of bard songs', 'Songs' },  { 'View list of ninjutsu', 'Ninjutsu' },
    { 'View list of summoning', 'Summoning' }, { 'View list of blue magic', 'Blue Magic' },
    { 'View list of geomancy', 'Geomancy' }, { 'View list of Trust', 'Trust' },
    -- Communication
    { "Use the PlayOnline viewer's Friend List", 'Friend List' }, { 'Display the Emote List', 'Emote List' },
};

local focus_ptr = nil;       -- address that holds the focused-menu pointer (Balloon addon's pattern)
local hidden = nil;          -- { obj, b69, b6a, b78 }
local objs = {};
local opened = 0;            -- xi_now() when the menu appeared (slide-in)
local last_obj = nil;

local function label_for(help)
    local best = nil;                        -- the longest matching help-text start wins
    for _, l in ipairs(LABELS) do
        if help:sub(1, #l[1]) == l[1] and (best == nil or #l[1] > #best[1]) then best = l; end
    end
    if best then return best[2]; end
    local words = {};
    for w in help:gmatch('[%a\']+') do words[#words + 1] = w; if #words == 2 then break; end end
    return table.concat(words, ' ');
end

local help_cache = {};
local function help_of(entry)
    local h = help_cache[entry];
    if h == nil then
        local p = mem.u32(entry + 8);
        h = (p and mem.ok(p, 96)) and (ashita.memory.read_string(p, 96) or ''):match('^[^%z]*') or '';
        help_cache[entry] = h;
    end
    return h;
end

local function is_row_of(r, obj) return mem.ok(r, 0x70) and mem.u32(r + 0x58) == r and mem.u32(r + 0x5C) == obj; end

-- All of a window's row objects (buttons, title, arrows): the window keeps them in a linked list at obj+0x14
-- (node +0x00 next, +0x10 -> row). Rows can live in several memory blocks, so this list is the only reliable way.
local function rows_of(obj)
    local out, n = {}, mem.u32(obj + 0x14);
    while n and n ~= 0 and #out < 120 and mem.ok(n, 0x14) do
        local r = mem.u32(n + 0x10);
        if r and is_row_of(r, obj) then out[#out + 1] = r; end
        n = mem.u32(n);
    end
    return out;
end

--- The focused command menu as { obj, rows = { labels }, cursor }, or nil.
-- Windows that are restyled only when opened from somewhere specific: Status » Currencies reuses the Key Items
-- window with other contents (not restyled yet).
-- (opener[name] = the window that had focus just before `name` got it)
local opener, focus_prev = {}, nil;
local function track_focus()
    local _, n = native.focused();
    if n ~= focus_prev then
        if n then opener[n] = focus_prev; end
        focus_prev = n;
    end
end
cmd.opener = opener;
-- The action menu's entries (labels, cursor), or nil while any entry's label is still unknown: then the game draws
-- its own menu, and each entry's label is learned from the help line as the cursor passes over it.
local slots = {};
local function slot_of(name)
    slots[name] = require('core.gamewin').slot(name) or false;
    return slots[name] or nil;
end

-- Learning a label: the help line changes a moment after the cursor moves, so a help line counts for the entry under
-- the cursor only once it has changed since the cursor got there (or, when the menu has just opened, after a short
-- wait). The help text itself is kept (store.data.action_help), so better LABELS apply to entries learned earlier.
local learn = { obj = nil, cursor = nil, help = nil, t = 0 };
local function action_rows(name, obj)
    local slot = slot_of(name);
    local cls = slot and mem.u32(slot);
    local cursor = mem.u32(obj + 0x4C);
    if cls == nil or cursor == nil then return nil; end
    local ids = {};
    for i = 0, 15 do
        local v = mem.u16(cls + 0x1C + i * 2);
        if v == nil or v == 0 then break; end
        ids[#ids + 1] = v;
    end
    -- the list can run on past the menu's end (left over from a longer menu): the window's +0x58 (u16) is the row count
    local count = mem.u16(obj + 0x58);
    if count and count >= 1 and count < #ids then for i = #ids, count + 1, -1 do ids[i] = nil; end end
    if cursor < 1 or cursor > #ids then return nil; end
    local learned = store.data.action_help or {};
    local help = require('ui.listpanel').help_line();
    local cur_id = ids[cursor];
    local now = xi_now();
    if learn.obj ~= obj or learn.cursor ~= cursor then
        -- the cursor moved (or the menu opened): the help line still shows the previous entry for a moment
        learn.help = (learn.obj == obj) and help or nil;
        learn.obj, learn.cursor, learn.t = obj, cursor, now;
    end
    local settled = (learn.help ~= nil and help ~= learn.help) or (learn.help == nil and now - learn.t > 0.3) or now - learn.t > 0.6;
    if help ~= '' and settled and not ACTION_IDS[cur_id] and learned[tostring(cur_id)] ~= help then
        learned[tostring(cur_id)] = help;
        store.data.action_help = learned;
        store.save();
    end
    local rows = {};
    for i, id in ipairs(ids) do
        local h = learned[tostring(id)];
        rows[i] = ACTION_IDS[id] or (h and label_for(h));
        if rows[i] == nil then return nil; end
    end
    return rows, cursor;
end

local function declined(name, obj)
    track_focus();
    if ACTION_MENUS[name] then return obj == nil or action_rows(name, obj) == nil; end
    return name == 'evitem' and opener.evitem == 'statcom2';
end

function cmd.read()
    track_focus();
    if focus_ptr == nil then
        local p = ashita.memory.find('FFXiMain.dll', 0, '8B480C85C974??8B510885D274??3B05', 16, 0);
        focus_ptr = (p and p ~= 0) and p or false;
    end
    if not focus_ptr then return nil; end
    local obj = mem.chain(focus_ptr, 0, 0);
    if obj == nil then return nil; end
    local hdr = mem.u32(obj + 4);
    if hdr == nil or not mem.ok(hdr + 0x46, 16) then return nil; end
    local name = (ashita.memory.read_string(hdr + 0x4E, 8) or ''):gsub('[%z ]+$', '');
    if not MENUS[name] then return nil; end
    if ACTION_MENUS[name] then
        local rows, cursor = action_rows(name, obj);
        if rows == nil then return nil; end
        return { obj = obj, rows = rows, helps = {}, cursor = cursor, name = name, style = 'stack' };
    end
    local ix = INDEXED[name];
    if declined(name) then return nil; end
    if name == 'quest00' then
        -- Commands » Quests: five rows (no help texts); the selected row is the window's +0x08 row object, rows
        -- numbered at +0x3A. The record / currency figures the game prints in this window come from ui/roe.lua.
        local cur, labels = mem.u32(obj + 0x08), { 'Current Quests', 'Completed Quests', 'Records of Eminence',
                                                   'Objective List', "Vana'Bout" };
        local c = nil;
        for _, r in ipairs(rows_of(obj)) do
            if r == cur then c = mem.u16(r + 0x3A); end
        end
        if c == nil or c < 1 or c > 5 then return nil; end
        local sum = require('ui.roe').summary();
        local helps = { 'Quests you are working on.\n' .. sum, 'Quests you have completed.\n' .. sum,
                        'Records of Eminence you have taken on.\n' .. sum,
                        'Choose new Records of Eminence to take on.\n' .. sum, "Vana'Bout.\n" .. sum };
        return { obj = obj, rows = labels, helps = helps, cursor = c, name = name, style = 'list' };
    end
    if name == 'mapv3' then
        -- Map » Markers: ten marker slots. Each row's label is a text object the class points to (+0x18, one per
        -- row; the text buffer at [+4]); empty slots have no text. Left / Right switch the marker colour.
        local slot = slot_of(name);
        local cls = slot and mem.u32(slot);
        local c = mem.u32(obj + 0x4C);
        if cls == nil or c == nil or c < 1 or c > 10 then return nil; end
        local rows = {};
        for r = 0, 9 do
            local t = mem.u32(cls + 0x18 + r * 4);
            local buf = t and mem.u32(t + 4);
            local txt = (buf and mem.ok(buf, 4)) and (ashita.memory.read_string(buf, 32) or ''):match('^[^%z]*') or '';
            rows[r + 1] = (txt ~= '' and txt:match('^[%w%p ]+$')) and txt or '(empty)';
        end
        local helps = {};
        for i = 1, 10 do helps[i] = 'Left / Right: marker colour.  Confirm: show this marker on the map.'; end
        return { obj = obj, rows = rows, helps = helps, cursor = c, name = name, style = 'list' };
    end
    if ix then
        local slot = slot_of(name);
        local cls = slot and mem.u32(slot);
        local c = cls and mem.u8(cls + ix.cursor);
        if c == nil or c >= #ix.labels then return nil; end
        return { obj = obj, rows = ix.labels, helps = {}, cursor = c + 1, name = name, style = 'list' };
    end
    local cursor, cur = mem.u32(obj + 0x4C), mem.u32(obj + 0x08);
    if not cursor or cursor < 1 or cursor > 64 or not cur then return nil; end
    -- Row objects: 0x70 apart, +0x58 -> itself, +0x5C -> the window, +0x0C -> table entry (help text at entry+8),
    -- +0x2C on-screen y, +0x3A row number. Memory order isn't screen order, a menu's window can be followed by its
    -- decorations (no help text) and by stale rows from an earlier opening, so: real rows only, one per row number,
    -- sorted by y.
    if not is_row_of(cur, obj) then return nil; end
    local fy1, fy2 = mem.u16(obj + 0x3C) or 0, mem.u16(obj + 0x40) or 0;
    local list, seen = {}, {};
    for _, r in ipairs(rows_of(obj)) do
        local entry = mem.u32(r + 0x0C);
        local h = entry and help_of(entry) or '';
        local n = mem.u16(r + 0x3A);
        local ry = mem.u16(r + 0x2C) or -1;
        if (h ~= '' or NOHELP[name]) and n and not seen[n] and ry > fy1 and ry <= fy2 then
            seen[n] = true;
            list[#list + 1] = { y = ry, label = label_for(h), help = h, sel = (r == cur) };
        end
    end
    table.sort(list, function (a, b) return a.y < b.y; end);
    local rows, helps = {}, {};
    -- known menus: the label for the button at that slot (buttons are 16 px apart, the first 6 px below the frame top)
    local order = ORDER[name];
    if order then
        -- by slot; slots without a row object (e.g. Search » Master Level) still get their label
        local last = 0;
        for _, it in ipairs(list) do
            local slot = math.floor((it.y - fy1 - 6) / 16 + 0.5) + 1 - (SLOT_SKIP[name] or 0);
            rows[slot], helps[slot] = order[slot] or it.label, (HELPS[name] and HELPS[name][slot]) or it.help;
            if it.sel then cursor = slot; end
            if slot > last then last = slot; end
        end
        for i = 1, last do
            if rows[i] == nil then rows[i], helps[i] = order[i] or '', ''; end
        end
    else
        for i, it in ipairs(list) do
            rows[i], helps[i] = it.label, it.help;
            if it.sel then cursor = i; end
        end
    end
    if #rows == 0 then return nil; end
    return { obj = obj, rows = rows, helps = helps, cursor = cursor, name = name, style = MENUS[name], page = PAGES[name] };
end

-- Hiding the game's drawing of a menu: the window's visibility bytes (+0x69/+0x6A: frame) and finger (+0x78), and
-- every row object's scale (+0x1C/+0x20, two floats of 1.0) set to 0. Row objects are the buttons and also the
-- title / arrow decorations. Clearing other bytes of a row object (e.g. its first) crashed the client: don't.
local ffi = require('ffi');
local shown_obj = {};        -- obj -> { b69, b6a, b78, name }: window bytes we cleared
local zeroed = {};           -- row -> obj: rows whose scale we set to 0

local function hide_menu(obj, name)
    -- a window object reused by a sub-menu: same object, new name (the bytes we saved still apply)
    if shown_obj[obj] and shown_obj[obj][4] ~= name then shown_obj[obj][4] = name; end
    if not shown_obj[obj] then
        local a, b, f = mem.u8(obj + 0x69), mem.u8(obj + 0x6A), mem.u8(obj + 0x78);
        if a == nil or a > 1 or b == nil or b > 1 or f == nil or f > 1 then return false; end
        shown_obj[obj] = { a, b, f, name };
        mem.w8(obj + 0x69, 0); mem.w8(obj + 0x6A, 0); mem.w8(obj + 0x78, 0);
    end
    for _, r in ipairs(rows_of(obj)) do
        -- (row objects are reused between menus, so a row hidden for an earlier menu counts as new here)
        local sc = ffi.cast('float*', r + 0x1C);
        if zeroed[r] ~= obj then
            if sc[0] == 1 and sc[1] == 1 then sc[0], sc[1] = 0, 0; zeroed[r] = obj; end
        elseif sc[0] ~= 0 or sc[1] ~= 0 then
            sc[0], sc[1] = 0, 0;      -- the game re-animated it (cursor moved): hide it again
        end
    end
    return true;
end

-- Is a hidden menu still the same live window (its rows still point back at it, and it still has the same name)?
local function alive(obj)
    local w = shown_obj[obj];
    if w == nil then return false; end
    local hdr = mem.u32(obj + 4);
    local name = (hdr and mem.ok(hdr + 0x4E, 8)) and (ashita.memory.read_string(hdr + 0x4E, 8) or ''):gsub('[%z ]+$', '') or '';
    return name == w[4] and #rows_of(obj) > 0;
end

local function restore_menu(obj)
    local w = shown_obj[obj];
    for r, o in pairs(zeroed) do
        if o == obj then
            if is_row_of(r, obj) then
                local sc = ffi.cast('float*', r + 0x1C);
                if sc[0] == 0 and sc[1] == 0 then sc[0], sc[1] = 1, 1; end
            end
            zeroed[r] = nil;
        end
    end
    if w and alive(obj) then
        if mem.u8(obj + 0x69) == 0 then mem.w8(obj + 0x69, w[1]); end
        if mem.u8(obj + 0x6A) == 0 then mem.w8(obj + 0x6A, w[2]); end
        if mem.u8(obj + 0x78) == 0 then mem.w8(obj + 0x78, w[3]); end
    end
    shown_obj[obj] = nil;
end

local function restore_all()
    for obj in pairs(shown_obj) do restore_menu(obj); end
    -- rows of menus whose window is already gone: put their scale back if they still look like that menu's rows
    for r, o in pairs(zeroed) do
        if is_row_of(r, o) then
            local sc = ffi.cast('float*', r + 0x1C);
            if sc[0] == 0 and sc[1] == 0 then sc[0], sc[1] = 1, 1; end
        end
        zeroed[r] = nil;
    end
end

local function unhide() restore_all(); end




-- The Commands menu: a 1.0 window (title, rows, selected row lit, gold cursor) below the minimap.
local ui = require('core.ui');
local LIST_W, ROW_H = 250, 27;
local function render_list(m, now, depth, dim)
    local h = dim and 40 or (46 + #m.rows * ROW_H + 12);     -- a parent under a sub-menu shows its title only
    -- to the left of the minimap, so neither covers the other
    -- sub-menus stack straight down under their parent's title strip, aligned with it (a parent shows its title only)
    local x, y = layout.anchor('topright', LIST_W, h, -250, 50 + depth * 42, 'commands');
    if depth == 0 then layout.bounds('commands', x, y, LIST_W, h); end
    local t = math.max(0, math.min(1, (now - (m.opened or opened)) / 0.15)) * (dim and 0.55 or 1);
    local col = draw.alpha(0xFFFFFFFF, t);
    local bw, bh = layout.size('win_body');
    draw.nine('win_body', x, y, LIST_W, h, 12, bw, bh, col);
    local tw, th = layout.size('win_title');
    draw.nine('win_title', x + 4, y + 4, LIST_W - 8, 30, 10, tw, th, col);
    draw.image('title_swash', x + 8, y + 4, { color = col });
    local title = ui.label('cmdlist_title' .. depth, 'name', { font_height = 22 });
    title:set_opacity(t);
    text.draw(title, TITLES[m.name] or '', x + 40, y + 27, 'baseline');
    -- page arrows: Left / Right switch pages in the game
    if m.page then
        local pg = ui.label('cmdlist_page' .. depth, 'slotkey', { font_height = 15, font_alignment = text.align.Center });
        pg:set_opacity(t);
        text.draw(pg, string.format('%d/2', m.page), x + LIST_W - 46, y + 25, 'baseline');
        draw.image('dlg_arrow', x + LIST_W - 74, y + 12, { rot = -math.pi / 2, color = col });    -- pointing left
        draw.image('dlg_arrow', x + LIST_W - 30, y + 12, { rot = math.pi / 2, color = col });     -- pointing right
    end
    local sw, sh = layout.size('row_sel');
    for i, label in ipairs(dim and {} or m.rows) do
        local ry = y + 44 + (i - 1) * ROW_H;
        local sel = (i == m.cursor);
        if sel then
            draw.nine('row_sel', x + 22, ry, LIST_W - 34, ROW_H - 4, 6, sw, sh, col);
            if not dim then draw.image('cursor_gold', x + 2, ry + 2, { color = col }); end
        end
        local o = ui.label('cmdlist_row' .. depth .. '_' .. i, 'small', { font_height = 19 });
        o:set_font_color(sel and 0xFFFFFFFF or 0xFFD8D4C8);
        o:set_opacity(t);
        text.draw(o, label, x + 34, ry + ROW_H - 9, 'baseline');
    end
    return x, y + h, t;
end

-- The selected row's help line, in a box joined to the bottom of the menu (in place of the game's help bar).
local help_obj = nil;
local function render_help(help, x, y, w, t)
    if help == nil or help == '' then return; end
    help_obj = help_obj or text.new('small', { font_height = 17, font_color = 0xFFE8E4D8, box_width = w - 28 });
    if help_obj.settings.text ~= help then text.set(help_obj, help); end
    local _, th = text.size(help_obj);
    local h = th + 18;
    local bw, bh = layout.size('win_hud');
    draw.nine('win_hud', x, y - 2, w, h, 10, bw, bh, draw.alpha(0xFFFFFFFF, t));
    help_obj:set_opacity(t);
    text.render(help_obj, x + 14, y + 6);
end

-- The game's help bar (window "menu    helpwind") and its title tab ("menu    titlewin") are hidden while one of
-- our menus is up.
local titletab = { slot = nil, obj = nil, orig = nil };
local function titletab_hide(on)
    titletab.slot = require('core.gamewin').slot('titlewin') or false;
    if not titletab.slot then return; end
    local obj = mem.chain(titletab.slot, 0, 8);
    if on and obj then
        if titletab.obj ~= obj then
            local a, b = mem.u8(obj + 0x69), mem.u8(obj + 0x6A);
            if not (a and a <= 1 and b and b <= 1) then return; end
            titletab.obj, titletab.orig = obj, { a, b };
        end
        if mem.u8(obj + 0x69) ~= 0 then mem.w8(obj + 0x69, 0); end
        if mem.u8(obj + 0x6A) ~= 0 then mem.w8(obj + 0x6A, 0); end
    elseif not on and titletab.obj then
        -- (only while a game menu is still open: with none, the game has hidden the tab itself meanwhile, and
        -- writing our saved 'visible' back would leave an empty tab on screen)
        if obj == titletab.obj and native.focused() ~= nil then
            if mem.u8(obj + 0x69) == 0 then mem.w8(obj + 0x69, titletab.orig[1]); end
            if mem.u8(obj + 0x6A) == 0 then mem.w8(obj + 0x6A, titletab.orig[2]); end
        end
        titletab.obj = nil;
    end
end
local helpbar = { slot = nil, obj = nil, orig = nil, rows = {} };
local function helpbar_hide(on)
    titletab_hide(on);
    helpbar.slot = require('core.gamewin').slot('helpwind') or false;
    if not helpbar.slot then return; end
    local obj = mem.chain(helpbar.slot, 0, 8);
    -- its title tab and text are row objects of the help window: scale them to 0 as well
    if on and obj then
        for _, r in ipairs(rows_of(obj)) do
            local sc = ffi.cast('float*', r + 0x1C);
            if sc[0] == 1 and sc[1] == 1 then sc[0], sc[1] = 0, 0; helpbar.rows[r] = obj; end
        end
    elseif not on then
        for r, o in pairs(helpbar.rows) do
            if is_row_of(r, o) then
                local sc = ffi.cast('float*', r + 0x1C);
                if sc[0] == 0 and sc[1] == 0 then sc[0], sc[1] = 1, 1; end
            end
        end
        helpbar.rows = {};
    end
    if on then
        if obj and helpbar.obj ~= obj then
            local a, b = mem.u8(obj + 0x69), mem.u8(obj + 0x6A);
            if a and a <= 1 and b and b <= 1 then
                helpbar.obj, helpbar.orig = obj, { a, b };
                mem.w8(obj + 0x69, 0); mem.w8(obj + 0x6A, 0);
            end
        elseif obj and helpbar.obj == obj then
            if mem.u8(obj + 0x69) ~= 0 then mem.w8(obj + 0x69, 0); end
            if mem.u8(obj + 0x6A) ~= 0 then mem.w8(obj + 0x6A, 0); end
        end
    elseif helpbar.obj then
        if obj == helpbar.obj and native.focused() ~= nil then
            if mem.u8(obj + 0x69) == 0 then mem.w8(obj + 0x69, helpbar.orig[1]); end
            if mem.u8(obj + 0x6A) == 0 then mem.w8(obj + 0x6A, helpbar.orig[2]); end
        end
        helpbar.obj = nil;
    end
end

function cmd.release() restore_all(); helpbar_hide(false); end

--- Called at the start of each frame's first scene (before the game draws its UI): a menu that just opened is hidden
-- here already, so its own drawing never shows for a frame. Full reading and drawing still happen in render().
-- (runs at every scene start, ~8 per frame: the game creates menus partway through its frame)
local early_obj = nil;
function cmd.early()
    if store.data.cmd_menu == false then return; end
    -- rows the game re-animated (its cursor moved) since the last frame: hidden again before it draws them
    for r, o in pairs(zeroed) do
        local sc = ffi.cast('float*', r + 0x1C);
        if is_row_of(r, o) and (sc[0] ~= 0 or sc[1] ~= 0) then sc[0], sc[1] = 0, 0; end
    end
    if focus_ptr == nil then
        local p = ashita.memory.find('FFXiMain.dll', 0, '8B480C85C974??8B510885D274??3B05', 16, 0);
        focus_ptr = (p and p ~= 0) and p or false;
    end
    if focus_ptr == false then return; end
    local obj = mem.chain(focus_ptr, 0, 0);
    if obj == nil or obj == early_obj and shown_obj[obj] then return; end
    early_obj = obj;
    if shown_obj[obj] then return; end
    local hdr = mem.u32(obj + 4);
    if hdr == nil or not mem.ok(hdr + 0x4E, 8) then return; end
    local name = (ashita.memory.read_string(hdr + 0x4E, 8) or ''):gsub('[%z ]+$', '');
    if MENUS[name] and not declined(name, obj) then hide_menu(obj, name); helpbar_hide(true); cmd.first_seen.early = cmd.first_seen.early + 1; end
end
cmd.first_seen = { early = 0, late = 0 };     -- which hook saw new menus first (diagnostics)

-- The action menu (or a sub-menu) as a ring: compact slanted panels whose left ends ride on an arc around a point
-- left of them, like a wheel turned so the selected entry is always level, at the same spot beside the character.
-- The wheel turns smoothly as the cursor moves; entries further round the arc fade out.
local RING_R, RING_STEP, PANEL_H = 250, 0.165, 34;
local PANEL_ART_W, PANEL_ART_H = 323, 54;
local ring = { name = nil, pos = 1, t = 0 };
local stack_objs = {};

--- The ring's anchor: where the selected entry's panel starts (left end, vertical middle).
local function ring_anchor()
    return layout.anchor('center', 0, 0, 200, -40, 'cmdmenu');
end

-- Label widths, measured once per label with one text object per font (the panels' width follows the longest).
local measure = {};
local function width_of(label, font_h)
    local c = measure[font_h];
    if c == nil then c = { obj = text.new('name', { font_height = font_h }), w = {} }; measure[font_h] = c; end
    local w = c.w[label];
    if w == nil then
        text.set(c.obj, label);
        w = text.size(c.obj);
        c.w[label] = w;
    end
    return w;
end

local desc_obj = nil;

-- The last moment a restyled menu, a list opened from the action menu, or a target choice was up.
local busy_t = 0;
local GRACE = 0.5;
function cmd.mark_busy() busy_t = xi_now(); end

--- True for a moment after the action menu or a list opened from it lost focus to nothing (the game may be about
-- to reopen it): screens keep the game's windows hidden meanwhile instead of handing them back for a frame or two.
function cmd.grace()
    local _, n = native.focused();
    return n == nil and xi_now() - busy_t < GRACE;
end

--- Is the game waiting for a target (its target cursor up after a command that needs one)?
function cmd.choosing()
    local ok, v = pcall(function () return AshitaCore:GetMemoryManager():GetTarget():GetIsSubTargetActive(); end);
    return ok and v == 1;
end

--- Draw a ring of entries (the action menu, its sub-menus, and the lists opened from it).
-- key names this ring (the wheel's turn is kept per key); items = { { label, sub = right-hand text, icon = item id,
-- dim = greyed } ... }; cursor = the selected index (or nil); opened_t = when it appeared; dim = the whole ring is
-- waiting (target choice); desc = text for a box beside the selected entry. Returns the anchor x, y and panel width.
function cmd.ring(key, items, cursor, opened_t, dim, desc)
    local now = xi_now();
    local n = #items;
    local px, py = ring_anchor();
    local cx = px - RING_R;
    local cur = cursor or 1;
    if ring.name ~= key then ring.name, ring.pos = key, cur; end
    local dt = math.min(0.1, math.max(0, now - ring.t));
    ring.t = now;
    ring.pos = ring.pos + (cur - ring.pos) * math.min(1, dt * 16);
    local wl, ws, icon = 0, 0, false;
    for _, it in ipairs(items) do
        wl = math.max(wl, width_of(it.label, 22));
        if it.sub then ws = math.max(ws, width_of(it.sub, 16)); end
        if it.icon then icon = true; end
    end
    local lx = icon and 56 or 24;                       -- label start within the panel
    local pw = lx + wl + (ws > 0 and ws + 18 or 0) + 30;
    local scale = { pw / PANEL_ART_W, PANEL_H / PANEL_ART_H };
    layout.bounds('cmdmenu', px - 40, py - 120, pw + 50, 240);
    local order = {};
    for i = 1, n do
        if math.abs((i - ring.pos) * RING_STEP) < 1.25 then order[#order + 1] = i; end
    end
    table.sort(order, function (a, b) return math.abs(a - ring.pos) > math.abs(b - ring.pos); end);
    for _, i in ipairs(order) do
        local it = items[i];
        local th = (i - ring.pos) * RING_STEP;
        local t = math.max(0, math.min(1, (now - (opened_t or opened) - math.min(8, math.abs(i - cur)) * 0.025) / 0.16));
        local ease = 1 - (1 - t) ^ 3;
        local x = cx + RING_R * math.cos(th) + (1 - ease) * 40;
        local y = py + RING_R * math.sin(th) - PANEL_H / 2;
        local sel = (i == cursor);
        local fade = sel and 1 or math.max(0.2, 1 - math.abs(th) / 1.25);
        local a = ease * fade * (dim and 0.45 or 1);
        local col = draw.alpha(0xFFFFFFFF, a);
        draw.image(sel and 'cmd_panel_sel' or 'cmd_panel', x, y, { color = col, scale = scale });
        if sel and not dim then
            local bob = math.sin(now * 3) * 2;
            draw.image('crystal_shard', x - 26, y - 3 + bob, { color = col, scale = 0.8 });
        end
        if it.icon then draw.entry(draw.item_icon(it.icon), x + 22, y + 3, 28, 28, col); end
        -- text objects by place in the ring (a long list doesn't make one per entry)
        local slot = key .. ':' .. (i - math.floor(ring.pos + 0.5));
        local o = stack_objs[slot];
        if o == nil then
            o = { text.new('name', { font_height = 22, font_color = 0xFFFFFFFF }),
                  text.new('label', { font_height = 19, font_color = 0xFFE8E4D8 }),
                  text.new('small', { font_height = 16, font_color = 0xFFC8C4B8, font_alignment = text.align.Right }) };
            stack_objs[slot] = o;
        end
        local t_obj = sel and o[1] or o[2];
        local tc = it.dim and 0xFF9098A0 or (sel and 0xFFFFFFFF or 0xFFE8E4D8);
        if t_obj.settings.font_color ~= tc then t_obj:set_font_color(tc); end
        t_obj:set_opacity(a);
        text.draw(t_obj, it.label, x + lx, y + PANEL_H / 2 + 6, 'baseline');
        if it.sub then
            o[3]:set_opacity(a);
            text.draw(o[3], it.sub, x + pw - 26, y + PANEL_H / 2 + 6, 'baseline');
        end
    end
    if dim then
        -- waiting for a target: say what the keys do now
        local hx, hy = px + pw + 16, py - 19;
        local bw, bh = layout.size('win_hud');
        draw.nine('win_hud', hx, hy, 300, 60, 10, bw, bh);
        local h1 = ui.label('cmd_target_hint', 'label', { font_height = 19, font_color = 0xFFF0E6C8 });
        text.draw(h1, 'Choose a target', hx + 14, hy + 24, 'baseline');
        local h2 = ui.label('cmd_target_hint2', 'small', { font_height = 16, font_color = 0xFFC8C4B8 });
        text.draw(h2, 'Enter / A confirms,  Esc / B back', hx + 14, hy + 48, 'baseline');
    elseif desc and desc ~= '' then
        local bw, bh = layout.size('win_hud');
        local dx, dy = px + pw + 16, py - PANEL_H / 2;
        desc_obj = desc_obj or text.new('small', { font_height = 16, font_color = 0xFFE8E4D8, box_width = 300 });
        if desc_obj.settings.text ~= desc then text.set(desc_obj, desc); end
        local _, th = text.size(desc_obj);
        draw.nine('win_hud', dx, dy, 326, th + 20, 10, bw, bh);
        text.render(desc_obj, dx + 13, dy + 9);
    end
    return px, py, pw;
end

local function render_stack(m, now, back, dim)
    local items = {};
    for i, label in ipairs(m.rows) do items[i] = { label = label }; end
    return cmd.ring(m.name, items, m.cursor, m.opened, dim);
end

-- Game windows opened from the action menu that xiv1ui draws in the menu's place (anything else, e.g. after Check,
-- means the action menu has closed)
local CHILDREN = { ability = true, magic = true, inventor = true, iuse = true, itmsort2 = true, iteminfo = true };

--- Where the action menu stands (top-left, HUD units) while a list opened from it is up, else nil.
local function focused_name() local _, n = native.focused(); return n or ''; end
local action_rows_n = nil;   -- rows of the action menu while it or a list opened from it is up
function cmd.action_spot()
    if action_rows_n == nil then return nil; end
    local px, py = ring_anchor();
    return px - 30, py - 150;
end

-- When a fight ends the game closes its action menu but leaves a list opened from it (Items, spells, abilities)
-- open, so it would stay up with nothing to fight: xiv1ui closes it (Esc for the game, at most three times: a
-- list inside a sub-menu takes two).
local from_battle = false;
local was_engaged, closing = false, nil;
local function close_after_battle(m)
    local e = AshitaCore:GetMemoryManager():GetEntity();
    local me = AshitaCore:GetMemoryManager():GetParty():GetMemberTargetIndex(0);
    local engaged = me ~= nil and e:GetStatus(me) == 1;
    local now = xi_now();
    -- (in a fight the action menu is still 'playermo'; what matters is being engaged while it was open)
    if m and ACTION_MENUS[m.name] then from_battle = engaged; end
    -- a list or a sub-menu (spell types, ability types) of the battle menu still up
    local left = (m == nil and CHILDREN[focused_name()]) or (m ~= nil and m.style == 'stack' and not ACTION_MENUS[m.name]);
    if was_engaged and not engaged and from_battle and left then
        closing = { t = now + 0.2, n = 0 };
    end
    was_engaged = engaged;
    if closing then
        if engaged or not left or closing.n >= 3 then
            closing = nil;
        elseif now >= closing.t then
            require('ui.gamein').press(0x01);
            closing.n, closing.t = closing.n + 1, now + 0.4;
        end
    end
end

local cache = {};             -- obj -> last read of that menu
cmd.last_choice = {};         -- menu name -> label of its selected row (which list a sub-screen shows)
local stack = {};             -- snapshots of the restyled menus under the focused one (drawn as title strips)
local last_m = nil;           -- the focused menu at the previous frame

function cmd.render()
    if store.data.cmd_menu == false then unhide(); helpbar_hide(false); return; end
    local m = cmd.read();
    -- (while the game waits for a target nothing has focus, but the action menu and its lists are still open; and
    -- for a moment after a command is confirmed nothing has focus either, before the game reopens its list, e.g. when
    -- the target is out of range: that moment counts as still open, or the help bar would flash)
    local waiting = m == nil and (cmd.choosing() or cmd.grace());
    if m == nil and not CHILDREN[focused_name()] and not waiting then action_rows_n = nil; end
    if m then
        action_rows_n = (m.style == 'stack') and #m.rows or nil;
    end
    close_after_battle(m);
    if action_rows_n and ((m and m.style == 'stack') or CHILDREN[focused_name()] or (m == nil and cmd.choosing())) then
        cmd.mark_busy();
    end
    if m == nil then
        -- A menu xiv1ui doesn't restyle (e.g. Linkshell's) opened on top of one it does: keep the parent restyled
        -- and let the game draw the child. With no restyled menu left open, the game draws everything itself.
        local now, depth = xi_now(), 0;
        local live = false;
        for obj in pairs(shown_obj) do
            if alive(obj) then live = true; else restore_menu(obj); end
        end
        if live and last_m and last_m.style == 'list' then
            for _, p in ipairs(stack) do render_list(p, now, depth, true); depth = depth + 1; end
            render_list(last_m, now, depth, false);
        elseif live and last_m and last_m.style == 'stack' and (CHILDREN[focused_name()] or waiting) then
            -- a list opened from the action menu (spells, abilities, items): it takes the menu's place (drawn by
            -- ui/listpanel.lua / ui/itempanel.lua); the action menu stays hidden underneath
        else
            stack, last_m = {}, nil;
            if next(zeroed) then restore_all(); end
            helpbar_hide(false);
        end
        last_obj = nil;
        return;
    end
    local now = xi_now();
    if m.obj ~= last_obj then opened, last_obj = now, m.obj; end
    m.opened = (cache[m.obj] and cache[m.obj].name == m.name and cache[m.obj].opened) or opened;
    if not shown_obj[m.obj] then cmd.first_seen.late = cmd.first_seen.late + 1; end
    if not hide_menu(m.obj, m.name) then return; end
    cache[m.obj] = m;
    cmd.last_choice[m.name] = m.rows[m.cursor];
    cmd.last_menu = m.name;

    -- navigation: opening a sub-menu pushes the previous menu; returning to a menu pops back down to it
    if last_m and last_m.name ~= m.name then
        local found = nil;
        for i, p in ipairs(stack) do if p.name == m.name then found = i; end end
        if found then
            for i = #stack, found, -1 do stack[i] = nil; end
        elseif PAGES[last_m.name] and PAGES[m.name] then
            -- switching Commands pages: the new page replaces the old one, it isn't a sub-menu
        elseif last_m.style == m.style then
            stack[#stack + 1] = last_m;
        end
    end
    -- a Commands page is always the bottom of the stack (nothing can be left over under it)
    if PAGES[m.name] then stack = {}; end
    last_m = m;
    local depth = 0;
    if m.style == 'list' then
        for _, p in ipairs(stack) do render_list(p, now, depth, true); depth = depth + 1; end
    end
    -- restyled windows no longer open (or no longer this menu) get their own drawing back
    for obj in pairs(shown_obj) do
        if obj ~= m.obj and not alive(obj) then restore_menu(obj); end
    end

    helpbar_hide(true);
    if m.style == 'list' then
        local hx, hy, t = render_list(m, now, depth, false);
        render_help(m.helps[m.cursor], hx, hy, LIST_W, t);
        return;
    end
    -- action menu and its sub-menus: a sub-menu takes its parent's place. After a command that needs a target
    -- (Check, Magic ...) the game waits for one (its target cursor is up): the menu is dimmed as the game greys its
    -- own, and a hint says what the keys do now.
    render_stack(m, now, 0, cmd.choosing());
end

return cmd;
