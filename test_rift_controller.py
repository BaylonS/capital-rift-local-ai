import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('controller', Path(__file__).resolve().parent / 'capital-rift-controller.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

class GuardTests(unittest.TestCase):
    def setUp(self):
        self.size = [1280, 720]
        self.targets = [{'id': 0, 'text': 'LOGISTICS', 'x': 1180, 'y': 288}]

    def check(self, **a):
        return c.validate(dict(reason='test', **a), self.size, self.targets)

    def test_exact_ocr_target(self):
        self.assertEqual(self.check(action='click_text', target_id=0)['target_text'], 'LOGISTICS')

    def test_bounds_and_browser_chrome(self):
        for x, y in [(0, 300), (1280, 300), (100, 100), (100, 719), (-1, 300), ('100', 300)]:
            with self.subTest(x=x, y=y), self.assertRaises(ValueError):
                self.check(action='click', x=x, y=y)

    def test_missing_target(self):
        with self.assertRaises(ValueError): self.check(action='click_text', target_id=5)

    def test_shell_and_os_shortcuts_blocked(self):
        for action in [dict(action='shell', command='id'), dict(action='key', key='ctrl+alt+t'),
                       dict(action='type', text='hello\n'), dict(action='scroll', x=300, y=300, amount=100)]:
            with self.subTest(action=action), self.assertRaises(ValueError): self.check(**action)

    def test_wiki_restricted(self):
        self.check(action='open_wiki', url='https://wiki.capitalrift.com/mechanics/mining/')
        for url in ['https://example.com/', 'http://wiki.capitalrift.com/',
                    'https://wiki.capitalrift.com.evil.test/', 'https://u:p@wiki.capitalrift.com/']:
            with self.subTest(url=url), self.assertRaises(ValueError): self.check(action='open_wiki', url=url)

    def test_destructive_target_blocked(self):
        with self.assertRaises(ValueError):
            c.validate({'action':'click_text','target_id':0,'reason':'test'}, self.size,
                       [{'id':0,'text':'Sell land','x':300,'y':300}])

    def test_focus_blocks_other_apps(self):
        with patch.object(c, 'run', side_effect=['active: 0x123', 'Terminal', 'xfce4-terminal']):
            with self.assertRaises(RuntimeError): c.window()

    def test_focus_allows_game(self):
        with patch.object(c, 'run', side_effect=['active: 0x123', 'Capital Rift - Google Chrome', 'google-chrome']):
            self.assertEqual(c.window()['id'], '0x123')

    def test_locked_frame_is_blocked(self):
        with self.assertRaises(RuntimeError):
            c.guard_frame({'title':'Capital Rift'}, [{'text':'Unlock Password'}])

    def test_game_frame_uses_visible_address(self):
        c.guard_frame({'title':'Capital Rift'}, [{'text':'play.capitalrift.com'}, {'text':'LOGISTICS'}])

    def test_other_content_is_blocked(self):
        with self.assertRaises(RuntimeError):
            c.guard_frame({'title':'Capital Rift'}, [{'text':'Server error'}])

    def test_camera_actions_are_bounded(self):
        self.check(action='zoom', amount=2)
        self.check(action='pan', direction='left', distance=120)
        for a in [dict(action='zoom', amount=10), dict(action='pan', direction='diagonal'),
                  dict(action='pan', direction='right', distance=800)]:
            with self.assertRaises(ValueError): self.check(**a)

    def test_grounded_object_coordinates(self):
        visual = c.visual_grounding({'targets':[{'label':'Crate','kind':'map_object','bbox':[400,400,500,500]}]}, self.size)
        a = c.validate({'action':'inspect','visual_id':0,'reason':'Read crate'}, self.size, [], visual)
        self.assertEqual((a['x'], a['y']), (576,324))
        with self.assertRaises(ValueError): self.check(action='inspect', visual_id=99)

    def test_bad_grounding_is_discarded(self):
        self.assertEqual(c.visual_grounding({'targets':[{'label':'X','kind':'map_object','bbox':[900,0,100,100]}]}, self.size), [])

    def test_exploration_cannot_edit(self):
        self.assertFalse(c.exploration_action({'action':'type','text':'1000'}, []))
        self.assertFalse(c.exploration_action({'action':'click_text','target_text':'Buy'}, []))
        with self.assertRaises(RuntimeError): c.guard_exploration([{'text':'Click corners on your land'}])

    def test_tiled_browser_bounds_block_other_apps(self):
        with self.assertRaises(ValueError):
            c.validate({'action':'click','x':950,'y':350,'reason':'test'}, self.size, [], [], [0,28,805,720])

    def test_crop_grounding_offset(self):
        t = c.visual_grounding({'targets':[{'label':'B','kind':'map_object','bbox':[400,400,500,500]}]}, [800,600], (100,28))
        self.assertEqual((t[0]['x'],t[0]['y']), (460,298))

    def test_ownership_tags_and_tickers_are_not_objects(self):
        self.assertEqual(c.visual_grounding({'targets':[{'label':'YOURS','kind':'map_object','bbox':[400,400,500,500]},
            {'label':'Company','kind':'map_object','bbox':[400,960,500,990]}]}, self.size), [])

    def test_information_label_ocr_variations(self):
        a={'target_text':'YOURS','x':300,'y':300}
        self.assertIsNotNone(c.resolve_text_target(a,[{'text':'Y0URS','x':301,'y':301}]))
        self.assertIsNone(c.resolve_text_target({'target_text':'Buy $100','x':300,'y':300},[{'text':'Buy $1000','x':301,'y':301}]))

    def test_land_card_reading_does_not_invent_inventory(self):
        data = c.classify_visual({'scene':'map','facts':['Land area 60,866 mÂ²','The player has not placed any items on it.']},
            [{'text':'Overview'},{'text':'Remote'},{'text':'60,866 mÂ²'}])
        self.assertEqual(data['scene'], 'item_panel')
        self.assertFalse(any('not placed' in f for f in data['facts']))

    def test_info_controls_allow_icons(self):
        self.assertTrue(c.exploration_action({'action':'click_text','target_text':'@ Editland'}, []))

if __name__ == '__main__': unittest.main()
