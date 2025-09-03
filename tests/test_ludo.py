import unittest
from ludo import LudoGame

class TestLudoGame(unittest.TestCase):
    def setUp(self):
        self.game = LudoGame()

    def test_add_player(self):
        player = self.game.add_player("Alice", (255,0,0))
        self.assertEqual(player.name, "Alice")

    def test_add_token(self):
        self.game.add_player("Alice", (255,0,0))
        token = self.game.add_token_to_player("Alice", (1,1))
        self.assertIsNotNone(token)
        self.assertEqual(token.position, (1,1))

if __name__ == "__main__":
    unittest.main()
