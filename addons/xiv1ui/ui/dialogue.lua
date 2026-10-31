--[[
* xiv1ui - NPC dialogue, after FFXIV 1.0's talk window: a soft-edged translucent black box at the lower centre of the
* screen, the speaker's name on a small grey plate above its top-left corner, the line in white serif, and a gold
* chevron at the bottom right while the game is waiting for you to continue.
*
* FFXI has no dialogue box of its own: NPC lines go to the chat log as "Name : text", ending in a prompt code
* (0x7F 0x31..0x37) when the game waits for Enter / the confirm button. xiv1ui reads those lines as they arrive and
* shows the latest one here. The line is taken out of the chat log (only its prompt code is passed on, so the game still
* waits for you); the game advances the conversation itself, and the box closes when you continue, pick a menu option, the conversation ends, or (for lines
* with no prompt) after a few seconds.
*
* Chat modes and prompt codes as documented by the Balloon addon: 150/152 NPC speech; 142, 144 and 151 are event
* and system text, shown only during an event.
--]]

local xi_now = require('core.now');
local draw   = require('core.draw');
local text   = require('core.text');
local layout = require('core.layout');
local store  = require('core.store');
local gdi_enc = require('gdifonts.encoding');
local choice  = require('ui.choice');
local gamewin = require('core.gamewin');

local dialogue = {};

local W = 640;               -- box width (HUD units)
local PAD_X, PAD_Y = 26, 22;
local MIN_H = 96;
local EDGE = 32;             -- feathered nine-slice corner (dlg_box)

local SPEECH = { [150] = true, [152] = true };
local EVENT_ONLY = { [142] = true, [144] = true, [151] = true };

local cur = nil;             -- { name, body, prompt, t0, expire }
local last_name = nil;       -- the most recent speaker (names the choice window)
local name_obj, body_obj, q_obj;
local row_objs = {};
local ROW_H, MAX_SHOWN = 32, 8;

function dialogue.init()
    name_obj = text.new('label', { font_height = 16, font_color = 0xFFE6DCC0 });
    body_obj = text.new('small', { font_height = 20, font_color = 0xFFF8F6F0, box_width = W - 2 * PAD_X });
    q_obj    = text.new('small', { font_height = 20, font_color = 0xFFF8F6F0, box_width = W - 2 * PAD_X });
end

-- Configuration » General: the box's font and text size (store.data.dlg_font: a chat font id; dlg_size: px)
-- (the choices are a size smaller than the text, as at the default 20 / 19)
local style_key, style_fam, style_size = nil, nil, 20;
local function style_obj(o, h)
    o.base_family = style_fam;
    o:set_font_family(style_fam);
    o:set_font_height(h);
    o.is_dirty = true;
end
local function apply_style()
    local font, size = store.data.dlg_font or 'serif', store.data.dlg_size or 20;
    local key = font .. '|' .. size;
    if key == style_key then return; end
    style_key, style_fam, style_size = key, require('ui.chatlog').font_family(font), size;
    style_obj(body_obj, size);
    style_obj(q_obj, size);
    for _, o in pairs(row_objs) do style_obj(o, size - 1); end
end

-- The game's own event text windows (the message line "rem4line" and its frame "rem4li2"): xiv1ui's box shows their
-- text, so they stay hidden while they're up.
local hider = gamewin.new();
local EVENT_WINDOWS = { 'rem4line', 'rem4li2' };

function dialogue.release() choice.release(); hider:restore(); end

function dialogue.close() cur = nil; end
function dialogue.current() return cur; end

local function in_event()
    local party = AshitaCore:GetMemoryManager():GetParty();
    local ent = AshitaCore:GetMemoryManager():GetEntity();
    local idx = party:GetMemberTargetIndex(0);
    return idx ~= 0 and ent:GetStatusServer(idx) == 4, idx, ent;
end

