"""Nova Software runtime.

Copyright (c) 2026 Nova Software. All rights reserved.
"""

import random
import time

from cheats import Cheats
from configReader import ConfigReader
from keybinds import KeybindManager
from mouse import get_mouse_implementation
from screen import Screen

APP_NAME = "Nova Software"
COPYRIGHT_NOTICE = "Copyright (c) 2026 Nova Software. All rights reserved."
BRAND_SIGNATURE = "NS-2026"


class NovaSoftware:
    def run(self):
        self.print_license()
        while True:
            start_time = time.perf_counter()

            config = ConfigReader()
            config.read_config()

            keybinds = KeybindManager(config)
            cheats = Cheats(config)
            mouse = get_mouse_implementation(config)
            screen = Screen(config)

            while True:
                now = time.perf_counter()
                delta_time = now - start_time
                start_time = now

                reload_config = keybinds.check_key_binds(cheats)
                if reload_config:
                    break

                if self._should_process_frame(keybinds, cheats, config):
                    target, trigger = screen.get_target(cheats.recoil_offset)

                    if keybinds.get_trigger_state() and trigger:
                        delay_before_click = self._calculate_trigger_delay(config)
                        mouse.click(delay_before_click)

                    cheats.calculate_aim(cheats.get_aim_state(), target)

                cheats.apply_recoil(cheats.recoil_state, delta_time)

                if cheats.move_x != 0 or cheats.move_y != 0:
                    mouse.move(cheats.move_x, cheats.move_y)

                cheats.move_x, cheats.move_y = (0, 0)

                time_spent = (time.perf_counter() - start_time) * 1000
                if time_spent < config.min_loop_time:
                    time.sleep((config.min_loop_time - time_spent) / 1000)

            screen.close()
            mouse.close()

    def _should_process_frame(self, keybinds, cheats, config):
        if keybinds.get_trigger_state() or cheats.get_aim_state():
            return True
        if config.debug and config.debug_always_on:
            return True
        return False

    def _calculate_trigger_delay(self, config):
        if config.trigger_delay == 0:
            return 0
        return (random.randint(0, max(config.trigger_randomization - 1, 0)) + config.trigger_delay) / 1000

    def print_license(self):
        print(f"{APP_NAME}")
        print(COPYRIGHT_NOTICE)
        print(f"Signature: {BRAND_SIGNATURE}")
