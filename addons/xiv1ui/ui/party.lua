--[[
* xiv1ui - party list (bottom right), after FFXIV 1.0 (reference §13):
* a "Light Party"/"Full Party" header, then per member the name (yours in yellow, the leader marked with a gold
* diamond, the current target marked with a gold shard), pink HP and yellow-green MP tubes side by side with italic
* values at their right ends. 1.0 showed no TP or buffs here. Members in another area are drawn faded.
* Click a member to target them.
--]]

local draw   = require('core.draw');
local text   = require('core.text');
local layout = require('core.layout');
local world  = require('core.world');

local party = { replaces = { 'party' } };

local ROW_H = 46;
local objs = {};
local header;
local rows = {};          -- screen rects for clicks: { x, y, w, h, slot }

function party.init()
    for i = 0, 5 do
        objs[i] = {
            name = text.new('name', { font_height = 20 }),
            hp   = text.new('numeral', { font_height = 18, font_alignment = text.align.Right, gradient_style = 0 }),
            mp   = text.new('numeral', { font_height = 18, font_alignment = text.align.Right, gradient_style = 0 }),
        };
    end
    header = text.new('label', { font_height = 17, font_color = 0xFF9EE6F0 });   -- light cyan, as in late 1.0
end

local function members()
    local p = AshitaCore:GetMemoryManager():GetParty();
    local list = {};
    for i = 0, 5 do
        if p:GetMemberIsActive(i) == 1 and p:GetMemberName(i) ~= '' then list[#list + 1] = i; end
    end
    return list, p;
end

function party.render()
    local list, p = members();
    local n = #list;
    if n == 0 then return; end

    local tw, th = layout.size('tube_track_party');
    local W = tw * 2 + 6;
    local H = n * ROW_H + 26;
    local x, y = layout.anchor('bottomright', W, H, -16, -118, 'party');
    layout.bounds('party', x, y - 10, W, H + 10);

    local title = (n >= 6 and 'Full Party') or (n >= 2 and 'Light Party') or 'Solo';
    draw.image('lock_mark', x + W - 120, y - 4, { scale = 0.7, color = 0xFF9EE6F0 });
    text.draw(header, title, x + W - 100, y + 14, 'baseline');

    local leader = p:GetAlliancePartyLeaderServerId1();
    local myzone = p:GetMemberZone(0);
    local tidx = world.target_index();
    rows = {};

    for r, i in ipairs(list) do
        local ry = y + 22 + (r - 1) * ROW_H;
        local o = objs[i];
        local here = (p:GetMemberZone(i) == myzone);
        local a = here and 1 or 0.45;
        local white = draw.alpha(0xFFFFFFFF, a);
        rows[#rows + 1] = { x, ry, W, ROW_H, i };

        -- name line: [leader diamond] Name [target shard]
        local nx = x + 14;
        if leader ~= 0 and p:GetMemberServerId(i) == leader then draw.image('leader_diamond', x, ry + 6, { color = white }); end
        local col = (i == 0) and world.COLOR.self or 0xFFF4F0E6;
        col = draw.alpha(col, a);
        if o.name.settings.font_color ~= col then o.name:set_font_color(col); end
        text.draw(o.name, p:GetMemberName(i), nx, ry + 18, 'baseline');
        if tidx ~= 0 and p:GetMemberTargetIndex(i) == tidx then
            local nw = text.size(o.name);
            draw.image('lock_mark', nx + nw + 4, ry + 2, { scale = 0.7 });
        end

        -- HP and MP tubes side by side, values at the right ends
        local gy = ry + 24;
        local hpp = (p:GetMemberHPPercent(i) or 0) / 100;
        local mpp = (p:GetMemberMPPercent(i) or 0) / 100;
        draw.image('tube_track_party', x, gy, { color = white });
        if hpp > 0 then draw.image('tube_fill_party_hp', x, gy, { sw = math.floor(tw * hpp + 0.5), color = white }); end
        draw.image('tube_track_party', x + tw + 6, gy, { color = white });
        if mpp > 0 then draw.image('tube_fill_party_mp', x + tw + 6, gy, { sw = math.floor(tw * mpp + 0.5), color = white }); end
        text.draw(o.hp, tostring(p:GetMemberHP(i)), x + tw - 6, gy + 2, 'baseline');
        text.draw(o.mp, tostring(p:GetMemberMP(i)), x + 2 * tw, gy + 2, 'baseline');
    end
end

function party.mouse(e)
    if e.message ~= 0x201 and e.message ~= 0x202 then return; end
    for _, r in ipairs(rows) do
        if e.x >= r[1] and e.x < r[1] + r[3] and e.y >= r[2] and e.y < r[2] + r[4] then
            e.blocked = true;
            if e.message == 0x202 then
                AshitaCore:GetChatManager():QueueCommand(1, string.format('/ta <p%d>', r[5]));
            end
            return;
        end
    end
end

return party;
