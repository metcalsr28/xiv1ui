--[[
* xiv1ui - the lobby: title menu, character select / delete, character creation and its confirmations, in xiv1ui's
* style (FFXIV 1.0's lobby, reference §43). Map of the game's screens: docs/LOBBY.md.
*
* As with the in-game menus, the game still runs every screen: xiv1ui reads which window is focused and where its
* cursor is, hides the game's drawing of it, and draws its own. Keys and the pad work exactly as before; a click on
* one of xiv1ui's rows moves the game's cursor there and confirms.
*
* The lobby's rows carry no help text and their labels are pictures, so the labels (and the help line) come from the
* tables below, by window and row number.
--]]

local mem     = require('core.mem');
local draw    = require('core.draw');
local text    = require('core.text');
local layout  = require('core.layout');
local xi_now  = require('core.now');
local gamewin = require('core.gamewin');
local native  = require('core.native');
local ui      = require('core.ui');
local ffi     = require('ffi');

local lobby = {};
local hider = gamewin.new();

-- Lists: the labels by row number (n), the order they appear on screen (when it isn't 1..n), and the help line.
local LISTS = {
    loby2win = { title = nil, labels = { 'Select Character', 'Create Character', 'Delete Character', 'Back', 'Config' },
                 order = { 1, 2, 3, 5, 4 },
                 helps = { 'Choose a character and enter the world.', 'Make a new character.',
                           'Delete one of your characters. Deleted characters cannot be restored.',
                           'Return to the previous screen.', "Change the game's options." } },
    chmkrace = { title = 'Race', step = 1,
                 labels = { 'Hume Male', 'Hume Female', 'Elvaan Male', 'Elvaan Female', 'Tarutaru Male',
                            'Tarutaru Female', 'Mithra', 'Galka' },
                 help = "Choose your character's race and gender." },
    chmkface = { title = 'Face', step = 2,
                 labels = { 'Face 1', 'Face 2', 'Face 3', 'Face 4', 'Face 5', 'Face 6', 'Face 7', 'Face 8' },
                 help = "Choose your character's face." },
    chmkhair = { title = 'Hair', step = 3, labels = { 'Hair A', 'Hair B' }, help = "Choose your character's hair colour." },
    chmksize = { title = 'Height', step = 4, labels = { 'Small', 'Medium', 'Large' }, help = "Choose your character's size." },
    chmkjobs = { title = 'Job', step = 5,
                 labels = { 'Warrior', 'Monk', 'White Mage', 'Black Mage', 'Red Mage', 'Thief' },
                 help = "Choose the job your character begins as. You can change jobs later in the game." },
    chfwin   = { title = 'Settings', labels = { 'Load Settings', 'Save Settings' },
                 helps = { "Load this character's settings (keys, macros, windows) from a file.",
                           "Save this character's settings to a file." } },
    chmktown = { title = 'Nation', step = 9, labels = { "San d'Oria", 'Bastok', 'Windurst' },
                 help = 'Choose the nation your character sets out from.' },
};
local RACES = { 'Hume Male', 'Hume Female', 'Elvaan Male', 'Elvaan Female', 'Tarutaru Male', 'Tarutaru Female',
                'Mithra', 'Galka' };
-- starting attributes by race (STR DEX VIT AGI INT MND CHR; FFXI's base stats, as its creation screen shows them)
local ATTR_NAMES = { 'STR', 'DEX', 'VIT', 'AGI', 'INT', 'MND', 'CHR' };
local ATTRS = { hume = { 8, 7, 6, 7, 5, 5, 6 }, elvaan = { 9, 7, 7, 6, 4, 6, 6 }, tarutaru = { 7, 7, 6, 8, 7, 5, 6 },
                mithra = { 8, 9, 6, 8, 5, 5, 5 }, galka = { 9, 7, 8, 7, 5, 5, 5 } };
-- the lobby's Yes / No questions xiv1ui knows, by the message number in the window's class object (see question())
local QUESTIONS = {
    [0x05] = { title = 'Create Character', text = 'Register "%s" and begin play?' },
    [0x0D] = { title = 'Select Character', text = 'Log in with %s?' },
    [0x04] = { title = 'Delete Character', text = 'Delete %s? The data will be lost forever. Proceed?', warn = true },
};
local STEPS = { 'Race', 'Face', 'Hair', 'Height', 'Job', 'Name', 'World', 'World Pass', 'Nation' };

-- every lobby window xiv1ui draws in place of the game's
local HIDE = { 'ptc8lice', 'ptcbgwin', 'ptc9dele', 'loby1win', 'loby2win', 'lobyhelp', 'dbnamese', 'chfwin', 'chmkname',
               'chmkserv', 'worldsel', 'chmkpass', 'chmkrace', 'chmkface', 'chmkhair', 'chmksize', 'chmkjobs', 'chmktown',
               'race1', 'race2', 'race3', 'race4', 'race5', 'race6', 'race7', 'race8' };

--- In the lobby: not in the world, and the lobby's help bar is up (it is on every lobby screen, never in the world).
function lobby.active()
    local p = AshitaCore:GetMemoryManager():GetPlayer();
    if p and p:GetLoginStatus() ~= 0 then return false; end
    return gamewin.window('lobyhelp') ~= nil;
end

local function focused()
    local o, name = native.focused();
    return o, name or '';
end

local function cursor_of(o)
    local c = o and mem.u32(o + 0x4C);
    if c == nil or c < 1 or c > 64 then return nil; end
    return c;
end

--- Between the lobby and the world (after a character is chosen, before the player exists): 1.0's loading screen,
-- black with "Now Loading..." small at the bottom right (reference §43.6).
-- (it stays up until xiv1ui's HUD can draw: the player's entity exists and the game's "Downloading data" bar is gone)
-- (safety: never more than 8 s once the player exists, or 60 s in all, whatever the windows say)
local load_since, player_since = nil, nil;
local function hud_ready()
    local mm = AshitaCore:GetMemoryManager();
    local p = mm:GetPlayer();
    if p == nil or p:GetLoginStatus() ~= 2 or p:GetMainJob() == 0 then return false; end
    local me = mm:GetParty():GetMemberTargetIndex(0);
    if me == nil or me == 0 or (mm:GetEntity():GetServerId(me) or 0) == 0 then return false; end
    player_since = player_since or xi_now();
    if xi_now() - player_since > 8 then return true; end
    local nb = gamewin.window('netbar');
    return nb == nil or mem.u8(nb + 0x6A) == 0;
end

function lobby.loading()
    if lobby.left_lobby ~= true or gamewin.window('lobyhelp') ~= nil then
        load_since, player_since = nil, nil;
        return false;
    end
    load_since = load_since or xi_now();
    if hud_ready() or xi_now() - load_since > 60 then lobby.left_lobby = false; return false; end
    return true;
end

-- (no_backdrop: only the "Now Loading..." mark, over the game's own screen; used between areas, ui/zoning.lua)
function lobby.render_loading(no_backdrop)
    local sw, sh = layout.screen();
    if not no_backdrop then draw.rect(0, 0, sw, sh, 0xFF000000); end
    local t = ui.label('lobby_loading', 'small', { font_height = 18, font_flags = 2, font_color = 0xFFE8E4D8,
                                                   font_alignment = text.align.Right });
    -- a soft pulse, and a small four-point sparkle before the words
    local a = 0.65 + 0.35 * math.sin(xi_now() * 3);
    t:set_opacity(a);
    text.draw(t, 'Now Loading...', sw - 48, sh - 44, 'baseline');
    local tw = text.size(t);
    local cx, cy = sw - 48 - tw - 16, sh - 50;
    local col = draw.alpha(0xFFE8E4D8, a);
    draw.rect(cx - 6, cy, 13, 1, col);
    draw.rect(cx, cy - 6, 1, 13, col);
    draw.image('white', cx - 2, cy - 2, { scale = { 5 / 8, 5 / 8 }, color = col, rot = math.pi / 4 });
end

-- The character list's camera. The list window (dbnamese) moves the camera to the highlighted character in its own
-- per-frame drawing, which also draws the game's logo and texts; hidden, it stops. So while xiv1ui hides it, xiv1ui
-- makes the two calls that drawing makes for the camera: the camera step (thiscall(class, 0.1) every frame) and, every
-- 150 frames, the re-aim at the highlighted character (for a model that finished loading after the camera set off).
-- Both, and the two values they use, are read from that piece of the game's code, found by its bytes; if it isn't
-- found, the list is hidden as before and the camera stays where it is.
local list_cam = nil;
local function find_list_cam()
    list_cam = false;
    local at = ashita.memory.find('FFXiMain.dll', 0,
        '8B4E28418BC1894E283D960000007C2BA1????????8D0C808D1448C1E2048BBC32AC0000003BFD740F6A018BCEE8????????893D'
        .. '????????896E285368CDCCCC3C8BCEE8????????', 0, 0);
    if at == nil or at == 0 then return; end
    local function target(call) return call + 5 + ffi.cast('int32_t*', call + 1)[0]; end
    list_cam = {
        index = mem.u32(at + 0x11),            -- the highlighted character (0-based)
        last = mem.u32(at + 0x34),             -- set to the character re-aimed at
        aim = ffi.cast('void (__fastcall*)(uint32_t, uint32_t, int32_t)', target(at + 0x2D)),
        step = ffi.cast('void (__fastcall*)(uint32_t, uint32_t, float)', target(at + 0x43)),
    };
end

local function list_camera()
    if list_cam == nil then find_list_cam(); end
    if not list_cam then return; end
    local s = gamewin.slot('dbnamese');
    local cls = s and mem.u32(s);
    if cls == nil or not mem.ok(cls, 0xC00, true) then return; end
    -- (the calls are made as fastcall with a dummy second register: the same stack as the game's thiscall)
    local frames = (mem.u32(cls + 0x28) or 0) + 1;
    if frames >= 150 then
        local i = mem.u32(list_cam.index);
        local model = (i and i < 16) and mem.u32(cls + i * 0xB0 + 0xAC) or 0;
        if model ~= 0 then
            list_cam.aim(cls, 0, 1);
            mem.w32(list_cam.last, model);
        end
        frames = 0;
    end
    mem.w32(cls + 0x28, frames);
    list_cam.step(cls, 0, 0.1);
end

-- Hide the game's drawing of the lobby windows xiv1ui replaces (at scene start, so they never show for a frame).
function lobby.early()
    -- (remember having been in the lobby: the loading screen only follows the lobby, not the game's own start-up)
    if gamewin.window('lobyhelp') ~= nil then lobby.left_lobby = true; end
    if not lobby.active() then
        if hider:active() then hider:restore(); end
        return;
    end
    hider:hide(HIDE);
    if gamewin.window('dbnamese') then list_camera(); end
    local id = gamewin.window('ptc6yesn') and lobby.question_id and lobby.question_id();
    if id and QUESTIONS[id] then hider:hide({ 'ptc6yesn' }); end
    -- the game's message box: only when xiv1ui knows what it says (see message())
    if lobby.message_text then hider:hide({ 'ok' }); end
end

function lobby.release() hider:restore(); end

-- Drawing ------------------------------------------------------------------------------------------------------------

local ROW_H = 30;

local function panel(x, y, w, h, title, a)
    local col = draw.alpha(0xFFFFFFFF, a);
    local bw, bh = layout.size('win_body');
    draw.nine('win_body', x, y, w, h, 12, bw, bh, col);
    if title then
        local tw, th = layout.size('win_title');
        draw.nine('win_title', x + 4, y + 4, w - 8, 30, 10, tw, th, col);
        draw.image('title_swash', x + 8, y + 4, { color = col });
        local t = ui.label('lobby_title_' .. title, 'name', { font_height = 22 });
        t:set_opacity(a);
        text.draw(t, title, x + 40, y + 27, 'baseline');
    end
end

-- rows: { label, ... } in screen order; sel: index into rows. Returns the rects of the rows (for clicks).
local function rows_at(key, rows, sel, x, y, w, a, size)
    local col = draw.alpha(0xFFFFFFFF, a);
    local sw, sh = layout.size('row_sel');
    local out = {};
    for i, label in ipairs(rows) do
        local ry = y + (i - 1) * ROW_H;
        if i == sel then
            draw.nine('row_sel', x + 20, ry, w - 32, ROW_H - 4, 6, sw, sh, col);
            draw.image('cursor_gold', x, ry + 3, { color = col });
        end
        local o = ui.label(key .. '_row' .. i, 'small', { font_height = size or 20 });
        o:set_font_color(i == sel and 0xFFFFFFFF or 0xFFD8D4C8);
        o:set_opacity(a);
        text.draw(o, label, x + 32, ry + ROW_H - 9, 'baseline');
        out[i] = { x, ry, w, ROW_H };
    end
    return out;
end

-- the help line along the bottom of the screen, in place of the game's help bar
local function help_line(str, a)
    if str == nil or str == '' then return; end
    local sw, sh = layout.screen();
    local o = ui.label('lobby_help', 'small', { font_height = 18, font_color = 0xFFE8E4D8 });
    if o.settings.text ~= str then text.set(o, str); end
    local tw = text.size(o);
    local w = math.min(sw - 80, tw + 80);
    local x, y = (sw - w) / 2, sh - 64;
    local bw, bh = layout.size('win_hud');
    draw.nine('win_hud', x, y, w, 36, 10, bw, bh, draw.alpha(0xFFFFFFFF, a));
    o:set_opacity(a);
    text.render(o, x + (w - tw) / 2, y + 7);
end

local opened = {};            -- window name -> when it was first seen (fade-in)
local function fade(name)
    local now = xi_now();
    if opened[name] == nil then opened[name] = now; end
    return math.max(0, math.min(1, (now - opened[name]) / 0.18));
end

local click_rows = nil;       -- { rects, rows (n per rect) } of the list drawn last frame

-- The game's title, as a wordmark (the game's own logo picture is hidden with its backdrop window, together with the
-- server's logo some installs put there), and the copyright line.
local function wordmark(a)
    local sw, sh = layout.screen();
    local cx, y = sw / 2, sh * 0.24;
    -- a soft shadow behind the title, so it reads over a bright sky
    local gw, gh = layout.size('lobby_glow');
    draw.image('lobby_glow', cx - 700, y - 190, { scale = { 1400 / gw, 330 / gh }, color = draw.alpha(0xFFFFFFFF, a * 0.85) });
    local big = ui.label('lobby_wordmark', 'numeral', { font_height = 70, font_alignment = text.align.Center,
                                                        outline_width = 4, outline_color = 0xF0080810 });
    big:set_opacity(a);
    text.draw(big, 'FINAL FANTASY XI', cx, y, 'baseline');
    -- a gold rule with a diamond, and the world's name under it
    local gold = draw.alpha(0xFFC8A860, a * 0.9);
    draw.rect(cx - 220, y + 22, 200, 1, gold);
    draw.rect(cx + 20, y + 22, 200, 1, gold);
    draw.image('white', cx - 5, y + 17, { scale = { 10 / 8, 10 / 8 }, color = gold, rot = math.pi / 4 });
    local sub = ui.label('lobby_sub', 'small', { font_height = 18, font_alignment = text.align.Center,
                                                 font_color = 0xFFE0D2A8, outline_width = 3, outline_color = 0xE0101018 });
    sub:set_opacity(a);
    text.draw(sub, "V A N A ' D I E L", cx, y + 52, 'baseline');
    local c = ui.label('lobby_copy', 'small', { font_height = 15, font_alignment = text.align.Center,
                                                font_color = 0xFFD8D4C8, outline_width = 3, outline_color = 0xE0101018 });
    c:set_opacity(a * 0.85);
    local cgw, cgh = layout.size('lobby_glow');
    draw.image('lobby_glow', cx - 160, sh - 108, { scale = { 320 / cgw, 40 / cgh }, color = draw.alpha(0xFFFFFFFF, a) });
    text.draw(c, '\u{00A9} SQUARE ENIX', cx, sh - 82, 'baseline');
end

-- The title menu: a column of commands under the game's title, centred.
local function title_menu(o, a)
    local def = LISTS.loby2win;
    local c = cursor_of(o);
    if c == nil then return; end
    local labels, sel = {}, nil;
    for i, n in ipairs(def.order) do
        labels[i] = def.labels[n];
        if n == c then sel = i; end
    end
    local sw, sh = layout.screen();
    local w = 340;
    local h = #labels * ROW_H + 28;
    local x, y = (sw - w) / 2, sh * 0.52;
    wordmark(a);
    panel(x, y, w, h, nil, a);
    click_rows = { rects = rows_at('lobby_title', labels, sel, x + 14, y + 14, w - 28, a, 21), rows = def.order };
    help_line(def.helps[c], a);
end

-- The character list (Select / Delete Character): the roster the list window keeps in its class object
-- (docs/LOBBY.md): entries 0xB0 apart, name at +0x44.
local function str_at(p, n)
    if not mem.ok(p, n) then return ''; end
    return (ashita.memory.read_string(p, n) or ''):match('^[%w%p ]*') or '';
end

local zone_by_abbr = nil;     -- the lobby's area names ("SSandOria") -> full zone names
local function zone_name(abbr)
    if zone_by_abbr == nil then
        zone_by_abbr = {};
        local rm = AshitaCore:GetResourceManager();
        -- (present-day zones first: "Bastok Markets [S]" shares Bastok Markets' short name)
        for pass = 1, 2 do
            for id = 1, 300 do
                local full = rm:GetString('zones.names', id);
                local short = rm:GetString('zones.names_abbr', id);
                if full and full ~= '' and (full:find('[', 1, true) == nil) == (pass == 1) then
                    for _, src in ipairs({ short or '', full }) do
                        local key = src:gsub('[^%a]', ''):sub(1, 10);
                        if key ~= '' and zone_by_abbr[key] == nil then zone_by_abbr[key] = full; end
                    end
                end
            end
        end
    end
    return zone_by_abbr[abbr] or abbr;
end

local function roster()
    local slot = gamewin.slot('dbnamese');
    local cls = slot and mem.u32(slot);
    if cls == nil or not mem.ok(cls + 0x20, 8) then return nil; end
    local slots, count = mem.u32(cls + 0x20), mem.u32(cls + 0x24);
    if slots == nil or slots < 1 or slots > 32 or count == nil or count > slots then return nil; end
    local list = { slots = slots, count = count };
    local rm = AshitaCore:GetResourceManager();
    for i = 0, count - 1 do
        local n = cls + 0x44 + i * 0xB0;
        local name = str_at(n, 16);
        if name ~= '' then
            local race, job, level = mem.u32(n + 0x30), mem.u32(n + 0x34), mem.u32(n + 0x48);
            list[#list + 1] = {
                name = name, world = str_at(n + 0x10, 16), area = zone_name(str_at(n - 0x10, 16)),
                race = RACES[race or 0] or '', job = (job and job > 0 and job < 32) and rm:GetString('jobs.names', job) or '',
                level = (level and level < 200) and level or 0,
            };
        end
    end
    return list;
end

local selected_char = nil;    -- the character highlighted in the list (named in the delete questions)

local function character_card(ch, a, deleting)
    local sw, sh = layout.screen();
    local x, w, h = 40, 380, 196;
    local y = sh - 120 - h;
    panel(x, y, w, h, nil, a);
    local nm = ui.label('lobby_card_name', 'name', { font_height = 30 });
    nm:set_opacity(a);
    nm:set_font_color(deleting and 0xFFF0A0A0 or 0xFFFFFFFF);
    text.draw(nm, ch.name, x + 22, y + 44, 'baseline');
    local gold = draw.alpha(0xFFC8A860, a * 0.8);
    draw.rect(x + 22, y + 56, w - 44, 1, gold);
    local lines = {
        { 'World', ch.world },
        { 'Race', ch.race },
        { 'Job', ch.level > 0 and string.format('%s  Lv. %d', ch.job, ch.level) or ch.job },
        { 'Location', ch.area },
    };
    for i, l in ipairs(lines) do
        local ly = y + 86 + (i - 1) * 27;
        local k = ui.label('lobby_card_k' .. i, 'small', { font_height = 16, font_color = 0xFFB8A880 });
        local v = ui.label('lobby_card_v' .. i, 'small', { font_height = 19, font_color = 0xFFE8E4D8 });
        k:set_opacity(a); v:set_opacity(a);
        text.draw(k, l[1], x + 22, ly, 'baseline');
        text.draw(v, l[2], x + 112, ly, 'baseline');
    end
end

local CHAR_H = 50;
local function character_list(o, a)
    local list = roster();
    local c = cursor_of(o);
    if list == nil or c == nil then return; end
    -- Select and Delete share the list window; only Select has the Options (settings) window beside it
    local deleting = gamewin.window('chfwin') == nil;
    local sw, sh = layout.screen();
    -- only the characters there are: the game's cursor can run on into the empty slots below them (Down keeps going);
    -- it's pushed back onto the last character
    local shown = math.max(#list, 1);
    if #list > 0 and c > #list then
        local t = xi_now();
        if t - (lobby.pushed_back or 0) > 0.2 then
            lobby.pushed_back = t;
            require('ui.gamein').press(0xC8);        -- Up
        end
        c = #list;
    end
    local w = 380;
    local h = 46 + shown * CHAR_H + 44;
    local x, y = sw - w - 40, math.max(40, sh - 120 - h);
    panel(x, y, w, h, deleting and 'Delete Character' or 'Characters', a);
    local col = draw.alpha(0xFFFFFFFF, a);
    local sw9, sh9 = layout.size('row_sel');
    local rects, order = {}, {};
    for i = 1, shown do
        local ry = y + 44 + (i - 1) * CHAR_H;
        local ch = list[i];
        local sel = i == c;
        if sel then
            draw.nine('row_sel', x + 32, ry, w - 44, CHAR_H - 4, 6, sw9, sh9, col);
            draw.image('cursor_gold', x + 12, ry + 13, { color = col });
        end
        local nm = ui.label('lobby_char_n' .. i, 'small', { font_height = 21 });
        local sub = ui.label('lobby_char_s' .. i, 'small', { font_height = 15 });
        nm:set_opacity(a); sub:set_opacity(a);
        if ch then
            nm:set_font_color(sel and 0xFFFFFFFF or 0xFFE0DCD0);
            sub:set_font_color(0xFFB8A880);
            text.draw(nm, ch.name, x + 46, ry + 22, 'baseline');
            text.draw(sub, string.format('Lv. %d %s  \u{00B7}  %s', ch.level, ch.job, ch.area), x + 46, ry + 40, 'baseline');
        else
            nm:set_font_color(0xFF8C887C);
            text.draw(nm, 'Empty slot', x + 46, ry + 30, 'baseline');
        end
        rects[i], order[i] = { x, ry, w, CHAR_H }, i;
    end
    click_rows = { rects = rects, rows = order };
    local cnt = ui.label('lobby_char_count', 'small', { font_height = 15, font_color = 0xFFB8A880 });
    cnt:set_opacity(a);
    text.draw(cnt, string.format('%d of %d character slots used', list.count, list.slots), x + 18, y + h - 16, 'baseline');
    if list[c] then character_card(list[c], a, deleting); end
    selected_char = list[c] and list[c].name or nil;
    help_line(deleting and 'Choose a character to delete. Deleted characters cannot be restored.'
                       or 'Choose a character to play.   + : Settings (load / save)', a);
end

-- What has been chosen so far in creation (by step window), kept as the player moves through the steps.
local chosen = {};

-- The character sheet beside the step list: race, its starting attributes, and the choices so far.
local function creation_sheet(a)
    local race = chosen.chmkrace;
    if race == nil then return; end
    local key = race:match('^(%a+)'):lower();
    local attrs = ATTRS[key];
    local x, y, w = 40, nil, 300;
    local _, sh = layout.screen();
    local h = 60 + 7 * 24 + 18 + 4 * 26 + 18;
    y = sh - 120 - h;
    panel(x, y, w, h, nil, a);
    local nm = ui.label('lobby_sheet_race', 'name', { font_height = 26 });
    nm:set_opacity(a);
    text.draw(nm, race, x + 20, y + 40, 'baseline');
    local gold = draw.alpha(0xFFC8A860, a * 0.8);
    draw.rect(x + 20, y + 52, w - 40, 1, gold);
    -- attributes: a bar each (out of 10), like 1.0's attribute window
    for i, n in ipairs(ATTR_NAMES) do
        local ly = y + 78 + (i - 1) * 24;
        local k = ui.label('lobby_sheet_k' .. i, 'small', { font_height = 15, font_color = 0xFFB8A880 });
        local v = ui.label('lobby_sheet_v' .. i, 'small', { font_height = 17, font_color = 0xFFE8E4D8,
                                                             font_alignment = text.align.Right });
        k:set_opacity(a); v:set_opacity(a);
        text.draw(k, n, x + 20, ly, 'baseline');
        local val = attrs and attrs[i] or 0;
        text.draw(v, tostring(val), x + 92, ly, 'baseline');
        draw.rect(x + 104, ly - 10, 170, 6, draw.alpha(0xFF2A2620, a));
        draw.rect(x + 104, ly - 10, math.floor(170 * val / 10), 6, draw.alpha(0xFFC8A860, a));
    end
    local rows = { { 'Face', chosen.chmkface }, { 'Hair', chosen.chmkhair }, { 'Height', chosen.chmksize },
                   { 'Job', chosen.chmkjobs } };
    local ry = y + 78 + 7 * 24 + 14;
    draw.rect(x + 20, ry - 12, w - 40, 1, gold);
    for i, r in ipairs(rows) do
        local ly = ry + 12 + (i - 1) * 26;
        local k = ui.label('lobby_sheet_ck' .. i, 'small', { font_height = 15, font_color = 0xFFB8A880 });
        local v = ui.label('lobby_sheet_cv' .. i, 'small', { font_height = 18 });
        k:set_opacity(a); v:set_opacity(a);
        v:set_font_color(r[2] and 0xFFE8E4D8 or 0xFF8C887C);
        text.draw(k, r[1], x + 20, ly, 'baseline');
        text.draw(v, r[2] or '-', x + 104, ly, 'baseline');
    end
end

-- Name, world and World Pass (steps 6-8): one panel with the three fields, the one being chosen highlighted.
local PROFILE = { chmkname = 6, worldsel = 7, chmkpass = 8 };
local PROFILE_HELP = {
    chmkname = 'Type a name and press Enter. Numeric keypad + : a random name. Short names (8 letters or fewer) show in full everywhere.',
    worldsel = 'Choose the world your character will live on.',
    chmkpass = 'Enter a Gold World Pass if a friend gave you one, so you start on their world. Otherwise press Enter.',
};

-- the name: while it's being typed, the game's text input holds it (Ashita sees it as the input line, with the
-- "other input" flag 0x20); once entered, the name window's class object keeps it (+0x14)
local function name_text()
    local chat = AshitaCore:GetChatManager();
    if bit.band(chat:IsInputOpen() or 0, 0x20) ~= 0 then
        return (chat:GetInputTextRaw() or ''):match('^[%w]*') or '', chat:GetInputTextRawCaretPosition();
    end
    local slot = gamewin.slot('chmkname');
    local cls = slot and mem.u32(slot);
    return cls and str_at(cls + 0x14, 16) or '';
end

local function worlds()
    local slot = gamewin.slot('worldsel');
    local cls = slot and mem.u32(slot);
    local out = {};
    local n = cls and mem.u32(cls + 0x10);
    if n == nil or n < 1 or n > 32 then return out; end
    for i = 0, n - 1 do out[#out + 1] = str_at(cls + 0x60 + i * 0x10, 16); end
    return out;
end

local function profile(name, o, a)
    local step = PROFILE[name];
    creation_sheet(a);
    local x, y, w = 40, 40, 420;
    local wl = worlds();
    local list_h = (name == 'worldsel') and (#wl * ROW_H + 8) or 0;
    local h = 46 + 3 * 64 + list_h + 36;
    panel(x, y, w, h, 'Profile', a);
    local typed, caret = name_text();
    local fields = {
        { 'Name', typed, 'chmkname' },
        { 'World', (name == 'chmkname') and '-' or (wl[1] or '-'), 'worldsel' },
        { 'Gold World Pass', step >= 8 and 'None' or '-', 'chmkpass' },
    };
    local fy = y + 48;
    local col = draw.alpha(0xFFFFFFFF, a);
    for i, f in ipairs(fields) do
        local active = f[3] == name;
        local k = ui.label('lobby_prof_k' .. i, 'small', { font_height = 15, font_color = 0xFFB8A880 });
        k:set_opacity(a);
        text.draw(k, f[1], x + 22, fy + 14, 'baseline');
        -- the field: a dark well, gold-edged when it's the one being chosen
        local fx, fw = x + 18, w - 36;
        draw.rect(fx, fy + 20, fw, 34, draw.alpha(0xC0000000, a));
        draw.rect(fx, fy + 53, fw, 1, draw.alpha(active and 0xFFC8A860 or 0x60C8C0B0, a));
        if active then draw.rect(fx, fy + 20, 2, 34, draw.alpha(0xFFC8A860, a)); end
        local v = ui.label('lobby_prof_v' .. i, 'small', { font_height = 21 });
        v:set_opacity(a);
        v:set_font_color(f[2] == '-' and 0xFF8C887C or 0xFFFFFFFF);
        text.draw(v, f[2], fx + 12, fy + 45, 'baseline');
        if active and f[3] == 'chmkname' and math.floor(xi_now() * 2) % 2 == 0 then
            -- the caret: after the letters before it (measured on a copy of the field's text up to the caret)
            local tw = 0;
            if f[2] ~= '' then
                local upto = caret and f[2]:sub(1, caret) or f[2];
                local m = ui.label('lobby_prof_measure', 'small', { font_height = 21 });
                if m.settings.text ~= upto .. '|' then text.set(m, upto .. '|'); end
                local bar = ui.label('lobby_prof_bar', 'small', { font_height = 21 });
                if bar.settings.text ~= '|' then text.set(bar, '|'); end
                tw = text.size(m) - text.size(bar);
            end
            draw.rect(fx + 14 + tw, fy + 26, 2, 22, col);
        end
        fy = fy + 64;
        if active and f[3] == 'worldsel' then
            local c = cursor_of(o) or 1;
            local rects = rows_at('lobby_worlds', wl, c, x + 12, fy, w - 24, a);
            local order = {};
            for j = 1, #wl do order[j] = j; end
            click_rows = { rects = rects, rows = order };
            fy = fy + list_h;
        end
    end
    local st = ui.label('lobby_step', 'small', { font_height = 15, font_color = 0xFFB8A880 });
    st:set_opacity(a);
    text.draw(st, string.format('Step %d of %d', step, #STEPS), x + 16, y + h - 14, 'baseline');
    help_line(PROFILE_HELP[name], a);
end

-- The nations' descriptions, as the game has them (strings in FFXiMain.dll: the title, then the text).
local NATION_TITLES = { "The Kingdom of San d'Oria", 'The Republic of Bastok', 'The Federation of Windurst' };
local lore_cache = {};

-- The lobby's texts (the nations' descriptions, the user agreement) are the game's own strings, loaded at an
-- address that changes from one start to the next (before or after FFXiMain.dll). They're found by one scan of the
-- readable memory the first time any is needed, for all of them at once, and kept.
pcall(ffi.cdef, [[
typedef struct { void* BaseAddress; void* AllocationBase; uint32_t AllocationProtect; size_t RegionSize; uint32_t State;
                 uint32_t Protect; uint32_t Type; } XIV1UI_MBI;
size_t __stdcall VirtualQuery(const void* address, void* buffer, size_t length);
]]);
local TEXTS = { "\0The Kingdom of San d'Oria\0", '\0The Republic of Bastok\0', '\0The Federation of Windurst\0',
                '\0FINAL FANTASY XI is a massively' };
local found = nil;
local function scan_texts()
    found = {};
    local k32 = ffi.load('kernel32');
    local mbi = ffi.new('XIV1UI_MBI[1]');
    local a, left = 0x10000, #TEXTS;
    while a < 0x7FFF0000 and left > 0 do
        if k32.VirtualQuery(ffi.cast('const void*', a), mbi, ffi.sizeof(mbi[0])) == 0 then break; end
        local r = mbi[0];
        local rb, size = tonumber(ffi.cast('uintptr_t', r.BaseAddress)), tonumber(r.RegionSize);
        local prot = bit.band(r.Protect, 0xFF);
        if r.State == 0x1000 and (prot == 0x02 or prot == 0x04 or prot == 0x20 or prot == 0x40)
           and bit.band(r.Protect, 0x100) == 0 and size <= 0x2000000 then
            local blob = ffi.string(ffi.cast('const char*', rb), size);
            for _, t in ipairs(TEXTS) do
                if found[t] == nil then
                    local f = blob:find(t, 1, true);
                    if f then found[t] = rb + f - 1; left = left - 1; end
                end
            end
        end
        a = rb + size;
    end
end
local function find_text(needle)
    if found == nil then scan_texts(); end
    return found[needle];
end
local function lore(i)
    if lore_cache[i] ~= nil then return lore_cache[i] or nil; end
    lore_cache[i] = false;
    local t = NATION_TITLES[i];
    local ok, a = pcall(find_text, '\0' .. t .. '\0');
    if ok and a then
        a = a + 1;
        local body = ashita.memory.read_string(a + #t + 1, 1200) or '';
        body = body:match('^[^%z]*') or '';
        -- the game breaks lines and indents paragraphs with spaces: keep the paragraphs, let the text wrap
        body = body:gsub('\n   ', '\0'):gsub('\n', ' '):gsub('%z', '\n\n'):gsub('^%s+', '');
        if body ~= '' then lore_cache[i] = { title = t, body = body }; end
    end
    return lore_cache[i] or nil;
end

local function nation_card(i, a)
    local l = lore(i);
    if l == nil then return; end
    local sw, sh = layout.screen();
    local w = 560;
    local body = ui.label('lobby_lore_body', 'small', { font_height = 18, font_color = 0xFFE8E4D8, box_width = w - 56 });
    if body.settings.text ~= l.body then text.set(body, l.body); end
    local _, bh = text.size(body);
    local h = 70 + bh + 24;
    local x, y = sw - w - 60, (sh - h) / 2 - 40;
    panel(x, y, w, h, nil, a);
    local tt = ui.label('lobby_lore_title', 'name', { font_height = 28 });
    tt:set_opacity(a);
    text.draw(tt, l.title, x + 28, y + 44, 'baseline');
    draw.rect(x + 28, y + 56, w - 56, 1, draw.alpha(0xFFC8A860, a * 0.8));
    body:set_opacity(a);
    text.render(body, x + 28, y + 70);
end

-- A creation step: the step list at the top left, with where the step falls in the whole process.
local function step_list(name, o, a)
    local def = LISTS[name];
    local c = cursor_of(o);
    if c == nil or c > #def.labels then return; end
    chosen[name] = def.labels[c];
    -- going back to an earlier step forgets the later choices
    for n, d in pairs(LISTS) do
        if d.step and def.step and d.step > def.step then chosen[n] = nil; end
    end
    if def.step and def.step <= 5 then creation_sheet(a); end
    if name == 'chmktown' then nation_card(c, a); end
    local x, y, w = 40, 40, 300;
    local h = 46 + #def.labels * ROW_H + 40;
    panel(x, y, w, h, def.title, a);
    local order = {};
    for i = 1, #def.labels do order[i] = i; end
    click_rows = { rects = rows_at('lobby_' .. name, def.labels, c, x + 12, y + 44, w - 24, a), rows = order };
    -- Step n of 9
    local st = ui.label('lobby_step', 'small', { font_height = 15, font_color = 0xFFB8A880 });
    st:set_opacity(a);
    text.draw(st, string.format('Step %d of %d', def.step, #STEPS), x + 16, y + h - 14, 'baseline');
    help_line(def.help, a);
end

-- The lobby's Yes / No questions (window ptc6yesn: row 1 Yes, row 2 No). The window's class object says which
-- question it is (+0x18, a message number) and the character it names (+0x20). Only questions whose number is known
-- are restyled: any other one keeps the game's own box, so a question can never be shown with the wrong words.
local function question_id()
    local slot = gamewin.slot('ptc6yesn');
    local cls = slot and mem.u32(slot);
    if cls == nil or not mem.ok(cls + 0x18, 0x18) then return nil; end
    return mem.u32(cls + 0x18), str_at(cls + 0x20, 16);
end
lobby.question_id = question_id;
local prev_focus = nil;
local last_question = nil;       -- the last Yes / No question's number ('delete' for the delete countdown)
local last_who = nil;            -- the character it named

local function question(o, a)
    local c = cursor_of(o);
    if c == nil or c > 2 then return; end
    local id, who = question_id();
    local def = id and QUESTIONS[id];
    if def == nil then return; end
    local title, warn = def.title, def.warn;
    local body = string.format(def.text, who ~= '' and who or 'this character');
    local sw, sh = layout.screen();
    local w = 560;
    local q = ui.label('lobby_q_body', 'small', { font_height = 21, font_color = 0xFFE8E4D8, box_width = w - 60 });
    if q.settings.text ~= body then text.set(q, body); end
    local _, qh = text.size(q);
    local h = 46 + 24 + qh + 30 + 40 + 24;
    local x, y = (sw - w) / 2, (sh - h) / 2;
    draw.rect(0, 0, sw, sh, draw.alpha(0x80000000, a));          -- the scene dims behind the question
    panel(x, y, w, h, title, a);
    q:set_opacity(a);
    q:set_font_color(warn and 0xFFF0B0A0 or 0xFFE8E4D8);
    local qw = text.size(q);
    text.render(q, x + (w - qw) / 2, y + 64);
    -- Yes / No as two buttons; the game's cursor picks which is lit
    local by = y + h - 64;
    local rects = {};
    for i, label in ipairs({ 'Yes', 'No' }) do
        local bx = x + w / 2 - 170 + (i - 1) * 180;
        local sel = i == c;
        local img = sel and 'btn_pill_focus' or 'btn_pill';
        local fw, fh = layout.size(img);
        draw.nine(img, bx, by, 160, 40, 12, fw, fh, draw.alpha(0xFFFFFFFF, a));
        local t = ui.label('lobby_q_btn' .. i, 'small', { font_height = 20, font_alignment = text.align.Center });
        t:set_opacity(a);
        t:set_font_color(sel and 0xFFFFFFFF or 0xFFC8C4B8);
        text.draw(t, label, bx + 80, by + 27, 'baseline');
        rects[i] = { bx, by, 160, 40 };
    end
    -- clicks: Left / Right move between the buttons here
    click_rows = { rects = rects, rows = { 1, 2 }, horizontal = true };
end

-- The game's message box (window ok: one OK button). Its text isn't kept anywhere stable, so the box is restyled only
-- after a step whose message is known; any other message is left to the game.
local function message(a)
    local str = lobby.message_text;
    if str == nil then return; end
    local sw, sh = layout.screen();
    local w = 520;
    local q = ui.label('lobby_msg', 'small', { font_height = 21, font_color = 0xFFE8E4D8, box_width = w - 60 });
    if q.settings.text ~= str then text.set(q, str); end
    local _, qh = text.size(q);
    local h = 30 + qh + 30 + 40 + 24;
    local x, y = (sw - w) / 2, (sh - h) / 2;
    draw.rect(0, 0, sw, sh, draw.alpha(0x80000000, a));
    panel(x, y, w, h, nil, a);
    q:set_opacity(a);
    local qw = text.size(q);
    text.render(q, x + (w - qw) / 2, y + 30);
    local bx, by = x + (w - 160) / 2, y + h - 64;
    local fw, fh = layout.size('btn_pill_focus');
    draw.nine('btn_pill_focus', bx, by, 160, 40, 12, fw, fh, draw.alpha(0xFFFFFFFF, a));
    local t = ui.label('lobby_msg_ok', 'small', { font_height = 20, font_alignment = text.align.Center });
    t:set_opacity(a);
    text.draw(t, 'OK', bx + 80, by + 27, 'baseline');
    click_rows = { rects = { { bx, by, 160, 40 } }, rows = { 1 } };
end

-- The last step of deleting (window ptc9dele: Delete, Cancel). First it asks for Delete with the D key (L3) held;
-- once chosen, the game counts down a few seconds (its cursor is gone then) and Cancel still stops it.
local function delete_dialog(o, a)
    local c = cursor_of(o);
    -- (once Delete is chosen the game counts down a few seconds with the same window up, and its cursor doesn't say
    -- so: one wording that's true either way)
    local counting = false;
    local who = last_who or selected_char or 'this character';
    local body = string.format('Erase %s for good? Hold the D key (or L3) and choose Delete. After a short countdown '
                               .. 'the character is gone; Cancel stops it.', who);
    local sw, sh = layout.screen();
    local w = 560;
    local q = ui.label('lobby_del_body', 'small', { font_height = 21, font_color = 0xFFF0B0A0, box_width = w - 60 });
    if q.settings.text ~= body then text.set(q, body); end
    local _, qh = text.size(q);
    local h = 46 + 24 + qh + 30 + 40 + 24;
    local x, y = (sw - w) / 2, (sh - h) / 2;
    draw.rect(0, 0, sw, sh, draw.alpha(0x80000000, a));
    panel(x, y, w, h, 'Delete Character', a);
    q:set_opacity(a);
    local qw = text.size(q);
    text.render(q, x + (w - qw) / 2, y + 64);
    local by = y + h - 64;
    local rects = {};
    for i, label in ipairs({ 'Delete', 'Cancel' }) do
        local bx = x + w / 2 - 170 + (i - 1) * 180;
        local sel = (i == c) or (counting and i == 2);
        local img = sel and 'btn_pill_focus' or 'btn_pill';
        local fw, fh = layout.size(img);
        local alpha = (counting and i == 1) and a * 0.4 or a;
        draw.nine(img, bx, by, 160, 40, 12, fw, fh, draw.alpha(0xFFFFFFFF, alpha));
        local t = ui.label('lobby_del_btn' .. i, 'small', { font_height = 20, font_alignment = text.align.Center });
        t:set_opacity(alpha);
        t:set_font_color(sel and 0xFFFFFFFF or 0xFFC8C4B8);
        text.draw(t, label, bx + 80, by + 27, 'baseline');
        rects[i] = { bx, by, 160, 40 };
    end
    -- (keys only here: Delete needs the D key held, so a click can't do it)
end

-- The first screen after start-up: the user agreement (window ptc8lice: Accept, Decline) over the game's striped
-- backdrop (ptcbgwin). The wording is the game's own (a string next to the lobby's other texts).
local agreement = nil;
local function agreement_screen(o, a)
    local sw, sh = layout.screen();
    draw.rect(0, 0, sw, sh, 0xFF06080C);
    wordmark(a);
    if agreement == nil then
        agreement = false;
        local ok, at = pcall(find_text, '\0FINAL FANTASY XI is a massively');
        if ok and at then
            local t = (ashita.memory.read_string(at + 1, 600) or ''):match('^[^%z]*') or '';
            agreement = t:gsub('\n', ' '):gsub('%s+', ' ');
        end
    end
    local c = cursor_of(o);
    if c == nil or c > 2 then return; end
    local w = 620;
    local body = ui.label('lobby_agree', 'small', { font_height = 20, font_color = 0xFFE8E4D8, box_width = w - 64 });
    local str = agreement or 'Before playing, please read and accept the FINAL FANTASY XI User Agreement.';
    if body.settings.text ~= str then text.set(body, str); end
    local _, bh = text.size(body);
    local h = 46 + 20 + bh + 30 + 40 + 24;
    local x, y = (sw - w) / 2, sh * 0.42;
    panel(x, y, w, h, 'User Agreement', a);
    body:set_opacity(a);
    text.render(body, x + 32, y + 62);
    local by = y + h - 64;
    local rects = {};
    for i, label in ipairs({ 'Accept', 'Decline' }) do
        local bx = x + w / 2 - 170 + (i - 1) * 180;
        local sel = i == c;
        local img = sel and 'btn_pill_focus' or 'btn_pill';
        local fw, fh = layout.size(img);
        draw.nine(img, bx, by, 160, 40, 12, fw, fh, draw.alpha(0xFFFFFFFF, a));
        local t = ui.label('lobby_agree_btn' .. i, 'small', { font_height = 20, font_alignment = text.align.Center });
        t:set_opacity(a);
        t:set_font_color(sel and 0xFFFFFFFF or 0xFFC8C4B8);
        text.draw(t, label, bx + 80, by + 27, 'baseline');
        rects[i] = { bx, by, 160, 40 };
    end
    click_rows = { rects = rects, rows = { 1, 2 }, horizontal = true };
end

function lobby.render()
    local o, name = focused();
    if name ~= prev_focus then
        -- the last question answered decides what the next message box says (other windows can take focus for a
        -- moment in between); any list or creation step forgets it
        if name == 'ptc6yesn' then
            local who;
            last_question, who = question_id();
            if who and who ~= '' then last_who = who; end
        elseif name == 'ptc9dele' then last_question = 'delete';
        elseif LISTS[name] or PROFILE[name] or name == 'dbnamese' then last_question = nil; end
        if name == 'ok' then
            if last_question == 0x05 then
                lobby.message_text = 'Player data registered.';
            elseif last_question == 'delete' then
                -- (the game's text here is about unused content IDs on a Square Enix account)
                lobby.message_text = string.format('%s has been deleted.', last_who or selected_char or 'The character');
            else
                lobby.message_text = nil;
            end
        elseif name ~= '' and name ~= 'netbar' then
            lobby.message_text = nil;
        end
        prev_focus = name;
    end
    click_rows = nil;
    local a = fade(name);
    for k in pairs(opened) do if k ~= name then opened[k] = nil; end end
    if name == 'loby2win' then
        chosen = {};
        title_menu(o, a);
    elseif name == 'dbnamese' then
        character_list(o, a);
    elseif name == 'chfwin' then
        -- Settings over the character list (the list keeps its place underneath)
        character_list(gamewin.window('dbnamese'), a);
        local def, c = LISTS.chfwin, cursor_of(o);
        if c and c <= 2 then
            local sw, sh = layout.screen();
            local w, h = 300, 46 + 2 * ROW_H + 16;
            local x, y = sw - 380 - 40 - w - 16, sh - 120 - h;
            panel(x, y, w, h, def.title, a);
            click_rows = { rects = rows_at('lobby_chf', def.labels, c, x + 12, y + 44, w - 24, a), rows = { 1, 2 } };
            help_line(def.helps[c], a);
        end
    elseif LISTS[name] then
        step_list(name, o, a);
    elseif PROFILE[name] then
        profile(name, o, a);
    elseif name == 'ptc6yesn' then
        question(o, a);
    elseif name == 'ok' then
        message(a);
    elseif name == 'ptc9dele' then
        delete_dialog(o, a);
    elseif name == 'ptc8lice' then
        agreement_screen(o, a);
    end
end

-- Move the game's cursor from row `from` to row `to` (places in screen order) with Up / Down, then confirm.
local function press_to(from, to, horizontal)
    local gamein = require('ui.gamein');
    local d = to - from;
    local fwd, back = 0xD0, 0xC8;
    if horizontal then fwd, back = 0xCD, 0xCB; end
    for _ = 1, math.abs(d) do gamein.press(d > 0 and fwd or back); end
    gamein.press(0x1C);
end

--- Choose a row of the focused lobby list by its label (for the dev bridge and tests). Returns true if found.
function lobby.go(label)
    local o, name = focused();
    local def = LISTS[name];
    local c = cursor_of(o);
    if def == nil or c == nil then return false; end
    local order = def.order;
    if order == nil then order = {}; for i = 1, #def.labels do order[i] = i; end end
    local from, to = nil, nil;
    for i, n in ipairs(order) do
        if n == c then from = i; end
        if def.labels[n] == label then to = i; end
    end
    if from == nil or to == nil then return false; end
    press_to(from, to);
    return true;
end

-- Mouse: a click on a row moves the game's cursor there (Up / Down, as the keys would) and confirms.
function lobby.mouse(e)
    if click_rows == nil then return; end
    local hit = nil;
    for i, r in ipairs(click_rows.rects) do
        if e.x >= r[1] and e.x < r[1] + r[3] and e.y >= r[2] and e.y < r[2] + r[4] then hit = i; end
    end
    if hit == nil or (e.message ~= 0x201 and e.message ~= 0x202) then return; end
    e.blocked = true;
    if e.message ~= 0x202 then return; end
    local o = focused();
    local c = cursor_of(o);
    if c == nil then return; end
    -- move in screen order: from the cursor's place in the list to the clicked row
    local from = nil;
    for i, n in ipairs(click_rows.rows) do if n == c then from = i; end end
    if from == nil then return; end
    press_to(from, hit, click_rows.horizontal);
end

return lobby;
