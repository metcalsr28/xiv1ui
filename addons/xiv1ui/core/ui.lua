--[[
* xiv1ui - window framework for menus and windows in the FFXIV 1.0 style (reference §2).
*
* A window is a table: { id, title, w, h, x, y, style = 'menu'|'hud', draw = fn(win, x, y), key = fn(win, vk) -> bool,
*                        click = fn(win, mx, my, button) -> bool, wheel = fn(win, delta), close = fn(win) }
* x/y may be nil (the window is centred). ui.open/close manage a stack; the top window has keyboard focus.
* Keyboard: arrows/Enter/Escape/Tab go to the focused window while the game's chat input is closed.
--]]

local draw   = require('core.draw');
local text   = require('core.text');
local layout = require('core.layout');

local ui = {};

local stack = {};             -- open windows, last = top / focused
local title_objs = {};
local row_objs = {};          -- shared pool of row text objects by key
local rects = {};             -- id -> { x, y, w, h } of the last drawn frame

ui.VK = { LEFT = 0x25, UP = 0x26, RIGHT = 0x27, DOWN = 0x28, RETURN = 0x0D, ESCAPE = 0x1B, TAB = 0x09,
          HOME = 0x24, PRIOR = 0x21, NEXT = 0x22, BACK = 0x08, DELETE = 0x2E };

function ui.is_open(id)
    for _, w in ipairs(stack) do if w.id == id then return true; end end
    return false;
end

