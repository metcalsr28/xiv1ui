--[[
* xiv1ui - chat logs, after FFXIV 1.0 (reference §16): two semi-transparent log windows at the bottom left, Log 1
* ("General": conversation and system text) above the game's own typing box and Log 2 ("Battle") stacked above it,
* each with trapezoid tabs. Lines are coloured by channel as in 1.0 (say white, party blue, linkshell green, tell
* pink, shout orange, echo purple, system blue). The windows fade out after 60 s without new text and come back
* when something arrives or the mouse is over them. The mouse wheel scrolls a log; clicking a log opens the chat input.
*
* Text is read from the game as it arrives ('text_in'); nothing is blocked, so the game's own log keeps working
* underneath (it is hidden through HXIUIBegone when that addon is loaded).
*
* Typing: the game still runs its chat input (history, Tab completion, auto-translate, / commands); xiv1ui hides its
* blue bar (window `inline`) and draws the line under Log 1 instead, with the channel it will go to, the text and a
* caret, all read through Ashita's chat manager.
--]]

local xi_now = require('core.now');
local draw    = require('core.draw');
local text    = require('core.text');
local layout  = require('core.layout');
local gdi_enc = require('gdifonts.encoding');

local chatlog = { replaces = { 'chat1', 'chat2' } };
local hider = require('core.gamewin').new();

local KEEP     = 200;         -- lines kept per log
local AUTOHIDE = 60;          -- seconds
local LOG_W    = 400;         -- larger chat text (Configuration » Chat text size) wraps more and adds height
local LOG_MIN  = 280;         -- narrowest the logs get to make room for the action bar (narrow screens, large UI scale)
local log_w    = LOG_W;       -- the logs' width this frame (see fit_width)
local BASE_SIZE = 16;
local size = BASE_SIZE;
local LINE_PAD = 2;

-- channel -> colour (ARGB)
local COLORS = {
    say = 0xFFF4F0E6, shout = 0xFFF0A040, tell = 0xFFFFA0C8, party = 0xFF8CC8FF, linkshell = 0xFF9BE08C,
    emote = 0xFFC8C8C8, echo = 0xFFC8A0F0, system = 0xFF8CB4FF, npc = 0xFFF4F0E6, battle = 0xFFE8E2D0,
    battle_dim = 0xFFA8A49A,
};
-- other addons' lines xiv1ui shows (besides its own), and handlers that claim a line for a colour of their own;
-- see chatlog.extend()
local accept_tags = { 'xiv1ui' };
local line_handlers = {};

-- FFXI chat mode -> channel. Anything not listed is battle (20..120) or general/system text.
local MODES = {
    [1] = 'say', [9] = 'say', [2] = 'shout', [10] = 'shout', [11] = 'shout', [3] = 'tell', [4] = 'tell',
    [12] = 'tell', [5] = 'party', [13] = 'party', [6] = 'linkshell', [14] = 'linkshell', [213] = 'linkshell',
    [214] = 'linkshell', [7] = 'emote', [15] = 'emote', [206] = 'echo', [207] = 'echo', [142] = 'npc',
    [144] = 'npc', [150] = 'npc', [151] = 'npc', [190] = 'npc',
};

local logs = {
    { title = 'General', lines = {}, scroll = 0, height = 176 },
    { title = 'Battle',  lines = {}, scroll = 0, height = 150, wash = true },
};
local last_text = 0;
local hover_log = nil;
local rects = {};

local function channel(mode)
    local m = bit.band(mode, 0xFF);
    local ch = MODES[m];
    if ch then return ch; end
    if m >= 20 and m <= 120 then return 'battle'; end
    if m == 163 or m == 164 or (m >= 185 and m <= 191 and m ~= 190) then return 'battle'; end
    return 'system';
end

