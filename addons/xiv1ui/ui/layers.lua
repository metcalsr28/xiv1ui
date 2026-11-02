--[[
* xiv1ui - action bar layers. Each page of the action bar has two layers of ten slots: green (LT / Ctrl) and red
* (RT / Alt). The bar starts on green.
*
*   Tap LT or RT (Ctrl or Alt) to switch the bar to that layer; it stays there.
*   While the trigger (or Ctrl / Alt) is HELD, the bar is armed: its slots brighten and
*     controller: D-pad Left/Right move a selection ring, A fires the selected slot, Up/Down flip the page;
*     keyboard:   1..0 fire slots of the held layer.
*   Released, the D-pad and A belong to the game again. Keyboard 1..0 (Configuration » "Number keys fire the action
*   bar") fire the current layer at any time.
*
* The game reads the keyboard through DirectInput and the controller through XInput (Ashita's key_state /
* xinput_state events): Ctrl, Alt and both triggers never reach the game (so its own macro palette never opens), and
* the D-pad / A / number keys are kept from it while the bar is armed. Configuration » "Action bar layers" turns
* this off and gives the keys back.
--]]

local ffi    = require('ffi');
local bit    = require('bit');
local store  = require('core.store');

local layers = {};

layers.GREEN, layers.RED = 1, 2;

local DIK = { LCTRL = 0x1D, RCTRL = 0x9D, LALT = 0x38, RALT = 0xB8 };
local NUM = { 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B };   -- DIK_1 .. DIK_0
local XB = { UP = 0x0001, DOWN = 0x0002, LEFT = 0x0004, RIGHT = 0x0008, A = 0x1000 };
local TRIGGER_ON, TRIGGER_OFF = 40, 20;    -- trigger travel (0-255) to arm / stay armed (hysteresis)

pcall(ffi.cdef, [[
typedef struct { uint16_t wButtons; uint8_t bLeftTrigger; uint8_t bRightTrigger;
                 int16_t sThumbLX; int16_t sThumbLY; int16_t sThumbRX; int16_t sThumbRY; } XIV1UI_XPAD;
typedef struct { uint32_t dwPacketNumber; XIV1UI_XPAD Gamepad; } XIV1UI_XSTATE;
]]);

local kb_armed, pad_armed = nil, nil;      -- layer held on the keyboard / controller, or nil
local prev = {};                           -- DIK code -> held at the last key_state call
local pad_prev = 0;

local function hotbar() return require('ui.hotbar'); end

local function hb_state()
    local hb = store.data.hotbar;
    if hb.layer ~= 1 and hb.layer ~= 2 then hb.layer = 1; end
    hb.sel = hb.sel or T{ 1, 1 };
    return hb;
end

--- The layer the bar shows (1 green, 2 red), whether it is armed, and whether a controller is driving it.
function layers.current()
    local hb = hb_state();
    return hb.layer, (kb_armed or pad_armed) ~= nil, pad_armed ~= nil and kb_armed == nil;
end

--- The selected slot (1..10) of a layer (controller selection ring).
function layers.selected(lay)
    return hb_state().sel[lay or hb_state().layer] or 1;
end

local function switch(lay)
    local hb = hb_state();
    if hb.layer ~= lay then hb.layer = lay; store.save(); end
end

local function active()
    return store.data.macro.palette and AshitaCore:GetChatManager():IsInputOpen() == 0;
end

local reply_pending = false;      -- Ctrl+R pressed: the reply is typed once Ctrl is let go (typed under a held Ctrl,
                                 -- the game drops part of it)

--- DirectInput keyboard state, before the game reads it.
function layers.key_state(e)
    if not active() then kb_armed = nil; return; end
    local p = ffi.cast('uint8_t*', e.data_raw);
    local function held(k) return p[k] >= 0x80; end
    local ctrl = held(DIK.LCTRL) or held(DIK.RCTRL);
    if reply_pending and not ctrl then
        reply_pending = false;
        if not require('ui.chatlog').reply() then print('[xiv1ui] No tells to reply to yet.'); end
    end
    local alt  = held(DIK.LALT) or held(DIK.RALT);
    kb_armed = (ctrl and layers.GREEN) or (alt and layers.RED) or nil;
    if kb_armed == nil then prev = {}; return; end
    switch(kb_armed);
    p[DIK.LCTRL], p[DIK.RCTRL], p[DIK.LALT], p[DIK.RALT] = 0, 0, 0, 0;
    for i, k in ipairs(NUM) do
        local d = held(k);
        if d and not prev[k] then hotbar().use_layer(kb_armed, i); end
        prev[k] = d;
        p[k] = 0;
    end
    -- Ctrl+R: reply to the last tell (with the layers off, xiv1ui.lua's key handler does it)
    local r = ctrl and held(0x13);
    if r and not prev[0x13] then reply_pending = true; end
    prev[0x13] = r;
    if ctrl then p[0x13] = 0; end
end

--- XInput controller state, before the game reads it (e.state = what the pad reported, e.state_modified = what the
-- game will get).
function layers.xinput_state(e)
    if e.state == nil or e.state_modified == nil then return; end
    if not active() then pad_armed, pad_prev = nil, 0; return; end
    local g = ffi.cast('XIV1UI_XSTATE*', e.state).Gamepad;
    local out = ffi.cast('XIV1UI_XSTATE*', e.state_modified).Gamepad;
    -- the game never sees the triggers, at any travel (a light press would open its own macro palette)
    out.bLeftTrigger, out.bRightTrigger = 0, 0;
    local lt = g.bLeftTrigger >= (pad_armed == layers.GREEN and TRIGGER_OFF or TRIGGER_ON);
    local rt = g.bRightTrigger >= (pad_armed == layers.RED and TRIGGER_OFF or TRIGGER_ON);
    local was = pad_armed;
    if lt and rt then pad_armed = pad_armed or layers.GREEN;      -- both: the one pressed first wins
    elseif lt then pad_armed = layers.GREEN;
    elseif rt then pad_armed = layers.RED;
    else pad_armed = nil; end
    if pad_armed == nil then pad_prev = 0; return; end
    if pad_armed ~= was then switch(pad_armed); pad_prev = g.wButtons; end   -- a button already held doesn't fire

    local buttons = g.wButtons;
    local pressed = bit.band(buttons, bit.bnot(pad_prev));
    pad_prev = buttons;
    local hb = hb_state();
    local s = hb.sel[pad_armed] or 1;
    if bit.band(pressed, XB.LEFT) ~= 0 then s = (s - 2) % 10 + 1; end
    if bit.band(pressed, XB.RIGHT) ~= 0 then s = s % 10 + 1; end
    hb.sel[pad_armed] = s;
    if bit.band(pressed, XB.UP) ~= 0 then hotbar().page_step(-1); end
    if bit.band(pressed, XB.DOWN) ~= 0 then hotbar().page_step(1); end
    if bit.band(pressed, XB.A) ~= 0 then hotbar().use_layer(pad_armed, s); end
    -- keep the D-pad and A from the game while armed
    out.wButtons = bit.band(out.wButtons, bit.bnot(bit.bor(XB.UP, XB.DOWN, XB.LEFT, XB.RIGHT, XB.A)));
end

function layers.render()
    require('core.macros').tick();
end

return layers;
