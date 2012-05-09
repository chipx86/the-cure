from thecure.levels.base import *
from thecure.levels.level1 import Level1
from thecure.levels.level2 import Level2
from thecure.levels.level3 import Level3


def get_levels():
    return [Level1, Level2, Level3]