--- Strip FFXI control codes and convert to UTF-8 for drawing.
local function clean(s)
    s = s:gsub('[\30\31].', '')              -- colour codes 0x1E/0x1F + 1 byte
         :gsub('\127[1-7][\1-\9]?', '')    -- event control codes: 0x7F + digit (prompt, timing), with a delay byte
         :gsub('\127[\240-\255]', '')        -- name link markers around a player's name (0x7F 0xFC ... 0x7F 0xFB)
         :gsub('\239\39', '{'):gsub('\239\40', '}')   -- auto-translate brackets
         :gsub('\253......\253', '{...}')    -- unexpanded auto-translate phrase
         :gsub('\135\178', '\1'):gsub('\135\179', '\2')    -- the game's emphasis brackets (shown as quotes)
         :gsub('\7', ' ')
         :gsub('%s+$', '');
    local ok, u = pcall(gdi_enc.ShiftJIS_To_UTF8, gdi_enc, s, true);
    u = ok and u or s;
    return (u:gsub('\1', '\226\128\156'):gsub('\2', '\226\128\157'));
end

local function add_line(log, str, color)
    local obj = text.new('small', { font_height = size, font_color = color, box_width = log_w - 28, outline_width = 2 });
    text.set(obj, str);
    local lines = log.lines;
    lines[#lines + 1] = obj;
    if #lines > KEEP then table.remove(lines, 1); end
    if log.scroll > 0 then log.scroll = log.scroll + 1; end      -- keep the view still while scrolled back
    last_text = xi_now();
end

function chatlog.text_in(e)
    if e.message == nil or e.message == '' then return; end
    local ch = channel(e.mode);
    local s = clean(e.message_modified or e.message);
    if s == '' then return; end
    -- the time the game prints when xiv1ui switches its clock off or on (core/native.lua)
    if require('core.native').quiet() then
        local b = s:gsub('^%[%d+:%d+:%d+%] ?', '');          -- (a timestamp addon's prefix)
        if b:find("^Vana'diel: ") or b:find('^Earth: ') or b:find('^%s*%a+ ?%a* %(%d+%%%)$') then return; end
    end
    -- an untranslated server line ("結果：", "Result:") the English client prints after some fights: noise
    if s == '\231\181\144\230\158\156\239\188\154' then return; end
    for _, h in ipairs(line_handlers) do
        local t, key = h(s);
        if t then add_line(logs[1], t, COLORS[key] or COLORS.system); return; end
    end
    if ch == 'battle' then
        add_line(logs[2], s, COLORS.battle);
    else
        add_line(logs[1], s, COLORS[ch] or COLORS.system);
    end
end

--- Draw one log window with its bottom-left corner at x, y_bottom. Returns its top y.
local INPUT_H = 30;           -- the input line, inside the bottom of Log 1 while typing
local typing = false;

local function draw_log(i, x, y_bottom, alpha)
    local log = logs[i];
    local h = log.height;
    local y = y_bottom - h;
    rects[i] = { x, y - 22, log_w, h + 22 };
    if log.wash then
        if #log.lines == 0 then return y - 22; end     -- nothing to show: no wash either
        -- the Battle log: no box; a dark wash behind the lines (drawn below, once their height is known)
    else
        local pw, ph = layout.size('log_panel');
        draw.image('log_panel', x, y, { scale = { log_w / pw, h / ph }, color = draw.alpha(0xFFFFFFFF, alpha) });
        draw.image('log_tab_active', x + 6, y - 21, { color = draw.alpha(0xFFFFFFFF, alpha) });
        if not log.tab_obj then log.tab_obj = text.new('label', { font_height = 15, font_alignment = text.align.Center }); end
        text.draw(log.tab_obj, log.title, x + 54, y - 5, 'baseline');
    end

    -- newest lines at the bottom; walk upward until the window is full
    -- The serif's text boxes carry extra space above and below the ink: trim a fixed amount per message (measured
    -- on one line), not a share of the box, or wrapped messages would overlap the next one.
    local cy = y_bottom - 6;
    if i == 1 and typing then cy = cy - INPUT_H - 2; end
    local n = #log.lines - log.scroll;
    local one = log.one_line;
    if one == nil and log.lines[1] then
        local probe = text.new('small', { font_height = size, outline_width = 2 });
        text.set(probe, 'Ag');
        local _, h1 = text.size(probe);
        one = h1; log.one_line = one; log.one_size = size;
    end
    local trim = (one or 0) * 0.18;
    -- the Battle log's wash covers exactly the lines shown: measure first, then draw wash and lines
    if log.wash then
        local top, m = cy, n;
        while m >= 1 do
            local _, bh = text.size(log.lines[m]);
            local lh = bh - trim;
            if top - lh < y + 4 then break; end
            top = top - lh - LINE_PAD;
            m = m - 1;
        end
        local ww, wh = layout.size('log_wash');
        local wy = top - 10;
        draw.image('log_wash', 0, wy, { scale = { (x + log_w + 160) / ww, (y_bottom - wy + 6) / wh },
                                        color = draw.alpha(0xFFFFFFFF, alpha) });
    end
    while n >= 1 do
        local obj = log.lines[n];
        local _, bh = text.size(obj);
        local lh = bh - trim;
        if cy - lh < y + 4 then break; end
        cy = cy - lh - LINE_PAD;
        obj:set_opacity(alpha);
        text.render(obj, x + 12, cy - trim * 0.67);
        n = n - 1;
    end
    if log.scroll > 0 then
        if not log.more_obj then log.more_obj = text.new('slotkey', { font_height = 13, font_alignment = text.align.Right }); end
        text.draw(log.more_obj, string.format('▼ %d more', log.scroll), x + log_w - 10, y_bottom - 8, 'baseline');
    end
    return y - 22;
end

-- Follow the chat text size setting: re-render existing lines at the new size and make the logs taller to match.
local function apply_size()
    local want = require('core.store').data.chat_size or BASE_SIZE;
    if want == size then return; end
    size = want;
    for _, log in ipairs(logs) do log.one_line = nil; end
    for _, log in ipairs(logs) do
        log.height = math.floor((log == logs[1] and 176 or 150) * size / BASE_SIZE + 0.5);
        for _, obj in ipairs(log.lines) do
            obj:set_font_height(size);
        end
    end
end

-- The chat input line -------------------------------------------------------------------------------------------

-- where a line will go, from what it starts with (the game's default channel is Say)
local PREFIXES = {
    { '/p ', 'Party', 'party' }, { '/party ', 'Party', 'party' }, { '/l2 ', 'Linkshell 2', 'linkshell' },
    { '/linkshell2 ', 'Linkshell 2', 'linkshell' }, { '/l ', 'Linkshell', 'linkshell' },
    { '/linkshell ', 'Linkshell', 'linkshell' }, { '/sh ', 'Shout', 'shout' }, { '/shout ', 'Shout', 'shout' },
    { '/y ', 'Yell', 'shout' }, { '/yell ', 'Yell', 'shout' }, { '/s ', 'Say', 'say' }, { '/say ', 'Say', 'say' },
    { '/em ', 'Emote', 'emote' }, { '/emote ', 'Emote', 'emote' }, { '/echo ', 'Echo', 'echo' },
};

--- Extend the chat log: e = { colors = { key = ARGB }, prefixes = { { '/x ', 'Label', key } },
-- accept = { 'text an addon's printed lines contain' }, line = function (s) -> text, colour key (or nil) }.
function chatlog.extend(e)
    for k, v in pairs(e.colors or {}) do COLORS[k] = v; end
    for _, p in ipairs(e.prefixes or {}) do table.insert(PREFIXES, p); end
    for _, t in ipairs(e.accept or {}) do accept_tags[#accept_tags + 1] = t; end
    if e.line then line_handlers[#line_handlers + 1] = e.line; end
end

--- True for a line another addon printed that the chat log shows (xiv1ui's own, and any chatlog.extend accepts).
function chatlog.accepts_injected(msg)
    for _, t in ipairs(accept_tags) do if msg:find(t, 1, true) then return true; end end
    return false;
end
-- returns the channel's label, its colour key and how many bytes of prefix the label stands for (not drawn)
local function channel_of(str)
    local low = str:lower();
    local pre = low:match('^/t%s+%S+%s') or low:match('^/tell%s+%S+%s');
    if pre then return 'Tell ' .. str:match('^/%a+%s+(%S+)'), 'tell', #pre; end
    for _, p in ipairs(PREFIXES) do
        if low:sub(1, #p[1]) == p[1] then return p[2], p[3], #p[1]; end
    end
    if low:sub(1, 1) == '/' then return 'Command', 'system', 0; end
    return 'Say', 'say', 0;
end

local input = { obj = nil, label = nil, measure = nil, key = nil, shift = 0, caret_x = 0 };

local function input_text(raw)
    local chat = AshitaCore:GetChatManager();
    local ok, parsed = pcall(chat.ParseAutoTranslate, chat, raw, true);
    return clean(ok and parsed or raw);
end

-- width of a string in the input's font (gdifonts trims trailing spaces from the ink, so measure with a bar after)
local function width_of(str)
    local m = input.measure;
    text.set(m, str .. '|');
    local w = text.size(m);
    text.set(m, '|');
    local bar = text.size(m);
    return w - bar;
end

local function draw_input(x, y, w)
    local chat = AshitaCore:GetChatManager();
    local raw = chat:GetInputTextRaw() or '';
    local caret = math.max(0, math.min(#raw, chat:GetInputTextRawCaretPosition() or #raw));
    local h = INPUT_H;
    draw.rect(x, y, w, h, 0x90000000);
    draw.rect(x, y, w, 1, 0x60C8CCE0);
    if input.obj == nil then
        input.obj = text.new('small', { font_height = size, outline_width = 2 });
        input.label = text.new('small', { font_height = size - 2, outline_width = 2 });
        input.measure = text.new('small', { font_height = size, outline_width = 2 });
    end
    local name, ch, skip = channel_of(raw);
    local col = COLORS[ch] or COLORS.say;
    input.label.settings.font_color = col;
    text.draw(input.label, name, x + 10, y + h - 9, 'baseline');
    local lw = text.size(input.label);
    local tx = x + 10 + lw + 8;
    draw.rect(tx - 5, y + 6, 1, h - 12, draw.alpha(col, 0.5));
    local room = x + w - 10 - tx;
    -- re-measure only when the line or the caret changed
    local key = raw .. '\0' .. caret .. '\0' .. skip;
    if key ~= input.key then
        input.key = key;
        -- the channel prefix ("/p ") is shown as the label instead (unless the caret is inside it)
        local from = (caret >= skip) and skip + 1 or 1;
        local before, after = input_text(raw:sub(from, caret)), input_text(raw:sub(caret + 1));
        -- keep the caret in view: drop characters off the front while the text before it doesn't fit
        local shown, cut = before, 0;
        while #shown > 0 and width_of(shown) > room - 4 do
            shown = shown:gsub('^[%z\1-\127\194-\244][\128-\191]*', '');
            cut = cut + 1;
        end
        input.caret_x = width_of(shown);
        input.line = shown .. after;
    end
    input.obj.settings.font_color = COLORS.say;
    text.draw(input.obj, input.line, tx, y + h - 8, 'baseline');
    if math.floor(xi_now() * 2) % 2 == 0 then
        draw.rect(tx + input.caret_x + 1, y + 6, 2, h - 12, 0xFFF4F0E6);
    end
end

-- Open the game's chat input, as its Space key does. The game takes chat keys from window messages (not from
-- DirectInput, where gamein.press works), so the key goes to its window.
local ffi = require('ffi');
pcall(ffi.cdef, 'int __stdcall PostMessageA(void* h, uint32_t m, uintptr_t w, intptr_t l);');
local function open_input()
    local u = ffi.load('user32');
    local h = ffi.cast('void*', AshitaCore:GetProperties():GetFinalFantasyHwnd());
    u.PostMessageA(h, 0x100, 0x20, 0x00390001);          -- WM_KEYDOWN VK_SPACE
    u.PostMessageA(h, 0x101, 0x20, 0xC0390001);          -- WM_KEYUP
end

function chatlog.release() hider:restore(); end

-- Start of each scene, before the game draws: the moment the input window exists it's hidden, so the game's bar
-- never shows for a frame (the open flag can lag a frame behind the window). Other inputs that use the same window
-- (bazaar / search comments: flag 0x20) keep the game's look, since xiv1ui draws nothing for them.
function chatlog.early()
    if require('core.gamewin').window('inline') == nil
       or bit.band(AshitaCore:GetChatManager():IsInputOpen() or 0, 0x20) ~= 0 then
        if hider:active() then hider:restore(); end
        return;
    end
    hider:hide({ 'inline' });
end

-- The logs sit at the bottom left, beside the action bar. On a narrow screen (or at a large UI scale) the bar's left
-- end, its crest, reaches into them: the logs then get narrower (down to LOG_MIN) and their lines re-wrap.
local function fit_width()
    local w = LOG_W;
    local chat, bar = layout.widgets.chat, layout.widgets.hotbar;
    if chat and bar and chat[2] < bar[2] + bar[4] and bar[2] < chat[2] + chat[4] and chat[1] < bar[1] then
        w = math.max(LOG_MIN, math.min(LOG_W, math.floor(bar[1] - 12 - chat[1])));
    end
    if w == log_w then return; end
    log_w = w;
    for _, log in ipairs(logs) do
        log.one_line = nil;
        for _, obj in ipairs(log.lines) do text.set_box_width(obj, log_w - 28); end
    end
end

function chatlog.render()
    apply_size();
    fit_width();
    -- the chat input: the game's bar hidden, ours drawn under Log 1; the logs stay up while typing
    local open = bit.band(AshitaCore:GetChatManager():IsInputOpen() or 0, 0x10) ~= 0;
    typing = open;
    if open then last_text = xi_now(); end      -- (the game's bar is hidden in chatlog.early)
    local idle = xi_now() - last_text;
    local alpha = 1;
    if hover_log == nil and idle > AUTOHIDE and require('core.store').data.chat_autohide ~= false then
        alpha = math.max(0, 1 - (idle - AUTOHIDE) / 1.5);
    end
    if alpha <= 0 then return; end     -- (the last rects stay: hovering or clicking a faded log still works)
    local sw, sh = layout.screen();
    local ox, oy = layout.offset('chat');
    -- Log 1 sits just above the game's own typing box at the bottom left; Log 2 above it.
    local top = draw_log(1, 16 + ox, sh - 46 + oy, alpha);
    if open then draw_input(16 + ox + 6, sh - 46 + oy - INPUT_H - 4, log_w - 12); end
    local top2 = draw_log(2, 16 + ox, top - 8, alpha);
    layout.bounds('chat', 16 + ox, top2, log_w, sh - 46 + oy - top2);
end

function chatlog.mouse(e)
    local over = nil;
    for i, r in pairs(rects) do
        if e.x >= r[1] and e.x < r[1] + r[3] and e.y >= r[2] and e.y < r[2] + r[4] then over = i; end
    end
    if e.message == 0x200 then hover_log = over; return; end
    -- a click on a log opens the chat input (the click itself doesn't reach the game)
    if over and (e.message == 0x201 or e.message == 0x202) then
        e.blocked = true;
        if e.message == 0x202 and bit.band(AshitaCore:GetChatManager():IsInputOpen() or 0, 0x10) == 0 then
            open_input();
        end
        return;
    end
    if over and e.message == 0x20A then                  -- WM_MOUSEWHEEL: delta in the high word of wParam
        local delta = e.delta or 0;
        local log = logs[over];
        local step = (delta > 0) and 3 or -3;
        log.scroll = math.max(0, math.min(#log.lines - 1, log.scroll + step));
        e.blocked = true;
    end
end

return chatlog;
