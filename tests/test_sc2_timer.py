import unittest
from src.sc2_timer import SC2Timer

class TestSC2Timer(unittest.TestCase):
    def setUp(self):
        self.timer = SC2Timer()

    def test_get_instructions(self):
        instruction = self.timer.get_instructions("00:00")
        self.assertEqual(instruction, "开始建造工人")

if __name__ == '__main__':
    unittest.main()