--[[
* xiv1ui - cast bar, after FFXIV 1.0 (reference §8): the spell's disc in a round silver socket at the left, then a
* steel-blue tube with a bevelled silver rim, the spell name in white italic inside it, a bright tick at the fill
* edge, and a navy pennant swoosh under the left end. Shown above the action bar while casting.
--]]

local xi_now = require('core.now');
local draw    = require('core.draw');
local text    = require('core.text');
local layout  = require('core.layout');
local world   = require('core.world');
local actions = require('core.actions');

local castbar = { replaces = { 'castbar' } };

local name_obj, glyph_obj;
local ELEMENT = { [0] = 'fire', 'ice', 'wind', 'earth', 'thunder', 'water', 'light', 'dark' };

function castbar.init()
    name_obj  = text.new('name', { font_height = 18 });
    glyph_obj = text.new('name', { font_height = 18, font_alignment = text.align.Center });
end

function castbar.render()
    local c = world.casting;
    if c == nil then return; end
    if xi_now() - c.t > 30 then world.casting = nil; return; end

    local r = AshitaCore:GetResourceManager();
    local name, disc, icon = '', 'disc_command', nil;
    if c.kind == 8 then
        local s = r:GetSpellById(c.id);
        if s then name = s.Name[1]; disc = 'disc_' .. (ELEMENT[s.Element] or 'light'); end
    else
        local it = r:GetItemById(c.id);
        if it then name = it.Name[1]; icon = draw.item_icon(c.id); end
    end
    local pct = AshitaCore:GetMemoryManager():GetCastBar():GetPercent() or 0;
    pct = math.max(0, math.min(1, pct));

    local tw, th = layout.size('cast_track');
    local x, y = layout.anchor('bottom', tw + 50, 0, 0, -230, 'castbar');
    layout.bounds('castbar', x - 4, y - 20, tw + 54, 44);

    draw.image('gauge_swoosh', x + 30, y + 6, { scale = 1.2 });
    -- socket: a scaled-down slot with the spell's disc (or the item's icon)
    draw.image('slot_shadow', x - 4, y - 18, { scale = 0.75 });
    if icon then
        draw.entry(icon, x + 6, y - 8, 26, 26);
    else
        draw.image(disc, x + 3, y - 12, { scale = 0.75 });
        local ai = actions.icon_for(name);
        if ai then
            draw.image(ai, x + 3, y - 12, { scale = 0.75 });
        else
            text.draw(glyph_obj, actions.glyph(name), x + 19, y + 12, 'baseline');
        end
    end
    draw.image('slot_ring', x - 4, y - 18, { scale = 0.75 });

    local bx = x + 46;
    draw.image('cast_track', bx, y);
    local fw = math.floor(tw * pct + 0.5);
    if fw > 0 then draw.image('cast_fill', bx, y, { sw = fw }); end
    if fw > 4 and fw < tw - 4 then draw.image('gauge_tip', bx + fw - 4, y + 2, { color = 0xE0FFFFFF }); end
    text.draw(name_obj, name, bx + 16, y + 15, 'baseline');
end

return castbar;
