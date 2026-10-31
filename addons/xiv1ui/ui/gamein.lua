--[[
* xiv1ui - what the game gets from the keyboard and controller, and the game screens xiv1ui takes over.
*
*   - While an xiv1ui window is open, the game doesn't see the navigation keys (arrows, Enter, Esc, Tab, the numpad
*     arrows) or the controller's D-pad, face and shoulder buttons. Those drive the xiv1ui window only, so a menu of
*     the game's that is still open underneath doesn't move along with it. (The game reads the keyboard through
*     DirectInput and the pad through XInput, so blocking the window messages alone isn't enough.)
*   - gamein.press(dik) presses a key for the game (down for a few reads, then up), the way the dev bridge does.
*   - Commands » Macros » Edit Macros opens xiv1ui's Macros window instead of FFXI's macro books: when the game's
*     book list ("mcrselec") opens from the Macro menu, xiv1ui presses Esc for the game (back to the Macro menu) and
*     opens its own window. The Macros window has an entry that opens FFXI's books (gamein.ffxi_macros()).
*     Communication » Emote List opens xiv1ui's Emotes window the same way.
--]]

local ffi   = require('ffi');
local bit   = require('bit');
local ui    = require('core.ui');
local store = require('core.store');

local gamein = {};

local NAV_DIK = { 0xC8, 0xD0, 0xCB, 0xCD, 0x1C, 0x9C, 0x01, 0x0F, 0x48, 0x50, 0x4B, 0x4D, 0x4A, 0x4E };
-- D-pad, LB, RB, A, B, X, Y (Start and Back stay with the game)
local NAV_PAD = bit.bor(0x0001, 0x0002, 0x0004, 0x0008, 0x0100, 0x0200, 0x1000, 0x2000, 0x4000, 0x8000);

pcall(ffi.cdef, [[
typedef struct { uint16_t wButtons; uint8_t bLeftTrigger; uint8_t bRightTrigger;
                 int16_t sThumbLX; int16_t sThumbLY; int16_t sThumbRX; int16_t sThumbRY; } XIV1UI_XPAD;
typedef struct { uint32_t dwPacketNumber; XIV1UI_XPAD Gamepad; } XIV1UI_XSTATE;
]]);

local queue = {};            -- scripted presses: { dik, reads so far }
function gamein.press(dik) queue[#queue + 1] = { dik, 0 }; end

-- a window opened this frame by a pad / key press: the release of that press must not reach the game either
local guard_until = 0;
local now = require('core.now');
local function guarding() return ui.any_open() or now() < guard_until; end

function gamein.key_state(e)
    local p = ffi.cast('uint8_t*', e.data_raw);
    if guarding() then
        for _, k in ipairs(NAV_DIK) do p[k] = 0; end
    end
    local q = queue[1];
    if q then
        q[2] = q[2] + 1;
        if q[2] <= 3 then p[q[1]] = 0x80;
        else p[q[1]] = 0; if q[2] >= 6 then table.remove(queue, 1); end end
    end
end

-- Controller buttons for xiv1ui, from the XInput state the game reads (the same source the action bar's triggers
-- use): each press / release goes to the dialogue box and to core/pad.lua; a button core/pad.lua takes stays away
-- from the game until it is released.
local prev_buttons, held_block = 0, 0
function gamein.xinput_state(e)
    if e.state == nil or e.state_modified == nil then return; end
    local now_b = ffi.cast('XIV1UI_XSTATE*', e.state).Gamepad.wButtons;
    local out = ffi.cast('XIV1UI_XSTATE*', e.state_modified).Gamepad;
    local changed = bit.bxor(now_b, prev_buttons);
    if changed ~= 0 then
        for b = 0, 15 do
            local m = bit.lshift(1, b);
            if bit.band(changed, m) ~= 0 then
                local down = bit.band(now_b, m) ~= 0;
                local ev = { button = b, state = down and 1 or 0 };
                pcall(require('ui.dialogue').pad, ev);
                local ok, block = pcall(require('core.pad').button, ev);
                if down and ok and block then held_block = bit.bor(held_block, m); end
                if not down then held_block = bit.band(held_block, bit.bnot(m)); end
            end
        end
        prev_buttons = now_b;
    end
    if held_block ~= 0 then out.wButtons = bit.band(out.wButtons, bit.bnot(held_block)); end
    if store.data.pad ~= false and guarding() then
        out.wButtons = bit.band(out.wButtons, bit.bnot(NAV_PAD));
    end
end

-- Game screens opened from a menu that xiv1ui replaces with its own window
local SWAPS = {
    mcrselec = { from = 'mcrmenu', window = 'ui.win_macros' },    -- Commands » Macros » Edit Macros
    emote    = { from = 'commenu', window = 'ui.win_emotes' },    -- Commands » Communication » Emote List
};
local prev_name = nil;
local bypass = false;        -- the player asked for FFXI's own macro books
function gamein.ffxi_macros()
    bypass = true;
    ui.close_all();
    guard_until = now() + 0.3;
    gamein.press(0x1C);      -- Enter on the Macro menu's "Edit Macros" (still selected underneath)
end

-- Opening one of FFXI's own menus for a button (keeping the game's behaviour): numpad minus opens the Commands menu,
-- then once it has focus the cursor is moved to the wanted entry (by its label, as xiv1ui reads the menu) and
-- confirmed. Gives up after a moment if the menu doesn't come up.
local want = nil;            -- { label, since, pressed }
function gamein.open_command(label)
    ui.close_all();
    want = { label = label, since = now(), pressed = false };
    gamein.press(0x4A);
end

local function follow_command()
    if want == nil then return; end
    if now() - want.since > 2 then want = nil; return; end
    if want.pressed then return; end
    local ok, m = pcall(function () return require('ui.cmdmenu').read(); end);
    if not ok or m == nil or (m.name ~= 'menuwind' and m.name ~= 'socialme') or m.rows == nil then return; end
    local to = nil;
    for i, l in ipairs(m.rows) do if l == want.label then to = i; end end
    if to == nil or m.cursor == nil then want = nil; return; end
    local d = to - m.cursor;
    for _ = 1, math.abs(d) do gamein.press(d > 0 and 0xD0 or 0xC8); end
    gamein.press(0x1C);
    want.pressed = true;
    want.since = now() - 1.5;      -- (then forget it shortly)
end

local was_open = false;
function gamein.render()
    follow_command();
    -- a window just closed (B / Esc): that press, still held, mustn't reach the game's menu underneath
    local open = ui.any_open();
    if was_open and not open then guard_until = math.max(guard_until, now() + 0.3); end
    was_open = open;
    local _, name = require('core.native').focused();
    if name ~= prev_name then
        local swap = SWAPS[name];
        if swap and prev_name == swap.from and not bypass and store.data.cmd_menu ~= false then
            gamein.press(0x01);                                  -- back to the menu it was opened from
            require(swap.window).open();
            guard_until = now() + 0.3;
        elseif name == 'mcrmenu' or name == nil then
            bypass = false;
        end
        prev_name = name;
    end
end

return gamein;
