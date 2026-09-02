Tank Battle (3D) - single file: tank_battle.py
================================================

Requirements:  pip install PyOpenGL PyOpenGL_accelerate
Run:           python tank_battle.py

ONLY uses gl/glut functions from the Lab 1 / 2 / 3 templates.
glutTimerFunc is NOT used (banned) -- all animation runs through
idle() using time.time() delta. glutKeyboardUpFunc is also avoided
(not in the templates), so movement is per key-press.

Controls:
   W / S        -> drive tank forward / backward (one step per press)
   A / D        -> turn tank left / right (turret turns with the body)
   Space / Left mouse click -> fire a shell (arcs through the air)
   V            -> switch camera (Orbit <-> Follow)
   Left / Right arrow -> rotate the orbit camera (it does NOT move by itself)
   P            -> pause / unpause (freezes game, doesn't close)
   R            -> restart after game over (or anytime)

14 features and where each lives in the code:
   1. Player tank (boxes + cylinder barrel)  -> draw_tank()
   2. Turret moves WITH the tank body         -> update(): turret_ang = tank_ang
   3. Enemy tanks chase nearest target (you   -> update_enemies() + enemy_fire()
      or your base) and fire at it from range
   4. Rounds/waves, harder each time         -> next_round_if_clear() + spawn_wave()
   5. Shells arc through the air (gravity)    -> update_shells() uses vz + GRAV
   6. Obstacles block view + movement         -> draw_obstacles() + blocked()
   7. Base has its own health (capsule bar)   -> base_hp, draw_hp_capsule()
   8. Tank flashes + shrinks when hit         -> draw_player_tank() (tank_hit_flash)
   9. Two camera views (orbit + follow)       -> setup_camera(), cam_mode
  10. Power-ups (rapid fire / speed boost)    -> update_powerups(), draw_powerups()
  11. Minimap in the corner                   -> draw_minimap()
  12. Score shown as animated coins           -> draw_score_coins() + draw_coin()
  13. Pause key                               -> keyboard_down() 'p'
  14. Game over screen + restart              -> draw_hud() + reset_game()

HP bars (this version):
   - Tank HP and Base HP are now shown as pretty rounded CAPSULE /
     oval bars (pill shape, NOT the boxy assignment-3 look), drawn as
     a 2D screen overlay at the top-left so they are ALWAYS clearly
     visible from any camera angle. (The earlier 3D floating bars were
     edge-on and hard to see -- that is fixed.)
   - Each capsule: dark outline -> light empty track -> colored fill
     sized by HP, with little segment gaps across the fill so it reads
     like the segmented pixel-art reference image (minus the hearts).
   - Fill colour: >=70% green, 40-70% yellow, below 40% red. Under 40%
     the bar also pulses (blinks) as a low-health warning.
   - Labels "TANK" and "BASE" sit to the left of each capsule.

Other visuals / animations:
   - Battlefield is a ROUND (circular) arena, and BIGGER now (radius
     800). It is far more colorful: green grass-tone ring tiles with a
     subtle animated shimmer, colorful accent rings, a bright teal
     center pad, and dark round scorch/crater patches. The surrounding
     wall is a circular ring whose segments cycle through rainbow-ish
     colors. Tank movement, enemy/power-up spawns and shell bounds all
     respect the circular edge; the base sits inside the ring.
   - A colorful SKY is drawn around the whole scene: a big circular
     backdrop with horizon-to-top gradient bands (orange -> pink ->
     purple -> deep blue), a soft glowing sun/moon disk, and distant
     hill silhouettes for depth. (All done with plain quads + colors,
     no textures/lighting -- only template functions.)
   - Everything is more colorful: the tank has a bright accent stripe
     and a glowing barrel tip; enemies are colored tanks; the base is
     a layered blue/purple fort with corner towers, a pulsing glow
     beacon and a rotating ring of orbs; obstacles are colored crates
     with bright caps and floating spinning gems.
   - Power-ups: spawn more often now and a couple appear at the start,
     so they're easy to find. Driving over a yellow one gives RAPID
     FIRE (shorter gap between shots) and a blue one gives SPEED BOOST
     (faster movement), each for 8 seconds, shown as pulsing icons at
     the top. (Verified working in the logic tests.)
   - Orbit camera stays still unless you press Left/Right arrows.
   - Turret stays aligned with the tank body.
   - Power-ups: floating + rotating pickups in the world, plus small
     pulsing icons at the top-center while active (yellow = rapid
     fire, blue = speed boost) with a seconds-left label.
   - Score: a spinning, bobbing coin with an "x N" count at top-left.
   - Shells arc; base antenna bobs; tank hit-flash + shrink.

Enemy shooting: enemies target whichever is nearer (you or the base)
and fire from range (not only when hugging the base). Shell arc and
collision windows are tuned so shots land reliably and actually
reduce HP.

NOTE: I could not visually render this in the sandbox (no display here).
I validated the game LOGIC with an automated harness that mocks OpenGL
and drives reset/keyboard/mouse/idle through every feature (movement,
firing, shell arc, wave progression, pause, camera toggle, power-up
pickup, base-destroyed game over, restart, obstacle blocking, turret
follow, static orbit camera, HP-capsule rendering at every HP level,
hp colours, enemy firing + damage, circular-arena spawns/bounds) --
all passed. I also rendered the
capsule shape to ASCII to confirm it is a rounded pill/oval, not a box.
Please run it on your machine to check the visuals/positions match what
you want, and tune numbers (speeds, sizes, positions) to taste.
