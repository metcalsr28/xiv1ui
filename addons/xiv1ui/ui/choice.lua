--[[
* xiv1ui - event choice menus ("What is your business?" + options), drawn in the 1.0 talk-window style in place of
* the game's own box. The game still owns the menu: the D-pad / arrow keys move its cursor and confirm / cancel
* choose, exactly as before. xiv1ui reads the question, the rows and the cursor from the menu each frame, hides the
* game's box and finger cursor, and draws its own. (How the menu was found: docs/MODDING-NOTES.md §7.)
*
* Layout (FFXI client of the HorizonXI era; every read is checked):
*   window "menu    query   " -> obj = [[slot] + 8]; visibility bytes obj+0x69 / +0x6A (the box), obj+0x78 (the
*   pointing-finger cursor; found by clearing each 1-valued flag byte in turn and watching the finger)
*   Q = [obj + 0x0C]   (Q+0x08 points back at obj)
*     Q+0x14  first row node   Q+0x24  row count   Q+0x30  cursor (u16, 0-based; Q+0x32 = scroll)   Q+0x36  question length   Q+0x38  question
*   row node (0x30 bytes): +0x00 next node, +0x10 -> text record + 8 (the text itself starts 4 bytes later)
*   text: u16 glyph codes, ASCII - 0x20 (space = 0), terminated by 0; 0xFEFE ... 0xFEFF bracket a highlighted name
*   (an item in "Which temporary item will you obtain?")
--]]

local mem    = require('core.mem');
local native = require('core.native');

local choice = {};

local MAX_ROWS = 40;

local slots = {};            -- menu name -> window slot (false if not found)
local hidden = {};           -- obj -> { slot, b69, b6a }: original visibility bytes we changed
local cache = nil;           -- { obj, q, count, question, rows }

local function slot_of(name)
    slots[name] = require('core.gamewin').slot(name) or false;
    return slots[name] or nil;
end

-- The text at `a`, and whether it held a code xiv1ui can't draw (then the game's own box shows the menu).
local function glyph_text(a, max)
    local t = {};
    local odd = false;
    for i = 0, (max or 160) - 1 do
        local c = mem.u16(a + i * 2);
        if c == 0xFEFE or c == 0xFEFF then
            -- (skipped) the start / end of a highlighted name, e.g. "An [antidote]." for an item
        elseif c == nil then break;
        elseif c >= 0x5F and i > 0 and mem.u16(a + i * 2 - 2) == 0 then
            break;                                         -- leftovers after the end of the text
        elseif c >= 0x5F then
            -- a glyph or code outside the letters xiv1ui knows, at the start or straight after a letter (leftovers
            -- come after a space): an item or key item name the game draws its own way (blank rows, "Equ."
            -- in Records of Eminence and Domain Invasion exchanges on retail)
            odd = true;
            break;
        elseif c == 0 then
            -- 0 is a space inside the text; two zeros in a row end it, and so does one after the end of a sentence:
            -- records are reused, so a short option written over a longer one leaves the old tail behind
            -- ("Yes." over "None of them." reads "Yes. of them." otherwise)
            local n = mem.u16(a + i * 2 + 2);
            if n == nil or n == 0 then break; end
            local last = t[#t];
            if last == '.' or last == '?' or last == '!' then break; end
            t[#t + 1] = ' ';
        else
            t[#t + 1] = string.char(c + 32);
        end
    end
    return (table.concat(t):gsub('^%s+', ''):gsub('%s+$', '')), odd;
end

--- The open choice menu as { question, rows = { ... }, cursor, count }, or nil.
function choice.read()
    local slot = slot_of('query');
    if slot == nil then return nil; end
    local obj = mem.chain(slot, 0, 8);
    if obj == nil then cache = nil; return nil; end
    local q = mem.u32(obj + 0x0C);
    if q == nil or mem.u32(q + 0x08) ~= obj then return nil; end
    local count = mem.u32(q + 0x24);
    if count == nil or count < 1 or count > MAX_ROWS then return nil; end
    if cache == nil or cache.obj ~= obj or cache.q ~= q or cache.count ~= count then
        local rows, node = {}, mem.u32(q + 0x14);
        for i = 1, count do
            if node == nil or node == 0 then break; end
            local rec = mem.u32(node + 0x10);
            local row, odd = '', false;
            if rec then row, odd = glyph_text(rec + 4); end
            if odd then cache = nil; return nil; end      -- (FFXI's own box shows this menu)
            rows[i] = row;
            node = mem.u32(node);
        end
        if #rows ~= count then return nil; end
        local qlen = mem.u16(q + 0x36);            -- the question's length in characters
        cache = { obj = obj, q = q, count = count, question = glyph_text(q + 0x38, qlen and math.min(qlen, 160)),
                  rows = rows };
    end
    cache.cursor = math.max(0, math.min(count - 1, mem.u16(q + 0x30) or 0)) + 1;   -- u16: Q+0x32 is the game's scroll offset
    return cache;
end

local function hide(slot, obj, finger)
    if obj == nil or hidden[obj] then return; end
    local a, b = mem.u8(obj + 0x69), mem.u8(obj + 0x6A);
    if (a ~= 0 and a ~= 1) or (b ~= 0 and b ~= 1) then return; end
    local f = finger and mem.u8(obj + 0x78) or nil;
    if f ~= nil and f ~= 0 and f ~= 1 then f = nil; end
    hidden[obj] = { slot, a, b, f };
    mem.w8(obj + 0x69, 0);
    mem.w8(obj + 0x6A, 0);
    if f then mem.w8(obj + 0x78, 0); end
end

local function show_all()
    for obj, h in pairs(hidden) do
        -- only an object its window slot still points at (a closed menu's object is freed and may be reused),
        -- and only bytes still holding our value
        if mem.chain(h[1], 0, 8) == obj then
            if mem.u8(obj + 0x69) == 0 then mem.w8(obj + 0x69, h[2]); end
            if mem.u8(obj + 0x6A) == 0 then mem.w8(obj + 0x6A, h[3]); end
            if h[4] and mem.u8(obj + 0x78) == 0 then mem.w8(obj + 0x78, h[4]); end
        end
    end
    hidden = {};
end

--- Called every frame: hides the game's box and finger while a choice menu is open; returns the menu or nil.
function choice.tick(enabled)
    local m = enabled and choice.read() or nil;
    if m then
        hide(slot_of('query'), m.obj, true);
    elseif next(hidden) then
        show_all();
    end
    return m;
end

function choice.release() show_all(); end

return choice;
