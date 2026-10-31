--[[
* xiv1ui - a single-line text field for xiv1ui's own windows (macro names and lines). While a field is being edited
* it takes every key from the game: characters are translated with the current keyboard layout (ToUnicode), Enter
* accepts, Esc cancels, Backspace / Delete / Left / Right / Home / End edit. Text is kept as UTF-8.
*
*   textinput.begin(initial, on_done)   on_done(text) on Enter, on_done(nil) on Esc
*   textinput.active()                  true while editing
*   textinput.key(e)                    from the 'key' event; returns true if the key was used (block it)
*   textinput.text(), textinput.caret()
--]]

local ffi = require('ffi');
local bit = require('bit');

pcall(ffi.cdef, [[
int __stdcall GetKeyboardState(uint8_t* state);
int __stdcall ToUnicode(uint32_t vk, uint32_t scan, const uint8_t* state, uint16_t* buf, int size, uint32_t flags);
]]);
local user32 = ffi.load('user32');

local ti = {};

local cur = nil;      -- { chars = { utf8 strings }, caret = 0.., done = fn }
local kstate = ffi.new('uint8_t[256]');
local wbuf = ffi.new('uint16_t[8]');

local function utf8(cp)
    if cp < 0x80 then return string.char(cp); end
    if cp < 0x800 then return string.char(0xC0 + bit.rshift(cp, 6), 0x80 + bit.band(cp, 0x3F)); end
    return string.char(0xE0 + bit.rshift(cp, 12), 0x80 + bit.band(bit.rshift(cp, 6), 0x3F), 0x80 + bit.band(cp, 0x3F));
end

