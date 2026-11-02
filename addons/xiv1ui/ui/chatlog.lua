--[[
* xiv1ui - chat logs, after FFXIV 1.0 (reference §16): two semi-transparent log windows at the bottom left, Log 1
* ("General": conversation and system text) above the game's own typing box and Log 2 ("Battle") stacked above it,
* each with trapezoid tabs. Lines are coloured by channel as in 1.0 (say white, party blue, linkshell green, tell
* pink, shout orange, echo purple, system blue). The windows fade out after 60 s without new text and come back
* when something arrives or the mouse is over them. The mouse wheel scrolls a log; clicking a log opens the chat input.
*
* Customisable (Configuration » Chat; store.data.chat): font, text size, line spacing, outline, background opacity,
* timestamps, repeated lines collapsed into one ("× 3"), battle text in its own log or merged into General. The logs
* are resized by dragging the grip at a log's top-right corner (width for both, height for that log).
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
local rich    = require('core.richtext');
local ui      = require('core.ui');

local chatlog = { replaces = { 'chat1', 'chat2' } };
local hider = require('core.gamewin').new();

local KEEP     = 200;         -- lines kept per log
local AUTOHIDE = 60;          -- seconds
local LOG_W    = 400;         -- default width; the player can resize the logs (store.data.chat.w)
local LOG_MIN  = 280;         -- narrowest the default-width logs get to make room for the action bar
local W_MIN, W_MAX, H_MIN, H_MAX = 240, 1400, 70, 900;    -- resize limits (HUD units)
local log_w    = LOG_W;       -- the logs' width this frame (see fit_width)
local BASE_SIZE = 16;
local size = BASE_SIZE;
local LINE_PAD = 2;

-- Fonts offered for the chat (all bundled, OFL, except Arial). Japanese text still switches to the Japanese font.
chatlog.FONTS = {
    { id = 'serif',   label = 'XIV1UI Serif' },
    { id = 'sans',    label = 'PT Sans',    family = 'PT Sans' },
    { id = 'ptserif', label = 'PT Serif',   family = 'PT Serif' },
    { id = 'arial',   label = 'Arial',      family = 'Arial' },
};

-- The chat settings, with defaults filled in.
local function cfg()
    local st = require('core.store').data;
    local t = st.chat or {};
    -- (saved tables carry Ashita's table helpers, e.g. :size() and :merge(): read the values raw)
    local function c(k) return rawget(t, k); end
    return {
        font = c('font') or 'serif',
        size = c('size') or rawget(st, 'chat_size') or BASE_SIZE,
        w = c('w') or 0, h1 = c('h1') or 0, h2 = c('h2') or 0,  -- 0 = default size
        bg = c('bg') or 0.85,                                    -- background opacity
        outline = c('outline') or 2,
        spacing = c('spacing') or LINE_PAD,
        collapse = c('collapse') ~= false,
        stamps = c('stamps') == true,
        merge = c('merge') == true,                              -- battle text in the General log
        hide = c('hide') or {},                                  -- channels left out of the logs: hide[channel] = true
        colors = c('colors') ~= false,                           -- key words in colour (ui/chatcolor.lua)
    };
end
chatlog.cfg = cfg;

local function font_family(id)
    for _, f in ipairs(chatlog.FONTS) do if f.id == id then return f.family or text.SERIF; end end
    return text.SERIF;
end
chatlog.font_family = font_family;

-- channel -> colour (ARGB)
local COLORS = {
    say = 0xFFF4F0E6, shout = 0xFFF0A040, tell = 0xFFFFA0C8, party = 0xFF8CC8FF, linkshell = 0xFF9BE08C,
    emote = 0xFFC8C8C8, echo = 0xFFC8A0F0, system = 0xFF8CB4FF, npc = 0xFFF4F0E6, battle = 0xFFE8E2D0,
    unity = 0xFFFFD270, assist = 0xFFA8DCF0,
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
    -- (a linkshell's message, Unity, Assist J / E and Linkshell 2: the numbers FFXI's log uses, as Balloon and FancyChat list them)
    [205] = 'linkshell', [211] = 'unity', [212] = 'unity', [217] = 'linkshell', [220] = 'assist', [221] = 'assist', [222] = 'assist',
    [223] = 'assist',
};

local logs = {
    { title = 'General', lines = {}, scroll = 0, height = 176 },
    { title = 'Battle',  lines = {}, scroll = 0, height = 150, wash = true },
};
function chatlog.logs_for_dev() return logs; end
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
    -- auto-translate phrases arrive as codes (0xFD id 0xFD): Ashita's parser writes them out, in 0xEF 0x27 /
    -- 0xEF 0x28 brackets (left as codes they came out as junk characters)
    if s:find('\253') then
        local cm = AshitaCore:GetChatManager();
        local ok, parsed = pcall(cm.ParseAutoTranslate, cm, s, true);
        if ok and type(parsed) == 'string' then s = parsed; end
    end
    s = s:gsub('[\30\31].', '')              -- colour codes 0x1E/0x1F + 1 byte
         :gsub('\127[1-7][\1-\9]?', '')    -- event control codes: 0x7F + digit (prompt, timing), with a delay byte
         :gsub('\127[\240-\255]', '')        -- name link markers around a player's name (0x7F 0xFC ... 0x7F 0xFB)
         :gsub('\239\39', '{'):gsub('\239%(', '}')   -- auto-translate brackets (0xEF 0x27 / 0xEF 0x28)
         :gsub('\253[^\253]*\253', '{...}') -- an auto-translate phrase the parser didn't know
         :gsub('\135\178', '\1'):gsub('\135\179', '\2')    -- the game's emphasis brackets (shown as quotes)
         :gsub('\7', '\n')               -- the game's line break: a new log line (chatlog.text_in)
         :gsub('%s+$', '');
    local ok, u = pcall(gdi_enc.ShiftJIS_To_UTF8, gdi_enc, s, true);
    u = ok and u or s;
    return (u:gsub('\1', '\226\128\156'):gsub('\2', '\226\128\157'));
end

-- A log line: { obj = text object, raw = the message, color, count (repeats collapsed into it), stamp }.
local style_key = nil;        -- font|size|outline the line objects were made with
local function new_obj(c, color)
    local obj = text.new('small', { font_height = c.size, font_color = color, box_width = log_w - 28,
                                    outline_width = c.outline, font_family = font_family(c.font) });
    obj.base_family = font_family(c.font);
    return obj;
end
local function line_text(ln, c)
    local t = ln.raw;
    if ln.count > 1 then t = t .. '  \u{00D7}' .. ln.count; end
    if c.stamps then t = '[' .. ln.stamp .. '] ' .. t; end
    return t;
end

-- A line's text object, or, when some of its words are lit (ui/chatcolor.lua), a rich text laid out from pieces
-- (core/richtext.lua): make / refresh it, measure it, draw it.
local function make_line(ln, c)
    local pieces = c.colors and require('ui.chatcolor').pieces(ln.raw, ln.color) or nil;
    if pieces then
        ln.obj = nil;
        ln.rich = rich.new({ font_family = font_family(c.font), font_height = c.size, outline_width = c.outline });
        if c.stamps then table.insert(pieces, 1, { '[' .. ln.stamp .. '] ', ln.color }); end
        if ln.count > 1 then pieces[#pieces + 1] = { '  \u{00D7}' .. ln.count, ln.color }; end
        rich.set(ln.rich, pieces);
        rich.set_width(ln.rich, log_w - 28);
    else
        ln.rich = nil;
        ln.obj = new_obj(c, ln.color);
        text.set(ln.obj, line_text(ln, c));
    end
end
local function line_size(ln)
    if ln.rich then return rich.size(ln.rich); end
    return text.size(ln.obj);
end
local function line_render(ln, x, y, alpha)
    if ln.rich then rich.render(ln.rich, x, y, alpha); return; end
    ln.obj:set_opacity(alpha);
    text.render(ln.obj, x, y);
end
local function line_width(ln, w)
    if ln.rich then rich.set_width(ln.rich, w); else text.set_box_width(ln.obj, w); end
end

-- The General log's tabs (1.0 had the same idea): each shows the lines of some channels; a tab that isn't open
-- marks new lines for it (pink for a tell). The open tab is kept in store.data.chat.tab.
local TABS = {
    { title = 'General' },
    { title = 'Party', ch = { party = true } },
    { title = 'Linkshell', ch = { linkshell = true } },
    { title = 'Tells', ch = { tell = true } },
};
local function tab_index()
    local t = tonumber((require('core.store').data.chat or {}).tab) or 1;
    return TABS[t] and t or 1;
end
local function shows(tab, ln) return tab.ch == nil or tab.ch[ln.ch or ''] == true; end

-- a tell's notice above the logs ("Tell from Aldo"), for a few seconds
local tell_note = nil;        -- { from, t }

local function add_line(log, str, color, ch)
    local c = cfg();
    local lines = log.lines;
    local last = lines[#lines];
    last_text = xi_now();
    if log == logs[1] then
        local open = tab_index();
        for k, tab in ipairs(TABS) do
            if k ~= open and tab.ch and tab.ch[ch or ''] then tab.unread = true; end
        end
    end
    if c.collapse and last and last.raw == str and last.color == color then
        last.count = last.count + 1;
        last.stamp = os.date('%H:%M');
        make_line(last, c);
        return;
    end
    local ln = { raw = str, color = color, count = 1, stamp = os.date('%H:%M'), ch = ch };
    make_line(ln, c);
    lines[#lines + 1] = ln;
    if #lines > KEEP then table.remove(lines, 1); end
    if log.scroll > 0 then log.scroll = log.scroll + 1; end      -- keep the view still while scrolled back
end

local function take_line(s, ch)
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
        if t then add_line(logs[1], t, COLORS[key] or COLORS.system, key); return; end
    end
    local c = cfg();
    if c.hide[ch] then return; end
    if ch == 'battle' and c.merge then
        add_line(logs[1], s, COLORS.battle, 'battle');
    elseif ch == 'battle' then
        add_line(logs[2], s, COLORS.battle, 'battle');
    else
        add_line(logs[1], s, COLORS[ch] or COLORS.system, ch);
    end
end

-- Ctrl+R: reply to the last tell (chatlog.reply). An incoming tell is chat mode 12, "Name>> message".
local last_tell_from = nil;

--- Opens the chat line with "/tell <last sender> " (Ctrl+R); false if no tell came yet.
-- The chat line is opened as a player opens it, by typing (a space opens it; letters typed into a closed line
-- are lost), and the text is set once it's open (chatlog.render).
pcall(require('ffi').cdef, 'int __stdcall PostMessageA(void* h, uint32_t m, uintptr_t w, intptr_t l);');
local reply_text, reply_until, reply_open = nil, 0, nil;
--- Open the chat line with "/tell <name> " (name: the last tell's sender when nil); false if there's nobody.
function chatlog.reply(name)
    name = name or last_tell_from;
    if name == nil then return false; end
    local h = require('ffi').cast('void*', AshitaCore:GetProperties():GetFinalFantasyHwnd());
    reply_text, reply_until = '/tell ' .. name .. ' ', xi_now() + 1;
    if bit.band(AshitaCore:GetChatManager():IsInputOpen() or 0, 0x10) == 0 then
        require('ffi').C.PostMessageA(h, 0x102, 0x20, 1);
    end
    return true;
end

function chatlog.text_in(e)
    if e.message == nil or e.message == '' then return; end
    local ch = channel(e.mode);
    if bit.band(e.mode, 0xFF) == 12 then
        local from = clean(e.message):gsub('^%[%d+:%d+:?%d*%] ?', ''):match('^(%a[%a%d]*)>>');
        if from then last_tell_from = from; tell_note = { from = from, t = xi_now() }; end
    end
    -- (one message can hold several lines, e.g. "X casts Y." and "X gains the effect of Z."; each is a log line,
    -- else a coloured word's line break drew its second line over the next one)
    -- (leading spaces dropped: FFXI centres some lines with them, e.g. the moon phase, and the font library sizes a
    -- line by its ink, so they pushed the end of the line out of view: "Last Quarter Moon (6(")
    for part in clean(e.message_modified or e.message):gmatch('[^\r\n]+') do take_line((part:gsub('^ +', '')), ch); end
end

--- Draw one log window with its bottom-left corner at x, y_bottom. Returns its top y.
local INPUT_H = 30;           -- the input line, inside the bottom of Log 1 while typing
local typing = false;

local grip_hover = nil;       -- the log whose resize grip is under the pointer
local function draw_log(i, x, y_bottom, alpha)
    local log = logs[i];
    local c = cfg();
    local h = log.height;
    local y = y_bottom - h;
    rects[i] = { x, y - 22, log_w, h + 22 };
    log.grip = { x + log_w - 18, y - (log.wash and 0 or 2), 18, 18 };
    if log.wash then
        if #log.lines == 0 then return y - 22; end     -- nothing to show: no wash either
        -- the Battle log: no box; a dark wash behind the lines (drawn below, once their height is known)
    else
        local pw, ph = layout.size('log_panel');
        draw.image('log_panel', x, y, { scale = { log_w / pw, h / ph }, color = draw.alpha(0xFFFFFFFF, alpha * c.bg) });
        if i == 1 then
            -- the tabs: the open one lit; others carry a dot while they hold lines not yet seen
            local open = tab_index();
            log.tab_rects = {};
            for k, tab in ipairs(TABS) do
                local tx = x + 6 + (k - 1) * 92;
                draw.image(k == open and 'log_tab_active' or 'log_tab', tx, y - 21, { color = draw.alpha(0xFFFFFFFF, alpha) });
                tab.obj = tab.obj or text.new('label', { font_height = 15, font_alignment = text.align.Center });
                local tc = (k == open) and 0xFFFFFFFF or 0xFFB8BCC8;
                if tab.obj.settings.font_color ~= tc then tab.obj:set_font_color(tc); end
                tab.obj:set_opacity(alpha);
                text.draw(tab.obj, tab.title, tx + 48, y - 5, 'baseline');
                if tab.unread then
                    local dc = (tab.ch and tab.ch.tell) and COLORS.tell or 0xFFF0D080;
                    local pulse = 0.65 + 0.35 * math.abs(math.sin(xi_now() * 3));
                    draw.image('white', tx + 84, y - 16, { scale = { 6 / 8, 6 / 8 }, color = draw.alpha(dc, alpha * pulse),
                                                          rot = math.pi / 4 });
                end
                log.tab_rects[k] = { tx, y - 21, 92, 22 };
            end
        else
            draw.image('log_tab_active', x + 6, y - 21, { color = draw.alpha(0xFFFFFFFF, alpha) });
            if not log.tab_obj then log.tab_obj = text.new('label', { font_height = 15, font_alignment = text.align.Center }); end
            text.draw(log.tab_obj, log.title, x + 54, y - 5, 'baseline');
        end
    end

    -- newest lines at the bottom; walk upward until the window is full
    -- The serif's text boxes carry extra space above and below the ink: trim a fixed amount per message (measured
    -- on one line), not a share of the box, or wrapped messages would overlap the next one.
    local cy = y_bottom - 6;
    if i == 1 and typing then cy = cy - INPUT_H - 2; end
    -- the open tab's lines (the General tab: all of them)
    local lines = log.lines;
    if i == 1 then
        local tab = TABS[tab_index()];
        if tab.ch then
            lines = {};
            for _, ln in ipairs(log.lines) do if shows(tab, ln) then lines[#lines + 1] = ln; end end
        end
    end
    log.view_n = #lines;
    log.hits = {};                                     -- (lines on screen, for clicks on a name)
    local n = #lines - log.scroll;
    local one = log.one_line;
    if one == nil and log.lines[1] then
        local probe = text.new('small', { font_height = size, outline_width = c.outline, font_family = font_family(c.font) });
        text.set(probe, 'Ag');
        local _, h1 = text.size(probe);
        one = h1; log.one_line = one; log.one_size = size;
    end
    local trim = (one or 0) * 0.18;
    -- the Battle log's wash covers exactly the lines shown: measure first, then draw wash and lines
    if log.wash then
        local top, m = cy, n;
        while m >= 1 do
            local _, bh = line_size(lines[m]);
            local lh = bh - trim;
            if top - lh < y + 4 then break; end
            top = top - lh - c.spacing;
            m = m - 1;
        end
        local ww, wh = layout.size('log_wash');
        local wy = top - 10;
        draw.image('log_wash', 0, wy, { scale = { (x + log_w + 160) / ww, (y_bottom - wy + 6) / wh },
                                        color = draw.alpha(0xFFFFFFFF, alpha * c.bg) });
    end
    while n >= 1 do
        local ln = lines[n];
        local _, bh = line_size(ln);
        local lh = bh - trim;
        if cy - lh < y + 4 then break; end
        cy = cy - lh - c.spacing;
        line_render(ln, x + 12, cy - trim * 0.67, alpha);
        if log.hits then log.hits[#log.hits + 1] = { x + 12, cy, lh, ln }; end
        n = n - 1;
    end
    if log.scroll > 0 then
        if not log.more_obj then log.more_obj = text.new('slotkey', { font_height = 13, font_alignment = text.align.Right }); end
        text.draw(log.more_obj, string.format('▼ %d more', log.scroll), x + log_w - 10, y_bottom - 8, 'baseline');
    end
    -- the resize grip: three short diagonal strokes at the top-right corner, shown while the pointer is on the log
    if hover_log == i or grip_hover == i or chatlog.resizing then
        local g = log.grip;
        local col = draw.alpha(grip_hover == i and 0xFFF4E0A0 or 0xB0E8E4D8, alpha);
        for k = 0, 2 do
            local o = 4 + k * 4;
            for d = 0, o do draw.rect(g[1] + g[3] - 4 - o + d, g[2] + 2 + d, 1, 1, col); end
        end
    end
    return y - 22;
end

-- Follow the chat settings: a new font, size or outline remakes the line objects; the logs' heights follow the
-- player's sizes (or, by default, grow with the text size).
local function apply_style()
    local c = cfg();
    size = c.size;
    logs[1].height = (c.h1 > 0) and c.h1 or math.floor(176 * size / BASE_SIZE + 0.5);
    logs[2].height = (c.h2 > 0) and c.h2 or math.floor(150 * size / BASE_SIZE + 0.5);
    local key = c.font .. '|' .. c.size .. '|' .. c.outline .. '|' .. tostring(c.stamps) .. '|' .. tostring(c.colors);
    if key == style_key then return; end
    style_key = key;
    for _, log in ipairs(logs) do
        log.one_line = nil;
        for _, ln in ipairs(log.lines) do make_line(ln, c); end
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
    { '/u ', 'Unity', 'unity' }, { '/unity ', 'Unity', 'unity' }, { '/assistj ', 'Assist (J)', 'assist' },
    { '/assiste ', 'Assist (E)', 'assist' },
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
    if input.obj and input.style ~= style_key then input.obj = nil; input.key = nil; end
    draw.rect(x, y, w, h, 0x90000000);
    draw.rect(x, y, w, 1, 0x60C8CCE0);
    if input.obj == nil then
        local c = cfg();
        local fam = font_family(c.font);
        input.obj = text.new('small', { font_height = size, outline_width = c.outline, font_family = fam });
        input.label = text.new('small', { font_height = size - 2, outline_width = c.outline, font_family = fam });
        input.measure = text.new('small', { font_height = size, outline_width = c.outline, font_family = fam });
        input.style = style_key;
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
    if input.line:find('[{}]') then
        -- auto-translate phrases with FFXI's green / red brackets, as in the logs
        if input.rich_for ~= input.line or input.rich_style ~= style_key then
            local c = cfg();
            input.rich = rich.new({ font_family = font_family(c.font), font_height = size, outline_width = c.outline });
            input.rich_for, input.rich_style = input.line, style_key;
            local pieces = {};
            for part, br in input.line:gmatch('([^{}]*)([{}]?)') do
                if part ~= '' then pieces[#pieces + 1] = { part, COLORS.say }; end
                if br == '{' then pieces[#pieces + 1] = { br, 0xFF6EE06E }; elseif br == '}' then pieces[#pieces + 1] = { br, 0xFFFF6E6E }; end
            end
            rich.set(input.rich, pieces);
            rich.set_width(input.rich, 4000);
        end
        local _, rh = rich.size(input.rich);
        rich.render(input.rich, tx, y + (h - rh) / 2, 1);
    else
        input.obj.settings.font_color = COLORS.say;
        text.draw(input.obj, input.line, tx, y + h - 8, 'baseline');
    end
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
    local chosen = cfg().w;
    local w = LOG_W;
    if chosen > 0 then
        w = chosen;                -- the player's width (they can move or shrink the action bar themselves)
    else
        local chat, bar = layout.widgets.chat, layout.widgets.hotbar;
        if chat and bar and chat[2] < bar[2] + bar[4] and bar[2] < chat[2] + chat[4] and chat[1] < bar[1] then
            w = math.max(LOG_MIN, math.min(LOG_W, math.floor(bar[1] - 12 - chat[1])));
        end
    end
    if w == log_w then return; end
    log_w = w;
    for _, log in ipairs(logs) do
        log.one_line = nil;
        for _, ln in ipairs(log.lines) do line_width(ln, log_w - 28); end
    end
end

function chatlog.render()
    apply_style();
    fit_width();
    if reply_text then
        -- (a moment after the line opens: set at once, the game's own opening overwrote part of it)
        if bit.band(AshitaCore:GetChatManager():IsInputOpen() or 0, 0x10) ~= 0 then
            reply_open = reply_open or xi_now();
            if xi_now() - reply_open > 0.15 then
                AshitaCore:GetChatManager():SetInputText(reply_text);
                reply_text, reply_open = nil, nil;
            end
        elseif xi_now() > reply_until then
            reply_text, reply_open = nil, nil;
        end
    end
    -- the chat input: the game's bar hidden, ours drawn under Log 1; the logs stay up while typing
    local open = bit.band(AshitaCore:GetChatManager():IsInputOpen() or 0, 0x10) ~= 0;
    typing = open;
    if open then last_text = xi_now(); end      -- (the game's bar is hidden in chatlog.early)
    local idle = xi_now() - last_text;
    local alpha = 1;
    if hover_log == nil and idle > AUTOHIDE and require('core.store').data.chat_autohide ~= false then
        alpha = math.max(0, 1 - (idle - AUTOHIDE) / 1.5);
    end
    -- a game window the player is using, drawn by the game where the logs are (the Mog House's job change and
    -- area lists, the auto-translate picker that Tab opens while typing ...): the logs step aside while it has
    -- focus (the line being typed stays)
    local sw, sh = layout.screen();
    local ox, oy = layout.offset('chat');
    local chat = layout.widgets.chat;
    if chat then
        local _, focus = require('core.native').focused();
        local fx, fy, fw, fh;
        if focus then fx, fy, fw, fh = require('core.gamewin').rect(focus); end
        if focus == 'fep' and fx == nil then fx, fy, fw, fh = chat[1], chat[2], 1, 1; end   -- (xiv1ui's own list)
        if fx and fx < chat[1] + chat[3] and chat[1] < fx + fw and fy < chat[2] + chat[4] and chat[2] < fy + fh then
            if open then draw_input(16 + ox + 6, sh - 46 + oy - INPUT_H - 4, log_w - 12); end
            return;
        end
    end
    if alpha <= 0 then return; end     -- (the last rects stay: hovering or clicking a faded log still works)
    -- Log 1 sits just above the game's own typing box at the bottom left; Log 2 above it.
    local top = draw_log(1, 16 + ox, sh - 46 + oy, alpha);
    if open then draw_input(16 + ox + 6, sh - 46 + oy - INPUT_H - 4, log_w - 12); end
    local top2 = top;
    if cfg().merge then rects[2] = nil; logs[2].grip = nil; else top2 = draw_log(2, 16 + ox, top - 8, alpha); end
    layout.bounds('chat', 16 + ox, top2, log_w, sh - 46 + oy - top2);
    local nh = chatlog.name_hover;
    if nh then draw.rect(nh[1], nh[2] + nh[4] - 3, nh[3], 1, draw.alpha(0xFFF4F0E6, alpha)); end
    -- a new tell: a notice over the logs for a few seconds (Ctrl+R answers)
    if tell_note then
        local age = xi_now() - tell_note.t;
        if age > 6 then
            tell_note = nil;
        else
            local na = math.min(1, age / 0.2, (6 - age) / 0.5);
            local msg = 'Tell from ' .. tell_note.from .. '   Ctrl+R: reply';
            local o = ui.label('chat_tell_note', 'label', { font_height = 17, font_color = COLORS.tell });
            o:set_opacity(na);
            if o.settings.text ~= msg then text.set(o, msg); end
            local tw = text.size(o);
            local bw, bh = layout.size('win_hud');
            local nx, ny = 16 + ox, top - 22 - 38;            -- (just above the General log's tabs)
            draw.nine('win_hud', nx, ny, tw + 28, 34, 10, bw, bh, draw.alpha(0xFFFFFFFF, na));
            text.render(o, nx + 14, ny + 7);
        end
    end
end

-- Resizing: a press on a log's grip starts it; moving changes the width (both logs) and that log's height (the
-- logs grow upward from their bottom edge); release saves. Called before HUD dragging (xiv1ui.lua), so the grip
-- doesn't move the whole chat.
chatlog.resizing = nil;
local function on_grip(e)
    for i, log in ipairs(logs) do
        local g = log.grip;
        if g and rects[i] and e.x >= g[1] - 4 and e.x < g[1] + g[3] + 4 and e.y >= g[2] - 4 and e.y < g[2] + g[4] + 4 then
            return i;
        end
    end
end

function chatlog.resize_mouse(e)
    local r = chatlog.resizing;
    if r then
        local st = require('core.store');
        st.data.chat = st.data.chat or {};
        if e.message == 0x200 then
            rawset(st.data.chat, 'w', math.floor(math.max(W_MIN, math.min(W_MAX, r.w + (e.x - r.x)))));
            rawset(st.data.chat, r.key, math.floor(math.max(H_MIN, math.min(H_MAX, r.h - (e.y - r.y)))));
        elseif e.message == 0x202 then
            chatlog.resizing = nil;
            st.save();
        end
        e.blocked = true;
        return true;
    end
    local i = on_grip(e);
    if e.message == 0x200 then grip_hover = i; return false; end
    if i and e.message == 0x201 then
        chatlog.resizing = { x = e.x, y = e.y, w = log_w, h = logs[i].height, key = (i == 1) and 'h1' or 'h2' };
        e.blocked = true;
        return true;
    end
    return false;
end

-- Who wrote a chat line, and where the name sits in it: the text before the name and the name.
-- Say / shout / yell "Name : ", party "(Name) ", linkshell "<Name> ", a tell "Name>> " or ">>Name : ".
local SENDER = {
    { '^()(%a[%a%d]*) : ', '' }, { '^(%()(%a[%a%d]*)%) ', '(' }, { '^(<)(%a[%a%d]*)> ', '<' },
    { '^()(%a[%a%d]*)>> ', '' }, { '^(>>)(%a[%a%d]*) : ', '>>' },
};
local function sender(ln)
    if ln.ch ~= 'say' and ln.ch ~= 'shout' and ln.ch ~= 'party' and ln.ch ~= 'linkshell' and ln.ch ~= 'tell' then return nil; end
    for _, p in ipairs(SENDER) do
        local _, name = ln.raw:match(p[1]);
        if name then return p[2], name; end
    end
    return nil;
end

local name_measure = nil;
local function measure(str)
    local c = cfg();
    if name_measure == nil or name_measure.key ~= style_key then
        name_measure = { obj = text.new('small', { font_height = c.size, outline_width = c.outline, font_family = font_family(c.font) }),
                         key = style_key };
    end
    local m = name_measure.obj;
    text.set(m, str .. '|');
    local w = text.size(m);
    text.set(m, '|');
    return w - text.size(m);
end

-- The line and name under the pointer (a player's name at the start of a chat line), or nil.
local function name_at(x, y)
    for i = 1, 2 do
        for _, h in ipairs(logs[i].hits or {}) do
            if y >= h[2] and y < h[2] + h[3] then
                local pre, name = sender(h[4]);
                if name == nil then return nil; end
                local me = AshitaCore:GetMemoryManager():GetParty():GetMemberName(0);
                if name == me then return nil; end
                local stamp = cfg().stamps and ('[' .. h[4].stamp .. '] ') or '';
                local x0 = h[1] + measure(stamp .. pre);
                local x1 = x0 + measure(name);
                if x >= x0 and x < x1 then return name, x0, h[2], x1 - x0, h[3]; end
                return nil;
            end
        end
    end
end
chatlog.name_hover = nil;          -- { x, y, w, h } of the name under the pointer (underlined)

function chatlog.mouse(e)
    local over = nil;
    for i, r in pairs(rects) do
        if e.x >= r[1] and e.x < r[1] + r[3] and e.y >= r[2] and e.y < r[2] + r[4] then over = i; end
    end
    if e.message == 0x200 then
        hover_log = over;
        local name, nx, ny, nw, nh = nil, nil, nil, nil, nil;
        if over then name, nx, ny, nw, nh = name_at(e.x, e.y); end
        chatlog.name_hover = name and { nx, ny, nw, nh } or nil;
        return;
    end
    -- a click on a player's name in a line: a tell to them (the chat line opens with "/tell Name ")
    if over and (e.message == 0x201 or e.message == 0x202) then
        local name = name_at(e.x, e.y);
        if name then
            e.blocked = true;
            if e.message == 0x202 then chatlog.reply(name); end
            return;
        end
    end
    -- a click on a tab of the General log opens that tab
    for k, r in ipairs(logs[1].tab_rects or {}) do
        if e.x >= r[1] and e.x < r[1] + r[3] and e.y >= r[2] and e.y < r[2] + r[4]
                and (e.message == 0x201 or e.message == 0x202) then
            e.blocked = true;
            if e.message == 0x202 then chatlog.open_tab(k); end
            return;
        end
    end
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
        log.scroll = math.max(0, math.min((log.view_n or #log.lines) - 1, log.scroll + step));
        e.blocked = true;
    end
end


--- Open tab k of the General log (1 General, 2 Party, 3 Linkshell, 4 Tells).
function chatlog.open_tab(k)
    if TABS[k] == nil then return; end
    local st = require('core.store');
    st.data.chat = st.data.chat or {};
    rawset(st.data.chat, 'tab', k);
    st.save();
    TABS[k].unread = nil;
    logs[1].scroll = 0;
    last_text = xi_now();
end

--- Page Up / Page Down scroll the General log (with Shift, the Battle log), as in FFXI's own; true if handled.
function chatlog.key(e, down)
    local vk = e.wparam;
    if vk ~= 0x21 and vk ~= 0x22 then return false; end
    local _, focus = require('core.native').focused();
    if focus ~= nil and focus ~= 'inline' then return false; end        -- (a menu uses them)
    if down then
        local shift = bit.band(require('ffi').C.GetKeyState(0x10), 0x8000) ~= 0;
        local log = (shift and not cfg().merge) and logs[2] or logs[1];
        local step = (vk == 0x21) and 5 or -5;
        log.scroll = math.max(0, math.min(math.max(0, (log.view_n or #log.lines) - 1), log.scroll + step));
        last_text = xi_now();                       -- (a log being read doesn't fade)
    end
    return true;
end

return chatlog;
