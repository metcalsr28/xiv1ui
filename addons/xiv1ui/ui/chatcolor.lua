--[[
* xiv1ui - key words in the chat logs, in colour (Configuration » Chat » "Colour key words"): what a /check says,
* critical hits, damage (gold dealt by your party, red taken by it), healing, misses, resisted spells, what a monster
* readies or casts, experience, level and skill gains, and items obtained.
*
* chatcolor.pieces(line, base colour) -> { { text, ARGB }, ... } when the line has something lit, else nil.
--]]

local chatcolor = {};

local C = {
    weak = 0xFF9C9C9C, easy = 0xFF7EC8FF, decent = 0xFF5AA0FF, even = 0xFFFFFFFF, tough = 0xFFFFE070,
    very = 0xFFFFA040, incredibly = 0xFFFF5A4A, gauge = 0xFFD08CFF,
    high = 0xFFFF8070, low = 0xFF8CE68C,
    crit = 0xFFFFC040, dealt = 0xFFFFE08A, taken = 0xFFFF7A6A, hp = 0xFF8CF08C, mp = 0xFF8CC8FF,
    miss = 0xFF8C887C, resist = 0xFFC8A0F0, defeat = 0xFFF0D080, foe_move = 0xFFFFB060, our_move = 0xFF9BE0E0,
    exp = 0xFF9BF0A0, level = 0xFFFFD86A, skill = 0xFF8CE6F0, item = 0xFFF0D080,
};
chatcolor.COLORS = C;

-- /check: the longest phrase first ("very tough" before "tough")
local CHECK = {
    { 'too weak to be worthwhile', C.weak }, { 'easy prey', C.easy }, { 'decent challenge', C.decent },
    { 'even match', C.even }, { 'incredibly tough', C.incredibly }, { 'very tough', C.very },
    { 'impossible to gauge', C.gauge }, { 'tough', C.tough },
};

-- the party's names (and their pets'), refreshed every few seconds
local party, party_t = {}, -100;
local function party_names()
    local now = os.clock();
    if now - party_t < 3 then return party; end
    party_t, party = now, {};
    local mm = AshitaCore:GetMemoryManager();
    local p, e = mm:GetParty(), mm:GetEntity();
    for i = 0, 17 do
        if p:GetMemberIsActive(i) == 1 then
            local n = p:GetMemberName(i);
            if n and n ~= '' then party[n] = true; end
            local idx = p:GetMemberTargetIndex(i);
            local pet = idx and idx > 0 and e:GetPetTargetIndex(idx) or 0;
            local pn = pet and pet > 0 and e:GetName(pet);
            if pn and pn ~= '' then party[pn] = true; end
        end
    end
    return party;
end

local function starts_with_party(s, names)
    for n in pairs(names) do
        if s:sub(1, #n) == n and not s:sub(#n + 1, #n + 1):match('%w') then return true; end
    end
    return false;
end

local function mentions_party(s, names)
    for n in pairs(names) do
        local a = s:find(n, 1, true);
        if a and not s:sub(a - 1, a - 1):match('%w') and not s:sub(a + #n, a + #n):match('%w') then return true; end
    end
    return false;
end

--- Spans to light in a line: { { from, to, colour }, ... } (byte positions), possibly overlapping.
local function spans(s)
    local out = {};
    local function add(a, b, col) if a and b and b >= a then out[#out + 1] = { a, b, col }; end end
    local function each(pat, col)
        local init = 1;
        while true do
            local a, b = s:find(pat, init);
            if not a then break; end
            add(a, b, type(col) == 'function' and col(a, b) or col);
            init = math.max(b + 1, init + 1);
        end
    end
    -- light the part `inner` of each match of before .. inner .. after (Lua patterns)
    local function capture(before, inner, after, col)
        local init = 1;
        while true do
            local x, y = s:match(before .. '()' .. inner .. '()' .. after, init);
            if not x then break; end
            add(x, y - 1, type(col) == 'function' and col(x, y - 1) or col);
            init = math.max(y, init + 1);         -- (always forward, even on an empty match)
        end
    end

    -- /check
    if s:find('seems', 1, true) or s:find('Impossible to gauge', 1, true) then
        for _, c in ipairs(CHECK) do
            local a, b = s:lower():find(c[1], 1, true);
            if a then add(a, b, c[2]); break; end
        end
        local a, b = s:find('high [%a ]-[%.!]');
        if a then add(a, a + 3, C.high); end
        a = s:find('low [%a ]-[%.!]');
        if a then add(a, a + 2, C.low); end
    end

    each('critical hit', C.crit);

    -- damage: whose? "X hits the Y for N points of damage" (actor first), "Y takes N points of damage" (target first)
    local names = party_names();
    local ours = starts_with_party(s, names);
    capture('for ', '%d+', ' points? of damage', function () return ours and C.dealt or (mentions_party(s, names) and C.taken or C.dealt); end);
    -- (the target is the subject: after the sentence before it, if any)
    local init = 1;
    while true do
        local a, x, y = s:match('()[%a\' ]-takes ()%d+() points? of damage', init);
        if not a then break; end
        local subj = s:sub(a):gsub('^[%.!%s]+', ''):gsub('^The ', '');
        add(x, y - 1, starts_with_party(subj, names) and C.taken or C.dealt);
        init = math.max(y, init + 1);
    end

    capture('recovers ', '%d+', ' HP', C.hp);
    capture('recovers ', '%d+', ' MP', C.mp);
    capture('gains ', '%d+', ' HP', C.hp);
    each('misses', C.miss);
    each('resists the spell', C.resist);
    each('resists the effects', C.resist);
    each('defeats', C.defeat);
    each('falls to the ground', C.defeat);

    -- what someone readies / casts / uses: a foe's in orange, the party's in teal
    local mover = ours and C.our_move or C.foe_move;
    capture('readies ', '.-', '%.', mover);
    if s:find('starts casting .- on ') then capture('starts casting ', '.-', ' on ', mover);
    else capture('starts casting ', '.-', '%.', mover); end
    capture('casts ', '.-', '%.', mover);
    capture(' uses ', '.-', '%.', mover);

    capture('gains ', '%d+', ' experience points', C.exp);
    capture('gains ', '%d+', ' limit points', C.exp);
    capture('gains ', '%d+', ' capacity points', C.exp);
    each('attains level %d+', C.level);
    capture('skill rises ', '%d+%.?%d*', ' points?', C.skill);
    capture('skill reaches level ', '%d+', '', C.skill);
    capture('Obtained: ', '.-', '%.', C.item);
    capture('obtains ', '.-', '%.', C.item);
    capture('You find an? ', '.-', ' on ', C.item);
    return out;
end

function chatcolor.pieces(s, base)
    local sp = spans(s);
    if #sp == 0 then return nil; end
    -- one colour per byte, earlier spans win
    local col = {};
    for _, x in ipairs(sp) do
        for i = x[1], x[2] do if col[i] == nil then col[i] = x[3]; end end
    end
    local out, cur, start = {}, nil, 1;
    for i = 1, #s + 1 do
        local c = (i <= #s) and (col[i] or base) or nil;
        if c ~= cur then
            if cur ~= nil then out[#out + 1] = { s:sub(start, i - 1), cur }; end
            cur, start = c, i;
        end
    end
    return out;
end

return chatcolor;
