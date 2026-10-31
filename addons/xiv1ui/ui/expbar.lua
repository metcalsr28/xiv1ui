--[[
* xiv1ui - EXP bar (bottom centre, under the HP/MP/TP row), after FFXIV 1.0 (reference §8):
* a square class tile, "Warrior Level: 75" (with the support job after it), a long thin light-blue gauge, and
* "Next 1234/5000" in gold italic at the right. With limit mode on it shows limit points and merits instead.
--]]

local draw   = require('core.draw');
local text   = require('core.text');
local layout = require('core.layout');

local expbar = {};

local job_obj, abbr_obj, next_lbl, next_val;

function expbar.init()
    job_obj  = text.new('label', { font_height = 16, font_color = 0xFFF4F0E6 });
    abbr_obj = text.new('slotkey', { fixed = true, font_height = 13, font_color = 0xFFF8E6A8, font_alignment = text.align.Center });
    next_lbl = text.new('label', { font_height = 16, font_color = 0xFFF0C860 });
    next_val = text.new('label', { font_height = 16, font_color = 0xFFF4F0E6, font_alignment = text.align.Right });
end

local function job_name(id)
    local s = AshitaCore:GetResourceManager():GetString('jobs.names', id);
    return (s and s ~= '') and s or ('Job ' .. id);
end

local function job_abbr(id)
    local s = AshitaCore:GetResourceManager():GetString('jobs.names_abbr', id);
    return (s and s ~= '') and s or job_name(id):sub(1, 3):upper();
end

function expbar.render()
    local p = AshitaCore:GetMemoryManager():GetPlayer();
    local main, lvl = p:GetMainJob(), p:GetMainJobLevel();
    local sub, slvl = p:GetSubJob(), p:GetSubJobLevel();

    local cur, need, label;
    if p:GetIsLimitModeEnabled() then
        cur, need, label = p:GetLimitPoints(), 10000, string.format('Limit  (%d merits)', p:GetMeritPoints());
    else
        cur, need, label = p:GetExpCurrent(), p:GetExpNeeded(), 'Next';
    end

    local tw, th = layout.size('exp_track');
    local x, y = layout.anchor('bottom', tw + 40, 0, 14, -14, 'expbar');
    layout.bounds('expbar', x, y - 24, tw + 40, 30);

    draw.image('job_tile', x, y - 22);
    text.draw(abbr_obj, job_abbr(main), x + 15, y - 3, 'baseline');
    local jl = string.format('%s Level: %d', job_name(main), lvl);
    if sub ~= 0 and slvl > 0 then jl = jl .. string.format('   / %s %d', job_name(sub), slvl); end
    text.draw(job_obj, jl, x + 38, y - 6, 'baseline');

    draw.image('exp_track', x + 36, y - 2);
    if need > 0 and cur > 0 then
        draw.image('exp_fill', x + 36, y - 2, { sw = math.floor(tw * math.min(1, cur / need) + 0.5) });
    end
    local val = string.format('%d/%d', cur, need);
    text.draw(next_val, val, x + 36 + tw, y - 6, 'baseline');
    local vw = text.size(next_val);
    text.draw(next_lbl, label, x + 36 + tw - vw - 8 - text.size(next_lbl), y - 6, 'baseline');
end

return expbar;