function ti.begin(initial, on_done)
    local chars = {};
    for ch in (initial or ''):gmatch('[%z\1-\127\194-\244][\128-\191]*') do chars[#chars + 1] = ch; end
    -- the on-screen keyboard only when the field was opened from the controller; with a keyboard you just type
    cur = { chars = chars, caret = #chars, done = on_done, osk = require('core.ui').via_pad == true };
end

--- True while the field being edited uses the on-screen keyboard (it was opened from the controller).
function ti.osk() return cur ~= nil and cur.osk; end

function ti.active() return cur ~= nil; end
function ti.text() return cur and table.concat(cur.chars) or ''; end
function ti.caret() return cur and cur.caret or 0; end
function ti.before_caret() return cur and table.concat(cur.chars, '', 1, cur.caret) or ''; end

local function finish(ok)
    local c = cur;
    cur = nil;
    if c and c.done then c.done(ok and table.concat(c.chars) or nil); end
end

function ti.key(e)
    if cur == nil then return false; end
    local down = bit.band(e.lparam, 0x80000000) == 0;
    if not down then return true; end
    local vk = e.wparam;
    if vk == 0x0D then finish(true);
    elseif vk == 0x1B then finish(false);
    elseif vk == 0x08 then
        if cur.caret > 0 then table.remove(cur.chars, cur.caret); cur.caret = cur.caret - 1; end
    elseif vk == 0x2E then
        if cur.caret < #cur.chars then table.remove(cur.chars, cur.caret + 1); end
    elseif vk == 0x25 then cur.caret = math.max(0, cur.caret - 1);
    elseif vk == 0x27 then cur.caret = math.min(#cur.chars, cur.caret + 1);
    elseif vk == 0x24 then cur.caret = 0;
    elseif vk == 0x23 then cur.caret = #cur.chars;
    else
        user32.GetKeyboardState(kstate);
        local scan = bit.band(bit.rshift(e.lparam, 16), 0xFF);
        local n = user32.ToUnicode(vk, scan, kstate, wbuf, 8, 0);
        for i = 0, n - 1 do
            local cp = wbuf[i];
            if cp >= 0x20 and #cur.chars < 60 then
                table.insert(cur.chars, cur.caret + 1, utf8(cp));
                cur.caret = cur.caret + 1;
            end
        end
    end
    return true;
end

-- On-screen keyboard (for the controller: the D-pad moves, A types, RB switches case, B deletes). The controller's
-- presses reach xiv1ui windows as arrow / Enter / Esc / Tab keys (core/pad.lua); real keyboard keys go through
-- ti.key above and never get here.
local ROWS_LOWER = { '1234567890', 'qwertyuiop', 'asdfghjkl/', "zxcvbnm<>'", '.,-!?:()@#' };
local ROWS_UPPER = { '1234567890', 'QWERTYUIOP', 'ASDFGHJKL/', 'ZXCVBNM<>"', '.,_!?;[]+=' };
local ACTIONS = { 'Aa', 'Space', 'Delete', 'Done' };
local osk = { r = 2, c = 1, upper = false };

local function osk_rows() return osk.upper and ROWS_UPPER or ROWS_LOWER; end

local function insert(ch)
    if cur and #cur.chars < 60 then table.insert(cur.chars, cur.caret + 1, ch); cur.caret = cur.caret + 1; end
end

--- A navigation key from the controller while editing (VK codes). Returns true (always consumed).
function ti.pad(vk)
    if cur == nil then return false; end
    local rows = osk_rows();
    local nrows = #rows + 1;                       -- + the action row
    local function width(r) return r > #rows and #ACTIONS or #rows[r]; end
    if vk == 0x26 then osk.r = (osk.r - 2) % nrows + 1; osk.c = math.min(osk.c, width(osk.r));
    elseif vk == 0x28 then osk.r = osk.r % nrows + 1; osk.c = math.min(osk.c, width(osk.r));
    elseif vk == 0x25 then osk.c = (osk.c - 2) % width(osk.r) + 1;
    elseif vk == 0x27 then osk.c = osk.c % width(osk.r) + 1;
    elseif vk == 0x09 then osk.upper = not osk.upper;
    elseif vk == 0x1B then
        if cur.caret > 0 then table.remove(cur.chars, cur.caret); cur.caret = cur.caret - 1; end
    elseif vk == 0x0D then
        if osk.r > #rows then
            local a = ACTIONS[osk.c];
            if a == 'Aa' then osk.upper = not osk.upper;
            elseif a == 'Space' then insert(' ');
            elseif a == 'Delete' then if cur.caret > 0 then table.remove(cur.chars, cur.caret); cur.caret = cur.caret - 1; end
            elseif a == 'Done' then finish(true); end
        else
            insert(rows[osk.r]:sub(osk.c, osk.c));
        end
    end
    return true;
end

--- Draw the on-screen keyboard with its top-left at x, y (HUD units).
function ti.draw_osk(x, y)
    if cur == nil or not cur.osk then return; end
    local draw, text, layout, ui = require('core.draw'), require('core.text'), require('core.layout'), require('core.ui');
    local rows = osk_rows();
    local KW, KH = 38, 36;
    local w, h = 10 * KW + 28, (#rows + 1) * KH + 60;
    local bw, bh = layout.size('win_body');
    draw.nine('win_body', x, y, w, h, 12, bw, bh);
    draw.nine('win_body', x, y, w, h, 12, bw, bh);
    local hint = ui.label('osk_hint', 'small', { font_height = 14, font_color = 0xFFB8C0D8 });
    text.draw(hint, 'A: type   B: delete   RB: Aa   Done: keep', x + 14, y + 22, 'baseline');
    for r, line in ipairs(rows) do
        for c = 1, #line do
            local kx, ky = x + 14 + (c - 1) * KW, y + 32 + (r - 1) * KH;
            local sel = (r == osk.r and c == osk.c);
            local pw, ph = layout.size('btn_pill');
            draw.nine(sel and 'btn_pill_focus' or 'btn_pill', kx, ky, KW - 4, KH - 4, 12, pw, ph);
            local ch = line:sub(c, c);
            local o = ui.label('osk_' .. r .. '_' .. c, 'label', { font_height = 19, font_alignment = text.align.Center });
            local col = sel and 0xFFF4E070 or 0xFFE8E4D8;
            if o.settings.font_color ~= col then o:set_font_color(col); end
            text.draw(o, ch, kx + (KW - 4) / 2, ky + KH - 13, 'baseline');
        end
    end
    local ar = #rows + 1;
    local aw = (10 * KW - 4 * 4) / #ACTIONS;
    for c, a in ipairs(ACTIONS) do
        local kx, ky = x + 14 + (c - 1) * (aw + 4), y + 32 + (ar - 1) * KH;
        local sel = (osk.r == ar and osk.c == c);
        local pw, ph = layout.size('btn_pill');
        draw.nine(sel and 'btn_pill_focus' or 'btn_pill', kx, ky, aw, KH - 4, 12, pw, ph);
        local o = ui.label('osk_a' .. c, 'label', { font_height = 17, font_alignment = text.align.Center });
        local col = sel and 0xFFF4E070 or 0xFFE8E4D8;
        if o.settings.font_color ~= col then o:set_font_color(col); end
        text.draw(o, a, kx + aw / 2, ky + KH - 13, 'baseline');
    end
end

return ti;
