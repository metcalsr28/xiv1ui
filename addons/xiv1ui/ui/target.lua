--[[
* xiv1ui - target unit frame (top centre), after FFXIV 1.0 (reference §9-§11):
* aggression orb with a level badge, the name in claim colour over a thin gold rule, a small "Target" label,
* the enmity capsule left of a long pink HP blade, and the HP percentage. Lock-on shows gold shards by the name.
--]]

local xi_now = require('core.now');
local draw   = require('core.draw');
local text   = require('core.text');
local layout = require('core.layout');
local world  = require('core.world');

local target = { replaces = { 'target' } };

local name_obj, label_obj, level_obj, pct_obj;
local shown_hp = 0;
local last_idx = 0;
local last_t = xi_now();

function target.init()
    name_obj  = text.new('name', { font_height = 26 });
    label_obj = text.new('label', { font_height = 15, font_color = 0xFFF0DCA0 });
    level_obj = text.new('numeral', { font_height = 18, font_color = 0xFFF8EBA0, gradient_style = 0 });
    pct_obj   = text.new('numeral', { font_height = 24, font_alignment = text.align.Right });
end

function target.render()
    local idx = world.target_index();
    local now = xi_now();
    local dt = math.min(0.1, now - last_t);
    last_t = now;
    local actor_name = (idx == 0) and world.target_actor() or nil;
    if idx == 0 and not actor_name then last_idx = 0; return; end

    local ent = AshitaCore:GetMemoryManager():GetEntity();
    local name = actor_name or require('core.npcnames').resolve(ent:GetName(idx), ent:GetServerId(idx));
    if name == nil or name == '' then return; end
    local hp = (ent:GetHPPercent(idx) or 0) / 100;
    if idx ~= last_idx then shown_hp = hp; last_idx = idx; end
    shown_hp = shown_hp + (hp - shown_hp) * math.min(1, dt * 8);

    local kind = actor_name and 'npc' or world.kind(idx);
    local tw, th = layout.size('tube_track_long');
    local W = tw + 60;
    local x, y = layout.anchor('top', W, 0, 0, 40, 'target');
    layout.bounds('target', x, y, W, 64);

    -- name line: [orb + level] Name ........ Target
    local nx = x + 44;
    if kind == 'mob' then
        local _, engaged = world.claim(idx);
        draw.image(engaged and 'aggro_active' or 'aggro_passive', x + 10, y + 2);
        text.draw(level_obj, '??', x + 26, y + 34, 'baseline');      -- FFXI doesn't reveal mob levels
    end
    local ncol = actor_name and 0xFFF4F0E6 or world.name_color(idx);
    if name_obj.settings.font_color ~= ncol then name_obj:set_font_color(ncol); end
    text.draw(name_obj, name, nx, y + 26, 'baseline');
    draw.image('name_rule', nx - 6, y + 28);
    text.draw(label_obj, 'Target', x + W - 52, y + 24, 'baseline');
    if world.locked() then
        local nw = text.size(name_obj);
        draw.image('lock_mark', nx + nw + 6, y + 4);
    end

    -- HP row: enmity capsule, then the blade (1.0 showed no HP bar for NPCs)
    if kind == 'npc' then return; end
    local hy = y + 44;
    local enm, flash = nil, false;
    if kind == 'mob' then enm, flash = world.enmity(idx); end
    if enm then
        local a = flash and (0.55 + 0.45 * math.abs(math.sin(now * 6))) or 1;
        draw.image('enmity_' .. enm, x + 4, hy + 1, { color = draw.alpha(0xFFFFFFFF, a) });
    end
    local bx = x + 46;
    draw.image('tube_track_long', bx, hy);
    local fw = math.floor(tw * math.max(0, math.min(1, shown_hp)) + 0.5);
    if fw > 0 then draw.image('tube_fill_enemy', bx, hy, { sw = fw }); end
    text.draw(pct_obj, string.format('%d%%', math.floor(hp * 100 + 0.5)), bx + tw + 54, hy + 14, 'baseline');
end

return target;
