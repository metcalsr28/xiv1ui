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
-- table are learned from the game's help line the first time the cursor is on them (store.data.action_ids); until
-- then such an entry shows as "…" (the menu stays xiv1ui's).
local MENUS = {};
local ACTION_MENUS = { playermo = true, battlemo = true };
local ACTION_IDS = { [1] = 'Attack', [3] = 'Disengage', [5] = 'Chat', [7] = 'Abilities', [8] = 'Magic', [9] = 'Items',
                     [10] = 'Check', [11] = 'Check', [12] = 'Treasure', [18] = 'Switch Target', [19] = 'Trade',
                     [25] = 'Trust', [27] = 'Request' };
local TITLES = {
    menuwind = 'Commands', socialme = 'Commands', commenu = 'Communication', statcom2 = 'Status',
    mgcmenu = 'Magic Spells', cmbmenu = 'Synthesis', abimenu = 'Abilities', prty1 = 'Party', searchma = 'Search',
    region = 'Region Info', map0 = 'Map', mogcont = 'Mog House', mcrmenu = 'Macro', configwi = 'Config',
    mnstorag = 'Show Gear From', iuse = 'Item', itmsort2 = 'Sort', missionm = 'Missions',
    ut_menu = 'Unity', mapv3 = 'Markers', quest00 = 'Quests', shopmain = 'Shop', shopsell = 'Sell?', shopbuy = 'Buy?',
    faqsub = 'Help Desk', link1 = 'Linkshell', maplist = 'Change Map', bazaar = 'Bazaar',
    evitem01 = 'Examine?', scanlist = 'Wide Scan', mount = 'Mount',
    myroom = 'Moogle', storage = 'Storage', mapv2 = 'Marker', flistmai = 'Friend List', searchjo = 'Search: Job', searchna = 'Search: Country', searchra = 'Search: Race',
    searchle = 'Search: Rank', comgenre = 'Comment',
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
    mapv2    = { 'Mark', 'Markers', 'Change Name' },
    mogcont  = { 'Mog Safe', 'Mog Safe 2', 'Storage', 'Mog Locker', 'Mog Satchel', 'Mog Sack', 'Mog Case',
                 'Mog Wardrobe', 'Mog Wardrobe 2', 'Mog Wardrobe 3', 'Mog Wardrobe 4', 'Mog Wardrobe 5',
                 'Mog Wardrobe 6', 'Mog Wardrobe 7', 'Mog Wardrobe 8' },
    mcrmenu  = { 'Edit Macros', 'Edit Equip Sets' },
    storage  = { 'Mog Safe', 'Mog Safe 2', 'Storage', 'Mog Locker', 'Mog Satchel', 'Mog Sack', 'Mog Case',
                 'Mog Wardrobe', 'Mog Wardrobe 2', 'Mog Wardrobe 3', 'Mog Wardrobe 4', 'Mog Wardrobe 5',
                 'Mog Wardrobe 6', 'Mog Wardrobe 7', 'Mog Wardrobe 8' },
    iuse     = { 'Use', 'Drop' },
    shopmain = { 'Buy', 'Sell' },
    shopsell = { 'Sell', 'Cancel' },
    shopbuy  = { 'Buy', 'Cancel' },
    bazaar   = { 'Set Prices', 'Edit Comment' },
    flistmai = { 'Friends', 'Messages', 'Online Status' },
    myroom   = { 'Storage', 'Delivery Box', 'Change Jobs', 'Gardening', 'Layout', 'Open Mog House', 'Remodel' },
    searchjo = { 'Warrior', 'Monk', 'White Mage', 'Black Mage', 'Red Mage', 'Thief', 'Paladin', 'Dark Knight',
                 'Beastmaster', 'Bard', 'Ranger', 'Samurai', 'Ninja', 'Dragoon', 'Summoner', 'Blue Mage', 'Corsair',
                 'Puppetmaster', 'Dancer', 'Scholar', 'Geomancer', 'Rune Fencer' },
    searchna = { "San d'Oria", 'Bastok', 'Windurst' },
    searchra = { 'Hume', 'Elvaan', 'Tarutaru', 'Mithra', 'Galka' },
    searchle = { 'Rank 1', 'Rank 2', 'Rank 3', 'Rank 4', 'Rank 5', 'Rank 6', 'Rank 7', 'Rank 8', 'Rank 9', 'Rank 10' },
    comgenre = { 'EXP Party', 'Battle Content', 'Missions & Quests', 'Item', 'Linkshell', 'Looking for Friends',
                 'Others' },
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
    -- Linkshell » (a linkshell)
    { 'Give a name to your linkshell', 'Name Linkshell' }, { 'Dispose of this', 'Drop' },
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
    local out, n, steps = {}, mem.u32(obj + 0x14), 0;
    -- (steps bound the walk: while the game rebuilds a window, e.g. zoning, the list can loop back on itself)
    while n and n ~= 0 and #out < 120 and steps < 400 and mem.ok(n, 0x14) do
        steps = steps + 1;
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
        rows[i] = ACTION_IDS[id] or (h and label_for(h)) or '\u{2026}';
    end
    return rows, cursor;
end

local function declined(name, obj)
    track_focus();
    if ACTION_MENUS[name] then return obj == nil or action_rows(name, obj) == nil; end
    if name == 'evitem' then
        if opener.evitem == 'statcom2' then return true; end
        -- Key Items: the same window shows the categories (class +0x90 = 1) and, once one is chosen, that category's
        -- key items (+0x90 = 2), which xiv1ui doesn't draw yet: the game draws the list
        local slot = slot_of(name);
        local cls = slot and mem.u32(slot);
        if cls and mem.u32(cls + 0x90) ~= 1 then return true; end
    end
    return false;
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
    if name == 'maplist' then
        -- Map » Change Map: the areas you hold maps for. The class object ([slot]) points (+0x38) at the entries,
        -- 0x54 apart until one with no flags (+0x00): name text at +0x28, then the number of maps (+0x2C; the
        -- current area's entry has text there instead; shown at the row's right), help text at +0x4C. The cursor is the visible row (+0x24,
        -- 1-based) plus the scroll offset (+0x1A).
        local slot = slot_of(name);
        local cls = slot and mem.u32(slot);
        local base = cls and mem.u32(cls + 0x38);
        local vis, top = cls and mem.u16(cls + 0x24), cls and mem.u16(cls + 0x1A);
        if base == nil or vis == nil or top == nil or not mem.ok(base, 0x54) then return nil; end
        local labels, helps, values = {}, {}, {};
        for k = 0, 63 do
            local e = base + k * 0x54;
            if not mem.ok(e, 0x54) or (mem.u32(e) or 0) == 0 then break; end
            local nm, n, h = mem.u32(e + 0x28), mem.u32(e + 0x2C), mem.u32(e + 0x4C);
            local label = (nm and mem.ok(nm, 2)) and (ashita.memory.read_string(nm, 40) or ''):match('^[^%z]*') or '';
            labels[#labels + 1] = label;
            helps[#helps + 1] = (h and mem.ok(h, 2)) and (ashita.memory.read_string(h, 80) or ''):match('^[^%z]*') or '';
            if k > 0 and n and n < 1000 then
                values[#labels] = tostring(n);
                helps[#helps] = helps[#helps] .. string.format('\n%d map%s of this area.', n, n == 1 and '' or 's');
            end
        end
        local c = top + vis;
        if #labels == 0 or c < 1 or c > #labels then return nil; end
        return { obj = obj, rows = labels, helps = helps, values = values, cursor = c, name = name, style = 'list' };
    end
    if name == 'evitem01' then
        -- Key Items » a key item » "Examine <name>?": Yes / No (cursor +0x4C; no help texts)
        local c = mem.u32(obj + 0x4C);
        if c == nil or c < 1 or c > 2 then return nil; end
        local id = require('ui.keyitems').selected();
        local nm = id and AshitaCore:GetResourceManager():GetString('keyitems.names', id) or nil;
        local what = nm and ('Examine ' .. nm .. '.') or 'Examine it.';
        return { obj = obj, rows = { 'Yes', 'No' }, helps = { what, 'Back to the list.' }, cursor = c, name = name,
                 style = 'list' };
    end
    if name == 'scanlist' then
        -- Map » Wide Scan: what the scan found. Laid out like maplist (class +0x38 -> entries 0x54 apart, cursor
        -- +0x1A + +0x24), with the name at +0x2C and, at [+0x48] + 4, the entity's index (u16): its distance is shown
        -- while it's near enough to be loaded.
        local slot = slot_of(name);
        local cls = slot and mem.u32(slot);
        local base = cls and mem.u32(cls + 0x38);
        local vis, top = cls and mem.u16(cls + 0x24), cls and mem.u16(cls + 0x1A);
        if base == nil or vis == nil or top == nil or not mem.ok(base, 0x54) then return nil; end
        local ent = AshitaCore:GetMemoryManager():GetEntity();
        local labels, helps, values = {}, {}, {};
        for k = 0, 255 do
            local e = base + k * 0x54;
            if not mem.ok(e, 0x54) or (mem.u32(e) or 0) == 0 then break; end
            local nm = mem.u32(e + 0x2C);
            labels[#labels + 1] = (nm and mem.ok(nm, 2)) and (ashita.memory.read_string(nm, 40) or ''):match('^[^%z]*') or '';
            local rec = mem.u32(e + 0x48);
            local idx = (rec and mem.ok(rec, 8)) and mem.u16(rec + 4) or nil;
            local d = idx and idx > 0 and idx < 2304 and (ent:GetName(idx) or '') ~= '' and ent:GetDistance(idx) or nil;
            values[#labels] = d and string.format('%dy', math.floor(math.sqrt(d) + 0.5)) or nil;
            helps[#labels] = 'Marked on the map.  Confirm: follow it (an arrow shows the way).';
        end
        local c = top + vis;
        if #labels == 0 or c < 1 or c > #labels then return nil; end
        return { obj = obj, rows = labels, helps = helps, values = values, cursor = c, name = name, style = 'list' };
    end
    if name == 'mount' then
        -- Abilities » Mount: the mounts she has, in id order (mount k comes with key item 3072 + k, "... companion").
        -- Cursor: class +0x30 (0-based), count +0x40; the help line is the game's.
        local slot = slot_of(name);
        local cls = slot and mem.u32(slot);
        local c, n = cls and mem.u32(cls + 0x30), cls and mem.u32(cls + 0x40);
        if c == nil or n == nil then return nil; end
        local ki = require('ui.keyitems');
        local rm = AshitaCore:GetResourceManager();
        local labels = {};
        for k = 0, 63 do
            local nm = rm:GetString('mounts.names', k);
            if nm == nil or nm == '' then break; end
            local has = ki.has(3072 + k);
            if has == nil then return nil; end
            if has then labels[#labels + 1] = nm; end
        end
        if #labels ~= n or c >= n then return nil; end
        local helps = {};
        helps[c + 1] = require('ui.listpanel').help_line();
        return { obj = obj, rows = labels, helps = helps, cursor = c + 1, name = name, style = 'list' };
    end
    if name == 'faqsub' then
        -- Commands » Help Desk: six buttons with no help texts. The class object ([slot]) keeps the id of the button
        -- under the cursor at +0x2E (not its position): Q&A 0x10, Adventuring Primer 0x18, Mentor Search 0x12,
        -- Help Desk 0x13, Config 0x14, Back 0xFFFF.
        local slot = slot_of(name);
        local cls = slot and mem.u32(slot);
        local c = ({ [0x10] = 1, [0x18] = 2, [0x12] = 3, [0x13] = 4, [0x14] = 5, [0xFFFF] = 6 })[cls and mem.u16(cls + 0x2E) or 0];
        if c == nil then return nil; end
        local labels = { 'Q&A', 'Adventuring Primer', 'Mentor Search', 'Help Desk', 'Config', 'Back' };
        local helps = { 'Search the game\'s answers by keyword.', 'A guide to the basics of adventuring.',
                        'Find a mentor to ask for advice.', 'Contact a GM.', 'Help Desk settings.', 'Close the Help Desk.' };
        return { obj = obj, rows = labels, helps = helps, cursor = c, name = name, style = 'list' };
    end
    if name == 'mapv3' then
        -- Map » Markers: ten marker slots in one of two colour sets (Left / Right switch: the map's class object,
        -- mapframe +0x106, 0 pink, 1 green). A slot's name is a text object the class points to (+0x18, one per
        -- row; the text buffer at [+4]); unnamed slots show as Marker n. Confirm opens Mark / Markers / Change Name
        -- for the slot (mapv2).
        local slot = slot_of(name);
        local cls = slot and mem.u32(slot);
        local c = mem.u32(obj + 0x4C);
        if cls == nil or c == nil or c < 1 or c > 10 then return nil; end
        local rows = {};
        for r = 0, 9 do
            local t = mem.u32(cls + 0x18 + r * 4);
            local buf = t and mem.u32(t + 4);
            local txt = (buf and mem.ok(buf, 4)) and (ashita.memory.read_string(buf, 32) or ''):match('^[^%z]*') or '';
            rows[r + 1] = (txt ~= '' and txt:match('^[%w%p ]+$')) and txt or ('Marker ' .. (r + 1));
        end
        local fs = slot_of('mapframe');
        local fc = fs and mem.u32(fs);
        local set = fc and mem.u16(fc + 0x106) or 0;
        local helps = {};
        for i = 1, 10 do
            helps[i] = 'Confirm: show, place or remove, or rename this marker.  Left / Right: '
                       .. (set == 1 and 'pink' or 'green') .. ' markers.';
        end
        return { obj = obj, rows = rows, helps = helps, cursor = c, name = name, style = 'list',
                 title = set == 1 and 'Markers (Green)' or 'Markers (Pink)' };
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
            -- (a row the game greys out, e.g. Remodel or a bag not unlocked yet, has +0x48 = 1)
            list[#list + 1] = { y = ry, label = label_for(h), help = h, sel = (r == cur), off = mem.u8(r + 0x48) == 1 };
        end
    end
    table.sort(list, function (a, b) return a.y < b.y; end);
    local rows, helps, offs = {}, {}, {};
    -- known menus: the label for the button at that slot (buttons are 16 px apart, the first 6 px below the frame top)
    local order = ORDER[name];
    -- In the Mog House the game turns the Commands menu's Map into Mog House (the Moogle's menu; its help text still
    -- says "View map"). FFXI's target keeps a Mog House callback, non-zero only there.
    local in_mog = name == 'menuwind' and (AshitaCore:GetMemoryManager():GetTarget():GetMyroomCallback() or 0) ~= 0;
    if in_mog then
        order = {};
        for i, l in ipairs(ORDER.menuwind) do order[i] = l; end
        order[12] = 'Mog House';
    end
    if order then
        -- by slot; slots without a row object (e.g. Search » Master Level) still get their label
        local last = 0;
        for _, it in ipairs(list) do
            local slot = math.floor((it.y - fy1 - 6) / 16 + 0.5) + 1 - (SLOT_SKIP[name] or 0);
            rows[slot], helps[slot] = order[slot] or it.label, (HELPS[name] and HELPS[name][slot]) or it.help;
            if in_mog and slot == 12 then helps[slot] = "Open your moogle's menu."; end
            offs[slot] = it.off;
            if it.sel then cursor = slot; end
            if slot > last then last = slot; end
        end
        for i = 1, last do
            if rows[i] == nil then rows[i], helps[i] = order[i] or '', ''; end
        end
    else
        for i, it in ipairs(list) do
            rows[i], helps[i], offs[i] = it.label, it.help, it.off;
            if it.sel then cursor = i; end
        end
    end
    if #rows == 0 then return nil; end
    return { obj = obj, rows = rows, helps = helps, offs = offs, cursor = cursor, name = name, style = MENUS[name],
             page = PAGES[name] };
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
    end
    -- (every frame: the game turns a parent window back on when a sub-menu opened from it closes)
    if mem.u8(obj + 0x69) ~= 0 then mem.w8(obj + 0x69, 0); end
    if mem.u8(obj + 0x6A) ~= 0 then mem.w8(obj + 0x6A, 0); end
    if mem.u8(obj + 0x78) ~= 0 then mem.w8(obj + 0x78, 0); end
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
-- long lists (Wide Scan) show this many rows at a time, scrolling with the cursor; first row shown by menu name
local MAX_ROWS = 14;
local list_first = {};

local function render_list(m, now, depth, dim)
    local n = #m.rows;
    local shown = math.min(n, MAX_ROWS);
    local first = 1;
    if n > MAX_ROWS then
        first = list_first[m.name] or 1;
        local c = m.cursor or 1;
        if c < first then first = c; end
        if c > first + MAX_ROWS - 1 then first = c - MAX_ROWS + 1; end
        first = math.max(1, math.min(first, n - MAX_ROWS + 1));
        list_first[m.name] = first;
    end
    local h = dim and 40 or (46 + shown * ROW_H + 12);       -- a parent under a sub-menu shows its title only
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
    text.draw(title, m.title or TITLES[m.name] or '', x + 40, y + 27, 'baseline');
    -- page arrows: Left / Right switch pages in the game
    if m.page then
        local pg = ui.label('cmdlist_page' .. depth, 'slotkey', { font_height = 15, font_alignment = text.align.Center });
        pg:set_opacity(t);
        text.draw(pg, string.format('%d/2', m.page), x + LIST_W - 46, y + 25, 'baseline');
        draw.image('dlg_arrow', x + LIST_W - 74, y + 12, { rot = -math.pi / 2, color = col });    -- pointing left
        draw.image('dlg_arrow', x + LIST_W - 30, y + 12, { rot = math.pi / 2, color = col });     -- pointing right
    end
    if n > MAX_ROWS and not dim then
        local rg = ui.label('cmdlist_range' .. depth, 'small', { font_height = 14, font_color = 0xFFC8C4B8,
                                                                  font_alignment = text.align.Right });
        rg:set_opacity(t);
        text.draw(rg, string.format('%d-%d / %d', first, first + shown - 1, n), x + LIST_W - 16, y + 25, 'baseline');
    end
    local sw, sh = layout.size('row_sel');
    for r = 1, dim and 0 or shown do
        local i = first + r - 1;
        local label = m.rows[i];
        local ry = y + 44 + (r - 1) * ROW_H;
        local sel = (i == m.cursor);
        if sel then
            draw.nine('row_sel', x + 22, ry, LIST_W - 34, ROW_H - 4, 6, sw, sh, col);
            if not dim then draw.image('cursor_gold', x + 2, ry + 2, { color = col }); end
        end
        local o = ui.label('cmdlist_row' .. depth .. '_' .. r, 'small', { font_height = 19 });
        local off = m.offs and m.offs[i];
        o:set_font_color(off and (sel and 0xFFA8A49A or 0xFF7C786E) or (sel and 0xFFFFFFFF or 0xFFD8D4C8));
        o:set_opacity(t);
        text.draw(o, label, x + 34, ry + ROW_H - 9, 'baseline');
        local v = m.values and m.values[i];
        if v then
            local vo = ui.label('cmdlist_val' .. depth .. '_' .. r, 'small',
                                { font_height = 16, font_alignment = text.align.Right });
            vo:set_font_color(sel and 0xFFF0DCA0 or 0xFFB8A880);
            vo:set_opacity(t);
            text.draw(vo, v, x + LIST_W - 18, ry + ROW_H - 9, 'baseline');
        end
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

-- windows the game opens alongside some menus, hidden while xiv1ui draws them (Mount: the ability list's sort
-- tabs and the "Next" recast box; a marker's Mark / Markers / Change Name: the game's marker slots, which xiv1ui's
-- Markers list shows once a slot is being chosen)
local EXTRA_HIDE = { mount = { 'abisortw', 'subwindo' }, mapv2 = { 'mapv3' } };
local extra_hider = require('core.gamewin').new();
local function extras(name)
    local list = name and EXTRA_HIDE[name];
    if list then extra_hider:hide(list); elseif extra_hider:active() then extra_hider:restore(); end
end

function cmd.release() restore_all(); helpbar_hide(false); extra_hider:restore(); end

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
    if obj == nil then return; end
    if shown_obj[obj] then
        -- (backing out of a sub-menu, the game turns its parent back on and draws it this frame: off again now.
        -- Only while it's still the same window: zoning frees windows, and a new object can take a hidden one's
        -- address; writing into that crashed the client)
        if not alive(obj) then shown_obj[obj] = nil; early_obj = nil; return; end
        if mem.u8(obj + 0x69) ~= 0 then mem.w8(obj + 0x69, 0); end
        if mem.u8(obj + 0x6A) ~= 0 then mem.w8(obj + 0x6A, 0); end
        if mem.u8(obj + 0x78) ~= 0 then mem.w8(obj + 0x78, 0); end
        early_obj = obj;
        return;
    end
    if obj == early_obj then return; end
    early_obj = obj;
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

-- The ring stands right of the character, or left of it once the character runs over to the right of the screen
-- (the camera lets it get there before it follows), so it never covers the character; it goes back to the right
-- when the character is left of the middle. side = 1 (right) or -1 (left); side_t = when it last changed (the
-- entries slide in again from there).
local side, side_t = 1, 0;
local old_side = 1;                  -- the side it's leaving (while side_t is recent)
local SIDE_EDGE = 90;                -- HUD units either side of the screen's middle before the ring changes sides
local function ring_side()
    local me = AshitaCore:GetMemoryManager():GetParty():GetMemberTargetIndex(0);
    local sx = me and me ~= 0 and require('core.project').on_model(me, 0.5, 0, 1.0);
    if sx and store.data.ring_follow ~= false then
        local mid = layout.screen() / 2;
        if side == 1 and sx > mid + SIDE_EDGE then old_side, side, side_t = 1, -1, xi_now();
        elseif side == -1 and sx < mid - SIDE_EDGE then old_side, side, side_t = -1, 1, xi_now(); end
    end
    return side;
end

--- The ring's anchor: where the selected entry's panel starts (vertical middle): its left end on the right side,
-- its right end on the left side.
local CROSS = 0.3;                   -- seconds the ring takes to change sides (fade out, then in)
local function anchor_of(sd)
    return layout.anchor('center', 0, 0, sd == -1 and -200 or 200, -40, 'cmdmenu');
end
local function ring_anchor() return anchor_of(side); end

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

-- One side's ring. sd = 1 right of the character, -1 left (mirrored: the panels' right ends ride on the arc and the
-- panel art is flipped); mul = opacity for a cross-fade; drift = HUD units it's pushed outward (away from the
-- character) while fading.
local function draw_side(sd, mul, drift, key, items, cursor, opened_t, dim, desc, L)
    local now = xi_now();
    local px, py = anchor_of(sd);
    px = px + sd * drift;
    local cx = px - sd * RING_R;
    local cur = cursor or 1;
    local pw, lx, scale = L.pw, L.lx, L.scale;
    for _, i in ipairs(L.order) do
        local it = items[i];
        local th = (i - ring.pos) * RING_STEP;
        local t = math.max(0, math.min(1, (now - (opened_t or opened) - math.min(8, math.abs(i - cur)) * 0.025) / 0.16));
        local ease = 1 - (1 - t) ^ 3;
        local edge = cx + sd * (RING_R * math.cos(th) + (1 - ease) * 40);
        local x = (sd == 1) and edge or (edge - pw);
        local y = py + RING_R * math.sin(th) - PANEL_H / 2;
        local sel = (i == cursor);
        local fade = sel and 1 or math.max(0.2, 1 - math.abs(th) / 1.25);
        local a = ease * fade * (dim and 0.45 or 1) * mul;
        local col = draw.alpha(0xFFFFFFFF, a);
        if sd == 1 then
            draw.image(sel and 'cmd_panel_sel' or 'cmd_panel', x, y, { color = col, scale = scale });
        else
            draw.image(sel and 'cmd_panel_sel' or 'cmd_panel', x + pw, y, { color = col, scale = { -scale[1], scale[2] } });
        end
        if sel and not dim then
            local bob = math.sin(now * 3) * 2;
            draw.image('crystal_shard', (sd == 1) and (x - 26) or (x + pw + 4), y - 3 + bob, { color = col, scale = 0.8 });
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
        local hx, hy = (sd == 1) and (px + pw + 16) or (px - pw - 16 - 300), py - 19;
        local bw, bh = layout.size('win_hud');
        draw.nine('win_hud', hx, hy, 300, 60, 10, bw, bh, draw.alpha(0xFFFFFFFF, mul));
        local h1 = ui.label('cmd_target_hint', 'label', { font_height = 19, font_color = 0xFFF0E6C8 });
        h1:set_opacity(mul);
        text.draw(h1, 'Choose a target', hx + 14, hy + 24, 'baseline');
        local h2 = ui.label('cmd_target_hint2', 'small', { font_height = 16, font_color = 0xFFC8C4B8 });
        h2:set_opacity(mul);
        text.draw(h2, 'Enter / A confirms,  Esc / B back', hx + 14, hy + 48, 'baseline');
    elseif desc and desc ~= '' then
        local bw, bh = layout.size('win_hud');
        local dx, dy = (sd == 1) and (px + pw + 16) or (px - pw - 16 - 326), py - PANEL_H / 2;
        desc_obj = desc_obj or text.new('small', { font_height = 16, font_color = 0xFFE8E4D8, box_width = 300 });
        if desc_obj.settings.text ~= desc then text.set(desc_obj, desc); end
        local _, th = text.size(desc_obj);
        draw.nine('win_hud', dx, dy, 326, th + 20, 10, bw, bh, draw.alpha(0xFFFFFFFF, mul));
        desc_obj:set_opacity(mul);
        text.render(desc_obj, dx + 13, dy + 9);
    end
    return px, py;
end

--- Draw a ring of entries (the action menu, its sub-menus, and the lists opened from it).
-- key names this ring (the wheel's turn is kept per key); items = { { label, sub = right-hand text, icon = item id,
-- dim = greyed } ... }; cursor = the selected index (or nil); opened_t = when it appeared; dim = the whole ring is
-- waiting (target choice); desc = text for a box beside the selected entry. Returns the anchor x, y and panel width.
-- Changing sides, the ring fades out drifting off on the old side, then fades in on the new one, each keeping its
-- own shape (nothing is reshaped while it's seen).
function cmd.ring(key, items, cursor, opened_t, dim, desc)
    local now = xi_now();
    local n = #items;
    local sd = ring_side();
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
    local L = {};
    L.lx = icon and 56 or 24;                         -- label start within the panel
    L.pw = L.lx + wl + (ws > 0 and ws + 18 or 0) + 30;
    L.scale = { L.pw / PANEL_ART_W, PANEL_H / PANEL_ART_H };
    L.order = {};
    for i = 1, n do
        if math.abs((i - ring.pos) * RING_STEP) < 1.25 then L.order[#L.order + 1] = i; end
    end
    table.sort(L.order, function (a, b) return math.abs(a - ring.pos) > math.abs(b - ring.pos); end);

    -- (one side at a time: a text object draws in one place a frame)
    local t = (side_t > 0) and math.min(1, (now - side_t) / CROSS) or 1;
    local px, py;
    if t < 0.4 then
        local u = t / 0.4;
        local e = u * u * (3 - 2 * u);
        px, py = draw_side(old_side, 1 - e, 24 * e, key, items, cursor, opened_t, dim, desc, L);
        px, py = anchor_of(sd);
    else
        local u = (t - 0.4) / 0.6;
        local e = u * u * (3 - 2 * u);
        px, py = draw_side(sd, e, -24 * (1 - e), key, items, cursor, opened_t, dim, desc, L);
    end
    local left0 = (sd == 1) and px or (px - L.pw);    -- the selected panel's left end
    layout.bounds('cmdmenu', left0 - 40, py - 120, L.pw + 50, 240);
    return px, py, L.pw;
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
    if side == -1 then return px - 330, py - 150; end
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
    if store.data.cmd_menu == false then unhide(); helpbar_hide(false); extras(nil); return; end
    local m = cmd.read();
    extras(m and m.name);
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
        -- (only while some other window has focus: a menu closing (Esc) loses focus at once but stays in memory for
        -- a few frames, and drawing it then made closing look slow)
        -- (and not when that window is the one with focus, now declined: e.g. Key Items showing a list)
        -- back from a sub-menu to a menu under it that the game draws now (e.g. Key Items' list, after "Examine?"):
        -- that menu is the current one again
        for i, p in ipairs(stack) do
            if p.name == focused_name() then
                last_m = p;
                for j = #stack, i, -1 do stack[j] = nil; end
                break;
            end
        end
        -- the full-screen map has focus again (a marker was just placed, or the map was clicked): the menus step
        -- aside, and the game's own row of marker slots shows (it alone shows which markers are placed)
        if focused_name() == 'mapframe' then
            for obj in pairs(shown_obj) do
                if cache[obj] and cache[obj].name == 'mapv3' then restore_menu(obj); end
            end
            helpbar_hide(false);
            last_obj = nil;
            return;
        end
        if live and last_m and last_m.style == 'list' and focused_name() == last_m.name then
            -- the game draws that window; the menus under it stay xiv1ui's (dimmed, titles only)
            if shown_obj[last_m.obj] then restore_menu(last_m.obj); end
            for _, p in ipairs(stack) do render_list(p, now, depth, true); depth = depth + 1; end
            helpbar_hide(false);
            last_obj = nil;
            return;
        end
        if live and last_m and last_m.style == 'list' and focused_name() ~= '' then
            for _, p in ipairs(stack) do render_list(p, now, depth, true); depth = depth + 1; end
            render_list(last_m, now, depth, false);
        elseif live and last_m and last_m.style == 'stack' and (CHILDREN[focused_name()] or waiting) then
            -- a list opened from the action menu (spells, abilities, items): it takes the menu's place (drawn by
            -- ui/listpanel.lua / ui/itempanel.lua); the action menu stays hidden underneath
        else
            stack, last_m = {}, nil;
            -- a menu that's closing (no focus, still in memory for a few frames) stays hidden until it's gone (the loop
            -- above hands each back once it is), or the game's own box would flash as it closes
            if next(zeroed) and not (live and focused_name() == '') then restore_all(); end
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
