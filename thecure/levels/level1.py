from thecure.levels.base import Level


class Level1(Level):
    def draw_bg(self, surface):
        surface.fill((237, 243, 255))
