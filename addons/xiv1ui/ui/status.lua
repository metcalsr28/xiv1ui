--[[
* xiv1ui - your status effects, after FFXIV 1.0 (reference §14): a row of unframed icons in the upper middle of the
* screen (below the target frame), each with an "MM:SS" timer centred under it in small white italic. Hovering an
* icon outlines it and shows its name. Right-click cancels it, using the game's own /cancel command.
--]]

local xi_now = require('core.now');
local draw   = require('core.draw');
local text   = require('core.text');
local layout = require('core.layout');

local status = {};

local ICON = 28;
local STEP = 38;
local MAX  = 32;

local timers, names = {}, {};
local hover = nil;
local rects = {};
local tipname;

function status.init()
    for i = 1, MAX do timers[i] = text.new('timer', { font_height = 14, font_alignment = text.align.Center }); end
    tipname = text.new('name', { font_height = 20 });
end

-- FFXI status timers are expiry times in 1/60 s ticks since the Vana'diel epoch, wrapped to 32 bits. Remaining time
-- = expiry - now (both mod 2^32). Verified in game: Berserk read 172 s right after use (it lasts 180 s).
local function remaining(raw)
    if raw == nil or raw == 0 or raw == 0xFFFFFFFF then return nil; end
    local now = (require('core.clock').now() - 1009810800) * 60;   -- FFXI's epoch, in 1/60 s ticks
    local left = raw - (now % 0x100000000);
    if left < 0 then left = left + 0x100000000; end
    left = left / 60;
    if left > 86400 then return nil; end                   -- not a countdown (permanent effects)
    return left;
end

local function list()
    local p = AshitaCore:GetMemoryManager():GetPlayer();
    local ids, tm = p:GetStatusIcons(), p:GetStatusTimers();
    local out = {};
    for i = 1, MAX do
        local id = ids[i];
        if id and id ~= 255 and id ~= 0 then out[#out + 1] = { id = id, left = remaining(tm[i]) }; end
    end
    return out;
end

local combo_obj, combo_name;

-- 1.0's combo indicator (reference §14): a pink glowing glyph with a timer in the upper middle of the screen. Here it
-- shows the skillchain window opened by a party weapon skill on your target.
local function draw_combo(x, y)
    local left = require('core.world').combo_left();
    if not left then return; end
    combo_obj = combo_obj or text.new('timer', { font_height = 15, font_alignment = text.align.Center });
    combo_name = combo_name or text.new('label', { font_height = 15, font_color = 0xFFFFB4E6, font_alignment = text.align.Center });
    local pulse = 0.6 + 0.4 * math.abs(math.sin(xi_now() * 5));
    draw.image('slot_glow', x - 36, y - 36, { scale = 1.0, color = draw.alpha(0xFFFF6EC8, pulse) });
    draw.image('disc_weaponskill', x - 22, y - 22, { color = 0xFFFFC8F0 });
    draw.image('slot_ring_pink', x - 30, y - 30);
    text.draw(combo_name, 'Skillchain', x, y + 46, 'baseline');
    local s = math.ceil(left);
    text.draw(combo_obj, string.format('00:%02d', s), x, y + 64, 'baseline');
end

function status.render()
    local sw = layout.screen();
    draw_combo(sw / 2 + 300, 150);
    local fx = list();
    rects = {};
    if #fx == 0 then return; end
    local W = #fx * STEP;
    local x0, y = layout.anchor('top', W, 0, 0, 118, 'status');
    layout.bounds('status', x0, y, W, 50);
    local hovered;
    for i, f in ipairs(fx) do
        local x = x0 + (i - 1) * STEP + (STEP - ICON) / 2;
        rects[i] = { x, y, ICON, ICON, f.id };
        local icon = draw.status_icon(f.id);
        if hover == i then
            draw.image('slot_glow', x - 22, y - 22, { scale = 0.75, color = 0xFF8CC8FF });   -- blue outline on hover (1.16)
            hovered = f;
        end
        draw.entry(icon, x, y, ICON, ICON);
        if f.left then
            local s = math.floor(f.left);
            text.draw(timers[i], string.format('%02d:%02d', math.floor(s / 60), s % 60), x + ICON / 2, y + ICON + 14, 'baseline');
        end
    end
    if hovered then
        local name = AshitaCore:GetResourceManager():GetString('buffs', hovered.id) or '';
        text.draw(tipname, name, x0, y + ICON + 36, 'baseline');
    end
end

local function hit(x, y)
    for i, r in ipairs(rects) do
        if x >= r[1] and x < r[1] + r[3] and y >= r[2] and y < r[2] + r[4] then return i, r[5]; end
    end
end

function status.mouse(e)
    local i, id = hit(e.x, e.y);
    if e.message == 0x200 then hover = i; return; end
    if not i then return; end
    if e.message == 0x204 then e.blocked = true;                                 -- WM_RBUTTONDOWN
    elseif e.message == 0x205 then                                               -- WM_RBUTTONUP: cancel the buff
        e.blocked = true;
        AshitaCore:GetChatManager():QueueCommand(1, '/cancel ' .. id);
    end
end

return status;
