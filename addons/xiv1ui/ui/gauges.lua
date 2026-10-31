--[[
* xiv1ui - HP / MP / TP gauges (bottom centre, under the action bar), as in FFXIV 1.0:
* a small italic label at the left of each bar and a large italic numeral right-aligned above it.
* Values ease toward their targets so changes animate instead of jumping.
--]]

local xi_now = require('core.now');
local draw    = require('core.draw');
local text    = require('core.text');
local layout  = require('core.layout');

local gauges = { replaces = { 'gauges' } };     -- FFXI's small HP / MP / TP box (shown while engaged)

local BARS = {
    { key = 'hp', label = 'HP', fill = 'gauge_fill_hp' },
    { key = 'mp', label = 'MP', fill = 'gauge_fill_mp' },
    { key = 'tp', label = 'TP', fill = 'gauge_fill_tp' },
};
local GAP = 18;          -- space between bars

local shown = { hp = 0, mp = 0, tp = 0 };   -- animated fill fractions
local labels, numerals = {}, {};
local last_t = xi_now();

function gauges.init()
    for i, b in ipairs(BARS) do
        labels[i]   = text.new('label', { font_height = 16, font_color = 0xFFF0DCA0 });   -- pale gold
        numerals[i] = text.new('numeral', { font_alignment = text.align.Right });
    end
end

local function values()
    local mm    = AshitaCore:GetMemoryManager();
    local party = mm:GetParty();
    local p     = mm:GetPlayer();
    local hp, mp, tp = party:GetMemberHP(0), party:GetMemberMP(0), party:GetMemberTP(0);
    local hpm, mpm = p:GetHPMax(), p:GetMPMax();
    return {
        hp = { hp, hpm > 0 and hp / hpm or 0 },
        mp = { mp, mpm > 0 and mp / mpm or 0 },
        tp = { tp, tp / 3000 },
    };
end

function gauges.render()
    local now = xi_now();
    local dt = math.min(0.1, now - last_t);
    last_t = now;

    local v = values();
    local tw, th = layout.size('gauge_track');
    local total = #BARS * tw + (#BARS - 1) * GAP;
    local x0, y = layout.anchor('bottom', total, 0, 0, -64, 'gauges');
    layout.bounds('gauges', x0 - 8, y - 30, total + 16, 54);

    for i, b in ipairs(BARS) do
        local x = x0 + (i - 1) * (tw + GAP);
        local val, frac = v[b.key][1], math.max(0, math.min(1, v[b.key][2]));
        -- ease toward the real value (fast enough to feel live, slow enough to read)
        shown[b.key] = shown[b.key] + (frac - shown[b.key]) * math.min(1, dt * 8);

        -- navy swoosh under the left end carries the label; the numeral sits at the right end
        draw.image('gauge_swoosh', x - 8, y + 2);
        draw.image('gauge_track', x, y);
        local fw = math.floor(tw * shown[b.key] + 0.5);
        if fw > 0 then
            draw.image(b.fill, x, y, { sw = fw });
            -- bright tick at the fill edge while not full
            if fw < tw - 8 then
                draw.image('gauge_tip', x + fw - 4, y + 1, { color = 0xC0FFFFFF });
            end
        end
        text.draw(labels[i], b.label, x + 6, y + 21, 'baseline');
        text.draw(numerals[i], tostring(val), x + tw - 8, y - 1, 'baseline');
    end
end

return gauges;