--- Shift-JIS line from the game -> UTF-8 for drawing; FFXI's 0x07 line breaks become real ones.
local function clean(s)
    -- (0x87 0xB2 / 0x87 0xB3 are the game's emphasis brackets around a key word, e.g. "check": shown as quotes;
    -- 0x0B marks where a message's options start, one per line: shown as a list)
    local quote_open, quote_close = '\1', '\2';
    s = s:gsub('[\30\31].', '')
         :gsub('\239\39', '{'):gsub('\239\40', '}')
         :gsub('\253......\253', '{...}')
         :gsub('\135\178', quote_open):gsub('\135\179', quote_close)
         :gsub('\7\11', '\n\11'):gsub('\7', '\n')
         :gsub('%s+$', '');
    local opts = s:match('\11(.*)$');
    if opts then
        local list = {};
        for o in opts:gmatch('[^\n]+') do list[#list + 1] = '\3' .. o; end
        s = s:gsub('\11.*$', table.concat(list, '\n'));
    end
    local ok, u = pcall(gdi_enc.ShiftJIS_To_UTF8, gdi_enc, s, true);
    u = ok and u or s;
    return (u:gsub('\1', '\226\128\156'):gsub('\2', '\226\128\157'):gsub('\3', '      \226\128\186  '));
end

--- Show a line (also used for testing: dialogue.show('Cid', 'Hello.', true)).
function dialogue.show(name, body, prompt, seconds)
    cur = { name = name, body = body, prompt = prompt, t0 = xi_now() };
    if name then last_name = name; end
    if not prompt then cur.expire = cur.t0 + (seconds or math.max(4, math.min(12, #body / 14))); end
end

-- The last few raw lines in the dialogue-ish modes, for diagnosing (read with /xiv1ui eval).
dialogue.raw = {};
local function remember(e, mode)
    local hex = (e.message or ''):gsub('[^\32-\126]', function (c) return string.format('<%02X>', c:byte()); end);
    table.insert(dialogue.raw, string.format('%.2f m=%d inj=%s %s', xi_now(), mode, tostring(e.injected), hex));
    if #dialogue.raw > 60 then table.remove(dialogue.raw, 1); end
end

function dialogue.text_in(e)
    if e.message == nil then return; end
    local mode = bit.band(e.mode, 0xFF);
    if mode >= 140 and mode <= 152 then remember(e, mode); end
    if e.injected then return; end
    if not SPEECH[mode] and not EVENT_ONLY[mode] then return; end
    local event, idx, ent = in_event();
    if EVENT_ONLY[mode] and not event then return; end
    -- NPC chatter while you fight (e.g. battlefield bosses) stays in the log only
    if not event and idx ~= 0 and ent:GetStatus(idx) == 1 then return; end

    local s = e.message;
    -- control codes at the end of the line: 0x7F + a digit, sometimes with a byte after it (e.g. 0x7F 0x34 0x09 then
    -- 0x7F 0x31 on the San d'Oria intro). The game still needs every one of them, so all of them, from the first
    -- 0x7F on, stay in what the game gets; the window shows the text before them. A code with a byte 1-9 after it
    -- continues by itself after that many seconds; otherwise the line waits for Enter.
    local auto, suffix = nil, '';
    local body = nil;
    while true do
        -- peel codes off the end, last first: 0x7F + digit (+ a delay byte 1-9)
        local pre, code = s:match('^(.*)(\127[1-7][\1-\9])$');
        if pre == nil then pre, code = s:match('^(.*)(\127[1-7])$'); end
        if pre == nil then break; end
        local n = code:byte(3);
        if n and auto == nil then auto = n; end
        s, suffix, body = pre, code .. suffix, pre;
    end
    local waits = body ~= nil and auto == nil;

    s = s:gsub('^[\30\31].', '');
    local name, rest = s:match('^([^:]-) : (.*)$');
    if name and #name > 0 and #name < 32 then s = rest; else name = nil; end
    local str = clean(s);
    if str == '' then
        -- the game follows each NPC line with empty ones (just a colour reset): ignore those; a blank line with an
        -- auto-continue code clears the window (scene changes)
        if auto then cur = nil; end
        return;
    end
    dialogue.show(name and clean(name) or nil, str, waits, auto and math.max(auto, 3) or nil);
    -- the line lives in the dialogue window only: the log gets just the prompt code (which the game still needs)
    e.message_modified = suffix;
end

--- Continue (Enter / Esc / confirm / cancel): the game moves on by itself; the box just closes.
function dialogue.advance()
    if cur and AshitaCore:GetChatManager():IsInputOpen() == 0 then cur = nil; end
end

function dialogue.key(e)
    local down = bit.band(e.lparam, 0x80000000) == 0;
    if down and (e.wparam == 0x0D or e.wparam == 0x1B) then dialogue.advance(); end
end

-- XInput button ids: 12 A, 13 B
function dialogue.pad(e)
    if (e.state or 0) ~= 0 and (e.button == 12 or e.button == 13) then dialogue.advance(); end
end

function dialogue.packet(e)
    if e.id == 0x00B then cur, last_name = nil, nil;                  -- zoning out (no speaker carries over)
    elseif e.id == 0x052 and #e.data >= 5 and e.data:byte(5) == 0 then cur = nil; end   -- conversation over
end

function dialogue.packet_out(e)
    if e.id ~= 0x05B or #e.data < 0x10 then return; end
    -- dialogue option chosen: close unless it opened a further menu (0x0E = still in a menu)
    local in_menu = e.data:byte(0x0E + 1) + e.data:byte(0x0E + 2) * 256;
    if in_menu == 0 then cur = nil; end
end

-- The speaker's name plate above the window's top-left corner.
local function name_plate(name, x, y, a, white)
    if name_obj.settings.text ~= name then text.set(name_obj, name); end
    local nw = text.size(name_obj);
    local pw, ph = layout.size('dlg_name');
    draw.nine('dlg_name', x + 6, y - ph + 2, math.max(150, nw + 44), ph, 14, pw, ph, white);
    name_obj:set_opacity(a);
    text.draw(name_obj, name, x + 24, y - 4, 'baseline');
end

-- A choice menu: the question, then the options with the gold cursor on the game's current choice.
local function render_choice(m)
    apply_style();
    if q_obj.settings.text ~= m.question then text.set(q_obj, m.question); end
    local _, qh = text.size(q_obj);
    if m.question == '' then qh = 0; end
    local shown = math.min(#m.rows, MAX_SHOWN);
    local first = math.max(1, math.min(m.cursor - math.floor(shown / 2), #m.rows - shown + 1));
    local ROW_H = math.max(ROW_H, style_size + 12);          -- (taller rows for larger text)
    local h = PAD_Y + qh + (qh > 0 and 10 or 0) + shown * ROW_H + PAD_Y - 4;
    local x, y = layout.anchor('bottom', W, h, 0, -215, 'dialogue');
    layout.bounds('dialogue', x, y - 24, W, h + 24);

    local bw, bh = layout.size('dlg_box');
    draw.nine('dlg_box', x - EDGE / 2, y - EDGE / 2, W + EDGE, h + EDGE, EDGE, bw, bh);
    if last_name then name_plate(last_name, x, y, 1, 0xFFFFFFFF); end
    if qh > 0 then text.render(q_obj, x + PAD_X, y + PAD_Y - 4); end

    local ry = y + PAD_Y + qh + (qh > 0 and 10 or 0);
    local sw, sh = layout.size('row_sel');
    for i = first, first + shown - 1 do
        local o = row_objs[i - first + 1];
        if o == nil then
            o = text.new('small', { font_height = 19 });
            row_objs[i - first + 1] = o;
            style_obj(o, style_size - 1);
        end
        local sel = (i == m.cursor);
        if sel then
            draw.nine('row_sel', x + PAD_X + 8, ry, W - 2 * PAD_X - 8, ROW_H - 4, 6, sw, sh, 0x90FFFFFF);
            draw.image('cursor_gold', x + PAD_X - 18, ry + ROW_H / 2 - 12);
        end
        o:set_font_color(sel and 0xFFFFFFFF or 0xFFC8C4B8);
        text.draw(o, m.rows[i], x + PAD_X + 20, ry + ROW_H - 10, 'baseline');
        ry = ry + ROW_H;
    end
    -- more options above / below
    if first > 1 then draw.image('dlg_arrow', x + W - PAD_X - 6, y + PAD_Y + qh, { rot = math.pi }); end
    if first + shown - 1 < #m.rows then draw.image('dlg_arrow', x + W - PAD_X - 6, ry - 10); end
end

dialogue.shown = false;      -- drawn this frame (others place themselves above it: layout.widgets.dialogue)
function dialogue.render()
    dialogue.shown = false;
    -- a line waiting for a key, but no event is running: nothing will continue it (the conversation ended
    -- without the game saying so), so it goes after a reading pause
    if cur and cur.prompt and not cur.expire and not in_event() and xi_now() - cur.t0 > 2 then
        cur.expire = xi_now() + math.max(3, math.min(10, #cur.body / 16));
    end
    -- the game's own message window is hidden only while xiv1ui's box shows the text (a line xiv1ui didn't catch
    -- must stay readable in the game's window)
    local ours = store.data.choice_menu ~= false and (cur ~= nil or choice.read() ~= nil);
    if ours then hider:hide(EVENT_WINDOWS); elseif hider:active() then hider:restore(); end
    local m = choice.tick(store.data.choice_menu ~= false);
    if m then render_choice(m); dialogue.shown = true; return; end
    if cur == nil then return; end
    local now = xi_now();
    if cur.expire and now > cur.expire then cur = nil; return; end

    apply_style();
    if body_obj.settings.text ~= cur.body then text.set(body_obj, cur.body); end
    local _, th = text.size(body_obj);
    local h = math.max(MIN_H, th + 2 * PAD_Y + 8);
    local x, y = layout.anchor('bottom', W, h, 0, -215, 'dialogue');
    layout.bounds('dialogue', x, y - 24, W, h + 24);
    dialogue.shown = true;

    -- quick fade in, and out over the last half second of a timed line
    local a = math.min(1, (now - cur.t0) / 0.15);
    if cur.expire then a = math.min(a, (cur.expire - now) / 0.5); end
    local white = draw.alpha(0xFFFFFFFF, a);

    local bw, bh = layout.size('dlg_box');
    draw.nine('dlg_box', x - EDGE / 2, y - EDGE / 2, W + EDGE, h + EDGE, EDGE, bw, bh, white);

    if cur.name then name_plate(cur.name, x, y, a, white); end

    body_obj:set_opacity(a);
    text.render(body_obj, x + PAD_X, y + PAD_Y - 4);

    if cur.prompt then
        local bob = math.floor(math.abs(math.sin((now - cur.t0) * 4)) * 3 + 0.5);
        draw.image('dlg_arrow', x + W - PAD_X - 6, y + h - PAD_Y - 6 + bob, { color = white });
    end
end

return dialogue;
