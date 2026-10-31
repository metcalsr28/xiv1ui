--[[
* xiv1ui - the game's small yes / no window ("menu    comyn": "Heading outside, kupo?", "Log out?", "Return to Home
* Point?" ...) as an xiv1ui dialogue: the question and two buttons, the selected one glowing. The game still runs the
* window (Left / Right / confirm / cancel work as before); a click on a button moves its cursor and confirms.
* While the knocked-out screen is up it draws the question itself (ui/deathscreen.lua), so this one stands aside.
*
* The question is a string the window's class object points to at +0x1C; the cursor is the window's +0x4C
* (1 Yes, 2 No).
--]]

local draw    = require('core.draw');
local text    = require('core.text');
local layout  = require('core.layout');
local ui      = require('core.ui');
local store   = require('core.store');
local mem     = require('core.mem');
local gamewin = require('core.gamewin');
local xi_now  = require('core.now');

local confirm = {};

local hider = gamewin.new();
local since = nil;
local buttons, hover = {}, nil;

function confirm.release() hider:restore(); end

local function question()
    local w = gamewin.window('comyn');
    if w == nil then return nil; end
    local slot = gamewin.slot('comyn');
    local cls = slot and mem.u32(slot);
    local p = cls and mem.u32(cls + 0x1C);
    local txt = (p and mem.ok(p, 8)) and (ashita.memory.read_string(p, 160) or ''):match('^[^%z]*') or '';
    local c = mem.u32(w + 0x4C);
    if txt == '' or c == nil or c < 1 or c > 2 then return nil; end
    -- the game's text can carry a speaker ("Moogle: Heading outside, kupo?") and line breaks
    local who, rest = txt:match('^([%w%.\' ]-)%s*:%s*(.+)$');
    if who and #who < 24 then txt = rest; else who = nil; end
    txt = txt:gsub('[\7\10]', ' '):gsub('%s+', ' ');
    local ok, u = pcall(require('gdifonts.encoding').ShiftJIS_To_UTF8, require('gdifonts.encoding'), txt, true);
    return { who = who, text = ok and u or txt, cursor = c };
end

function confirm.mouse(e)
    if #buttons == 0 then hover = nil; return; end
    local hit = nil;
    for _, b in ipairs(buttons) do
        if e.x >= b[1] and e.x < b[1] + b[3] and e.y >= b[2] and e.y < b[2] + b[4] then hit = b; end
    end
    if e.message == 0x200 then hover = hit and hit[5] or nil; return; end
    if hit == nil then return; end
    if e.message == 0x201 then e.blocked = true;
    elseif e.message == 0x202 then
        e.blocked = true;
        local gamein = require('ui.gamein');
        local d = hit[5] - hit[6];
        for _ = 1, math.abs(d) do gamein.press(d > 0 and 0xCD or 0xCB); end
        gamein.press(0x1C);
    end
end

function confirm.render()
    buttons = {};
    local q = store.data.cmd_menu ~= false and gamewin.window('dead') == nil and question() or nil;
    if q == nil then
        if hider:active() then hider:restore(); end
        since, hover = nil, nil;
        return;
    end
    hider:hide({ 'comyn' });
    local now = xi_now();
    since = since or now;
    local a = math.min(1, (now - since) / 0.15);

    local W, H = 460, 150;
    local x, y = layout.anchor('bottom', W, H, 0, -230, 'confirm');
    layout.bounds('confirm', x, y, W, H);
    local bw, bh = layout.size('dlg_box');
    draw.nine('dlg_box', x - 16, y - 16, W + 32, H + 32, 32, bw, bh, draw.alpha(0xFFFFFFFF, a));
    if q.who then
        local nw, nh = layout.size('dlg_name');
        local name = ui.label('confirm_who', 'label', { font_height = 16, font_color = 0xFFE6DCC0 });
        draw.nine('dlg_name', x + 6, y - nh + 2, 150, nh, 14, nw, nh, draw.alpha(0xFFFFFFFF, a));
        text.draw(name, q.who, x + 24, y - 4, 'baseline');
    end
    local qt = ui.label('confirm_q', 'small', { font_height = 21, font_color = 0xFFF8F6F0, font_alignment = text.align.Center });
    qt:set_opacity(a);
    text.draw(qt, q.text, x + W / 2, y + 44, 'baseline');

    local gw, gh = layout.size('button_glow');
    local wbw, wbh = layout.size('wide_button');
    local BW = 170;
    for i, label in ipairs({ 'Yes', 'No' }) do
        local px, py = x + W / 2 - BW - 10 + (i - 1) * (BW + 20), y + 78;
        local sel = (q.cursor == i);
        buttons[#buttons + 1] = { px, py, BW, wbh, i, q.cursor };
        local glow = sel and (0.75 + 0.25 * math.sin(now * 3)) or (hover == i and 0.5 or 0);
        if glow > 0 then
            local sx = (BW + gw - wbw) / gw;
            for _ = 1, sel and 2 or 1 do
                draw.image('button_glow', px - (gw * sx - BW) / 2, py - (gh - wbh) / 2,
                    { scale = { sx, 1 }, color = draw.alpha(0xFFFFFFFF, a * glow) });
            end
        end
        draw.image('wide_button', px, py, { scale = { BW / wbw, 1 },
            color = draw.alpha(sel and 0xFFFFFFFF or 0xFF9A9A9A, a * (sel and 1 or 0.7)) });
        local t = ui.label('confirm_b' .. i, 'label', { font_height = 20, font_alignment = text.align.Center });
        local col = sel and 0xFFFFF4E4 or 0xFFB8B0A8;
        if t.settings.font_color ~= col then t:set_font_color(col); end
        t:set_opacity(a);
        text.draw(t, label, px + BW / 2, py + wbh / 2 + 7, 'baseline');
    end
end

return confirm;
