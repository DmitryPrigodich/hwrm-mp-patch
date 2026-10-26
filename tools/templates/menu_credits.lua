    -- Compact attribution; full upstream role/map credits ship with the release.
    {
        type = "TextLabel",
        name = "HWMP_Credits",
        Layout = {
            sector = 1,
            pos_XY = { x = 0.025, y = 0.95, xr = "scr", yr = "scr" },
            size_WH = { w = 0.80, h = 0.025, wr = "scr", hr = "scr" },
            pivot_XY = { 0, 1 },
        },
        wrapping = 0,
        Text = {
            text = __HWMP_CREDITS__,
            font = "ListBoxItemFont",
            pixels = 28,
            rel = 2160,
            color = { 180, 205, 220, 255 },
            hAlign = "Left",
            vAlign = "Middle",
        },
    },
