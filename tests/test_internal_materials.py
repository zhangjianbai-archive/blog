import unittest
from tools.internal_materials import SafeFragment


class InternalMaterials(unittest.TestCase):
    def test_preserves_text_and_table(self):
        fragment = SafeFragment()
        fragment.feed('<table><tr><td colspan="2">甲 &amp; 乙</td></tr></table>')
        self.assertIn('colspan="2"', ''.join(fragment.parts))
        self.assertIn('甲 &amp; 乙', ''.join(fragment.parts))

    def test_rejects_active_content(self):
        for tag in ('script', 'iframe', 'img', 'object', 'form'):
            with self.assertRaises(ValueError):
                SafeFragment().feed(f'<{tag}>')

    def test_drops_attributes(self):
        fragment = SafeFragment()
        fragment.feed('<p onclick="alert(1)" style="color:red">正文</p>')
        self.assertEqual(''.join(fragment.parts), '<p>正文</p>')
