class Beatmap:
    def __init__(self, file_contents):
        self.file_contents = file_contents

        # sections
        self.osu_file_format_version = 0
        self.general_section = {}
        self.editor_section = []
        self.metadata_section = []
        self.difficulty_section = {}
        self.events_section = []
        self.timing_points_section = []
        self.colours_section = []
        self.hit_objects_section = []

        self.parse()

    def parse(self):
        current_section = ""

        for line in self.file_contents.splitlines():
            if "osu file format v" in line:
                self.osu_file_format_version = int(line.replace("osu file format v", "")
                                                   .replace("\ufeff", "").replace("\x7f", "").strip())
                continue
            elif "[General]" in line:
                current_section = "[General]"
                continue
            elif "[Editor]" in line:
                current_section = "[Editor]"
                continue
            elif "[Metadata]" in line:
                current_section = "[Metadata]"
                continue
            elif "[Difficulty]" in line:
                current_section = "[Difficulty]"
                continue
            elif "[Events]" in line:
                current_section = "[Events]"
                continue
            elif "[TimingPoints]" in line:
                current_section = "[TimingPoints]"
                continue
            elif "[Colours]" in line:
                current_section = "[Colours]"
                continue
            elif "[HitObjects]" in line:
                current_section = "[HitObjects]"
                continue

            if not line.strip():
                continue
            line = line.strip()

            if current_section == "[General]":
                try:
                    general_stuff = line.split(": ")
                    self.general_section[general_stuff[0]] = general_stuff[1]
                except IndexError:
                    general_stuff = line.split(":")
                    self.general_section[general_stuff[0]] = general_stuff[1]
            elif current_section == "[Editor]":
                self.editor_section.append(line)
            elif current_section == "[Metadata]":
                self.metadata_section.append(line)
            elif current_section == "[Difficulty]":
                diff_stuff = line.split(":")
                self.difficulty_section[diff_stuff[0]] = diff_stuff[1]
            elif current_section == "[Events]":
                self.events_section.append(line)
            elif current_section == "[TimingPoints]":
                self.timing_points_section.append(line.split(","))
            elif current_section == "[Colours]":
                self.colours_section.append(line)
            elif current_section == "[HitObjects]":
                self.hit_objects_section.append(line.split(","))

    def get_mode(self):
        return int(self.general_section["Mode"])

    def get_mode_str(self):
        mode_str = self.get_mode()

        if mode_str == 0:
            return "osu"
        elif mode_str == 1:
            return "taiko"
        elif mode_str == 2:
            return "ctb"
        elif mode_str == 3:
            return "mania"

        return