function ui.top() return stack[#stack]; end
function ui.any_open() return #stack > 0; end

function ui.open(win)
    ui.close(win.id);
    stack[#stack + 1] = win;
    if win.on_open then win.on_open(win); end
end

function ui.close(id)
    for i = #stack, 1, -1 do
        if stack[i].id == id then
            local w = table.remove(stack, i);
            if w.on_close then w.on_close(w); end
        end
    end
end

function ui.close_all()
    while #stack > 0 do ui.close(stack[#stack].id); end
end

function ui.toggle(win)
    if ui.is_open(win.id) then ui.close(win.id); else ui.open(win); end
end

--- A reusable text object for a key (so rows don't re-create textures every frame).
function ui.label(key, style, overrides)
    local o = row_objs[key];
    if o == nil then
        o = text.new(style or 'small', overrides);
        row_objs[key] = o;
    end
    return o;
end

-- Window chrome --------------------------------------------------------------------------------

local function chrome(win, x, y)
    local w, h = win.w, win.h;
    if win.style == 'hud' then
        local cw, ch = layout.size('win_hud');
        draw.nine('win_hud', x, y, w, h, 10, cw, ch);
    else
        local cw, ch = layout.size('win_body');
        draw.nine('win_body', x, y, w, h, 12, cw, ch);
    end
    if win.title then
        if win.style ~= 'hud' then
            local tw, th = layout.size('win_title');
            draw.nine('win_title', x + 4, y + 4, w - 8, 30, 10, tw, th);
            draw.image('title_swash', x + 8, y + 4);
        end
        local t = ui.label('title:' .. win.id, 'name', { font_height = 22 });
        text.draw(t, win.title, x + 40, y + 27, 'baseline');
        if win.style ~= 'hud' then
            local c = ui.label('close:' .. win.id, 'label', { font_height = 18, font_alignment = text.align.Right });
            text.draw(c, '×', x + w - 12, y + 26, 'baseline');
        end
    end
end

function ui.render()
    for _, win in ipairs(stack) do
        local sw, sh = layout.screen();
        local x = win.x or math.floor((sw - win.w) / 2);
        local y = win.y or math.floor((sh - win.h) / 2 - 40);
        if type(win.x) == 'function' then x, y = win.x(win); end
        rects[win.id] = { x, y, win.w, win.h };
        chrome(win, x, y);
        if win.draw then
            local ok, err = pcall(win.draw, win, x, y);
            if not ok then print('[xiv1ui] ' .. win.id .. ': ' .. tostring(err)); ui.close(win.id); end
        end
    end
end

-- Widgets --------------------------------------------------------------------------------------

--- A vertical list with the 1.0 selection look (lighter blue row + gold cursor at its left).
-- items: array of { label = string, color = ARGB?, right = string?, disabled = bool?, indent = px? }
-- (gdifonts drops leading spaces, so use `indent` to leave room for an icon.)
-- Returns the row rects (for clicks). `first` is the scroll offset, `rows` how many fit.
function ui.list(win, key, items, sel, x, y, w, row_h, rows, first, focused)
    local out = {};
    local sw, sh = layout.size('row_sel');
    first = first or 0;
    for r = 1, math.min(rows, #items - first) do
        local i = r + first;
        local it = items[i];
        local ry = y + (r - 1) * row_h;
        if i == sel then
            draw.nine('row_sel', x, ry, w, row_h - 2, 6, sw, sh, focused and 0xFFFFFFFF or 0x90FFFFFF);
            if focused then draw.image('cursor_gold', x - 26, ry + (row_h - 22) / 2); end
        end
        local col = it.disabled and 0xFF808488 or (it.color or 0xFFF4F0E6);
        local o = ui.label(key .. ':' .. r, 'small', { font_height = 17 });
        if o.settings.font_color ~= col then o:set_font_color(col); end
        text.draw(o, it.label, x + 10 + (it.indent or 0), ry + row_h - 7, 'baseline');
        if it.right then
            local ro = ui.label(key .. ':r' .. r, 'small', { font_height = 16, font_alignment = text.align.Right });
            if ro.settings.font_color ~= col then ro:set_font_color(col); end
            text.draw(ro, it.right, x + w - 8, ry + row_h - 7, 'baseline');
        end
        out[r] = { x, ry, w, row_h, i };
    end
    return out;
end

--- A pill button. Returns its rect.
function ui.button(key, label, x, y, w, focused)
    local pw, ph = layout.size('btn_pill');
    draw.nine(focused and 'btn_pill_focus' or 'btn_pill', x, y, w, 26, 12, pw, ph);
    local o = ui.label('btn:' .. key, 'small', { font_height = 16, font_alignment = text.align.Center });
    text.draw(o, label, x + w / 2, y + 19, 'baseline');
    return { x, y, w, 26 };
end

--- Section header: gold diamond, italic text, thin rule.
function ui.header(key, label, x, y, w)
    draw.image('leader_diamond', x, y - 11);
    local o = ui.label('hdr:' .. key, 'label', { font_height = 18, font_color = 0xFFF4EBD0 });
    text.draw(o, label, x + 18, y, 'baseline');
    draw.image('name_rule', x - 4, y + 2, { scale = { w / 300, 1 } });
end

function ui.hit(r, mx, my)
    return r and mx >= r[1] and mx < r[1] + r[3] and my >= r[2] and my < r[2] + r[4];
end

-- Input ----------------------------------------------------------------------------------------

local function chat_open()
    local ok, v = pcall(function () return AshitaCore:GetChatManager():IsInputOpen(); end);
    return ok and v and v ~= 0 and v ~= false;
end

--- True while an xiv1ui window has the keyboard (the same test ui.key uses): the arrow keys, Enter, Tab and Page
-- Up / Down then belong to it, and the game mustn't see them in its DirectInput state either (Up / Down there tilt
-- the camera in fixed steps).
function ui.has_keys()
    if #stack == 0 or chat_open() then return false; end
    local win = stack[#stack];
    return win.key ~= nil;
end

-- DirectInput codes of those keys (main block and numpad)
local NAV_DIK = { 0xC8, 0xD0, 0xCB, 0xCD, 0x1C, 0x9C, 0x0F, 0xC9, 0xD1, 0x48, 0x50, 0x4B, 0x4D };

--- key_state event: clear the keys an open xiv1ui window uses from the game's keyboard state.
function ui.key_state(e)
    if not ui.has_keys() then return; end
    local p = require('ffi').cast('uint8_t*', e.data_raw);
    for _, k in ipairs(NAV_DIK) do p[k] = 0; end
end

--- key_data event (DirectInput's buffered key events, a second way the game reads the keyboard): the same keys
-- are kept from it while a window has the keyboard.
local NAV_SET = {};
for _, k in ipairs(NAV_DIK) do NAV_SET[k] = true; end
function ui.key_data(e)
    if NAV_SET[e.key] and ui.has_keys() then e.blocked = true; end
end

--- key event: returns true when consumed.
function ui.key(e)
    if #stack == 0 or chat_open() then return false; end
    local up = bit.band(e.lparam, 0x80000000) ~= 0;
    local vk = e.wparam;
    local win = stack[#stack];
    local handled = false;
    if vk == ui.VK.ESCAPE then
        if not up then
            if not (win.key and win.key(win, vk)) then ui.close(win.id); end
        end
        handled = true;
    elseif win.key and (vk == ui.VK.UP or vk == ui.VK.DOWN or vk == ui.VK.LEFT or vk == ui.VK.RIGHT
            or vk == ui.VK.RETURN or vk == ui.VK.TAB or vk == ui.VK.PRIOR or vk == ui.VK.NEXT) then
        if not up then win.key(win, vk); end
        handled = true;
    end
    return handled;
end

--- mouse event: windows get clicks inside them (top first); returns true when consumed.
function ui.mouse(e)
    for i = #stack, 1, -1 do
        local win = stack[i];
        local r = rects[win.id];
        if ui.hit(r, e.x, e.y) then
            if e.message == 0x201 or e.message == 0x204 then
                -- bring to front
                if i ~= #stack then table.remove(stack, i); stack[#stack + 1] = win; end
                return true;
            elseif e.message == 0x202 or e.message == 0x205 then
                -- close box
                if win.style ~= 'hud' and e.x > r[1] + r[3] - 30 and e.y < r[2] + 34 then ui.close(win.id); return true; end
                if win.click then win.click(win, e.x, e.y, e.message == 0x202 and 1 or 2); end
                return true;
            elseif e.message == 0x20A then
                if win.wheel then win.wheel(win, e.delta or 0); end
                return true;
            elseif e.message == 0x200 then
                if win.hover then win.hover(win, e.x, e.y); end
                return false;
            end
            return true;
        end
    end
    return false;
end

return ui;
