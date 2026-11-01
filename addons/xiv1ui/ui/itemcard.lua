--[[
* xiv1ui - the item card: in place of FFXI's item info box ("menu    iteminfo") wherever the game shows it on its own
* (a treasure casket's "Obtain this item?", an NPC handing something over, ...). The item lists xiv1ui restyles
* (Items, Equipment) show the description in their own window and hide the box themselves; this covers the rest.
*
* The item comes from the box's class object (+0x24 item id, +0x26 bag index; gamewin.cursor_item()). The card sits
* above the dialogue box when one is up, else where that box would be.
--]]

local draw    = require('core.draw');
local text    = require('core.text');
local layout  = require('core.layout');
local ui      = require('core.ui');
local store   = require('core.store');
local mem     = require('core.mem');
local native  = require('core.native');
local gamewin = require('core.gamewin');

local card = {};

local hider = gamewin.new();
-- screens whose own panel shows the item (they hide the box themselves)
local OWNED = { inventor = true, iuse = true, itmsort2 = true, equip = true, mnstorag = true };

local W = 440;
local desc_obj = nil;

function card.release() hider:restore(); end

local owned_box = nil;        -- the item box a screen of OWNED was showing (it can outlive the screen for a moment)

function card.render()
    local o = gamewin.window('iteminfo');
    local _, fname = native.focused();
    local mine = hider:active();
    if OWNED[fname] then owned_box = o; elseif o == nil then owned_box = nil; end
    if store.data.cmd_menu == false or o == nil or OWNED[fname] or o == owned_box or require('ui.itempanel').selling(fname) or require('ui.itempanel').buying(fname)
            or not (mine or (mem.u8(o + 0x69) == 1 and mem.u8(o + 0x6A) == 1)) then
        if mine then hider:restore(); end
        return;
    end
    local id = gamewin.cursor_item();
    local r = id and AshitaCore:GetResourceManager():GetItemById(id);
    if r == nil then
        if mine then hider:restore(); end
        return;
    end
    hider:hide({ 'iteminfo' });

    local d = require('ui.itempanel').describe(r);
    desc_obj = desc_obj or text.new('small', { font_height = 17, font_color = 0xFFE8E4D8, box_width = W - 92 });
    if desc_obj.settings.text ~= d then text.set(desc_obj, d); end
    local _, dh = text.size(desc_obj);
    local h = math.max(76, 46 + dh + 14);

    local x, y;
    local dw = layout.widgets.dialogue;
    if require('ui.dialogue').shown and dw then
        x, y = dw[1] + (dw[3] - W) / 2, dw[2] - h - 10;
    else
        x, y = layout.anchor('bottom', W, h, 0, -300, 'itemcard');
    end
    layout.bounds('itemcard', x, y, W, h);

    local bw, bh = layout.size('win_hud');
    draw.nine('win_hud', x, y, W, h, 10, bw, bh);
    -- icon in a well
    local sw, sh = layout.size('slot_square');
    if sw > 0 then draw.image('slot_square', x + 14, y + 14, { scale = { 48 / sw, 48 / sh } }); end
    draw.entry(draw.item_icon(id), x + 18, y + 18, 40, 40);
    local name = ui.label('itemcard_name', 'name', { font_height = 22, font_color = 0xFFFFF4E0 });
    text.draw(name, (r.LogNameSingular and r.LogNameSingular[1] ~= '' and r.Name[1]) or r.Name[1] or '?', x + 76, y + 34, 'baseline');
    draw.image('name_rule', x + 76, y + 40, { scale = { (W - 92) / 300, 1 } });
    text.render(desc_obj, x + 76, y + 46);
end

return card;
