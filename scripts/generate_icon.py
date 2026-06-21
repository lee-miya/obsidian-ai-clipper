import struct, zlib, math

def create_paperclip_icon():
    s = 256
    BG1 = (35, 10, 120)
    BG2 = (120, 55, 250)
    PAPER = (254, 253, 250)
    PE = (208, 205, 196)
    YL = (252, 196, 34)
    YLL = (255, 224, 110)
    YLE = (205, 148, 8)
    FD = (112, 62, 226)
    FL = (170, 120, 252)
    MLL = (225, 225, 230)
    MM = (170, 170, 180)
    MDD = (80, 80, 92)
    MS = (120, 120, 130)
    LC = (206, 203, 193)

    px = [[(0, 0, 0) for _ in range(s)] for _ in range(s)]

    # Diagonal gradient background
    for y in range(s):
        for x in range(s):
            t = (x * 0.55 + y * 0.45) / s
            px[y][x] = (
                int(BG1[0] * (1 - t) + BG2[0] * t),
                int(BG1[1] * (1 - t) + BG2[1] * t),
                int(BG1[2] * (1 - t) + BG2[2] * t),
            )

    ang = -0.03
    dl, dt = 32, 12
    dw, dh = 192, 232
    cx, cy = dl + dw / 2, dt + dh / 2

    def rot(lx, ly):
        dx, dy = lx - cx, ly - cy
        c2, sn = math.cos(ang), math.sin(ang)
        return (cx + dx * c2 - dy * sn, cy + dx * sn + dy * c2)

    # White paper with rounded corners
    cr = 20
    for dy in range(dh):
        for dx in range(dw):
            lx, ly = dl + dx, dt + dy
            skip = False
            if dx < cr and dy < cr and (dx - cr) ** 2 + (dy - cr) ** 2 > cr**2:
                skip = True
            elif dx >= dw - cr and dy < cr and (dx - (dw - cr - 1)) ** 2 + (dy - cr) ** 2 > cr**2:
                skip = True
            elif dx < cr and dy >= dh - cr and (dx - cr) ** 2 + (dy - (dh - cr - 1)) ** 2 > cr**2:
                skip = True
            elif (
                dx >= dw - cr
                and dy >= dh - cr
                and (dx - (dw - cr - 1)) ** 2 + (dy - (dh - cr - 1)) ** 2 > cr**2
            ):
                skip = True
            if skip:
                continue
            rx, ry = rot(lx, ly)
            ix, iy = int(rx), int(ry)
            if 0 <= ix < s and 0 <= iy < s:
                e = dx < 6 or dx >= dw - 6 or dy < 6 or dy >= dh - 6
                px[iy][ix] = PE if e else PAPER

    # Folded corner
    fs = 80
    for dy in range(fs):
        for dx in range(fs - dy - 3):
            lx, ly = dl + dw - fs + dx, dt + dy
            rx, ry = rot(lx, ly)
            ix, iy = int(rx), int(ry)
            if 0 <= ix < s and 0 <= iy < s:
                t2 = (dx + dy) / fs
                px[iy][ix] = (
                    int(FD[0] + t2 * (FL[0] - FD[0])),
                    int(FD[1] + t2 * (FL[1] - FD[1])),
                    int(FD[2] + t2 * (FL[2] - FD[2])),
                )

    # Fold edge line
    for t in range(fs):
        lx = dl + dw - fs + (fs - t)
        ly = dt + t
        for w_off in range(2):
            rx, ry = rot(lx + w_off, ly)
            ix, iy = int(rx), int(ry)
            if 0 <= ix < s and 0 <= iy < s:
                px[iy][ix] = PE

    # Paper lines
    for ln in range(12):
        ly2 = dt + 30 + ln * 18
        if ly2 < dt + dh - 25:
            for lx in range(dl + 20, dl + dw - 20):
                if (lx - dl) % 10 > 5:
                    rx, ry = rot(lx, ly2)
                    ix, iy = int(rx), int(ry)
                    if 0 <= ix < s and 0 <= iy < s:
                        px[iy][ix] = LC

    # Yellow sticky note
    nl, nt = 72, 32
    nw, nh = 116, 140
    for dy in range(nh):
        for dx in range(nw):
            lx, ly = nl + dx, nt + dy
            rx, ry = rot(lx, ly)
            ix, iy = int(rx), int(ry)
            if 0 <= ix < s and 0 <= iy < s:
                if dx < 5 or dx >= nw - 5 or dy < 5 or dy >= nh - 5:
                    px[iy][ix] = YLE
                elif dy < 16:
                    t3 = dy / 16
                    px[iy][ix] = (
                        int(YLL[0] * (1 - t3) + YL[0] * t3),
                        int(YLL[1] * (1 - t3) + YL[1] * t3),
                        int(YLL[2] * (1 - t3) + YL[2] * t3),
                    )
                else:
                    px[iy][ix] = YL

    # Sticky note shadow
    for dy in range(10):
        for dx in range(5):
            lx = nl + nw + dx
            ly = nt + 20 + dy
            rx, ry = rot(lx, ly)
            ix, iy = int(rx), int(ry)
            if 0 <= ix < s and 0 <= iy < s:
                alpha = (10 - dy) / 14.0
                o = px[iy][ix]
                px[iy][ix] = (
                    int(o[0] * (1 - alpha) + PE[0] * alpha),
                    int(o[1] * (1 - alpha) + PE[1] * alpha),
                    int(o[2] * (1 - alpha) + PE[2] * alpha),
                )

    # Sticky note lines
    for ln in range(9):
        ly3 = nt + 28 + ln * 14
        if ly3 < nt + nh - 12:
            for lx in range(nl + 14, nl + nw - 16):
                if (lx - nl) % 9 > 4:
                    rx, ry = rot(lx, ly3)
                    ix, iy = int(rx), int(ry)
                    if 0 <= ix < s and 0 <= iy < s:
                        px[iy][ix] = YLE

    # Large paperclip
    pcx, pcy = nl + nw // 2 - 1, nt + nh // 2 - 2
    for dy in range(-40, 41):
        for dx in range(-28, 29):
            tld = math.sqrt((dx + 1.5) ** 2 + (dy + 20) ** 2)
            bld = math.sqrt((dx + 1.5) ** 2 + (dy - 20) ** 2)
            is_straight = abs(dx + 1.5) < 6.5 and abs(dy) < 17
            is_top_outer = 11.5 < tld < 21.5 and dy < 4
            is_bot_outer = 11.5 < bld < 21.5 and dy > -4

            if is_top_outer or is_bot_outer or is_straight:
                lx, ly = pcx + dx, pcy + dy
                rx, ry = rot(lx, ly)
                ix, iy = int(rx), int(ry)
                if 0 <= ix < s and 0 <= iy < s:
                    if is_straight:
                        if abs(dx + 1.5) < 3:
                            px[iy][ix] = MDD
                        elif abs(dx + 1.5) < 5:
                            px[iy][ix] = MLL
                        else:
                            px[iy][ix] = MS
                    elif (is_top_outer and dy < -8) or (is_bot_outer and dy > 8):
                        px[iy][ix] = MLL
                    elif (is_top_outer and dy > -4 and dy < -1) or (is_bot_outer and dy > 1 and dy < 4):
                        px[iy][ix] = MS
                    else:
                        t4 = abs(dy) / 25
                        px[iy][ix] = (
                            int(MLL[0] * (1 - t4) + MM[0] * t4),
                            int(MLL[1] * (1 - t4) + MM[1] * t4),
                            int(MLL[2] * (1 - t4) + MM[2] * t4),
                        )

    # Highlights on paperclip
    for dy in range(-12, 13):
        for dx in range(-2, 3):
            tld2 = math.sqrt((dx + 1) ** 2 + (dy + 20) ** 2)
            bld2 = math.sqrt((dx + 1) ** 2 + (dy - 20) ** 2)
            if (12.5 < tld2 < 14.5 and dy < -6) or (12.5 < bld2 < 14.5 and dy > 6):
                lx, ly = pcx + dx, pcy + dy
                rx, ry = rot(lx, ly)
                ix, iy = int(rx), int(ry)
                if 0 <= ix < s and 0 <= iy < s:
                    px[iy][ix] = (255, 255, 255)

    # Rounded border
    br = 28
    for y in range(s):
        for x in range(s):
            outs = False
            if x < br and y < br and (x - br) ** 2 + (y - br) ** 2 > (br - 1) ** 2:
                outs = True
            elif x >= s - br and y < br and (x - (s - br)) ** 2 + (y - br) ** 2 > (br - 1) ** 2:
                outs = True
            elif x < br and y >= s - br and (x - br) ** 2 + (y - (s - br)) ** 2 > (br - 1) ** 2:
                outs = True
            elif (
                x >= s - br
                and y >= s - br
                and (x - (s - br)) ** 2 + (y - (s - br)) ** 2 > (br - 1) ** 2
            ):
                outs = True
            if outs:
                px[y][x] = BG1

    # Downscale to 128x128
    small = [[(0, 0, 0) for _ in range(128)] for _ in range(128)]
    for y in range(128):
        for x in range(128):
            sy, sx = y * 2, x * 2
            rsum, gsum, bsum = 0, 0, 0
            for dy2 in range(2):
                for dx2 in range(2):
                    rr, gg, bb = px[sy + dy2][sx + dx2]
                    rsum += rr
                    gsum += gg
                    bsum += bb
            small[y][x] = (rsum // 4, gsum // 4, bsum // 4)

    # Write PNG
    def wpng(fn, pixel):
        w, h = len(pixel[0]), len(pixel)
        raw = b""
        for y in range(h):
            raw += b"\x00"
            for x in range(w):
                r2, g2, b2 = pixel[y][x]
                raw += struct.pack(
                    "BBB", max(0, min(255, r2)), max(0, min(255, g2)), max(0, min(255, b2))
                )

        def chk(ct, d):
            c = ct + d
            return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

        png = b"\x89PNG\r\n\x1a\n"
        png += chk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        png += chk(b"IDAT", zlib.compress(raw))
        png += chk(b"IEND", b"")
        with open(fn, "wb") as f:
            f.write(png)

    wpng("chrome-extension/icons/icon-128.png", small)
    print("DONE: chrome-extension/icons/icon-128.png")


create_paperclip_icon()
